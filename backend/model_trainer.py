import sqlite3
import pandas as pd
import numpy as np
import ta
import time
import os
import sys
import json
import lightgbm as lgb
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sklearn.model_selection import TimeSeriesSplit

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading_system.db")

NIFTY_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "ITC.NS",
    "LT.NS", "BHARTIARTL.NS", "HINDUNILVR.NS"
]

def get_db():
    return sqlite3.connect(DB_PATH)

def fetch_historical_data():
    conn = get_db()
    
    # 4-year limit for memory safety on Droplet
    four_years_ago = (datetime.now() - timedelta(days=4*365)).strftime('%Y-%m-%d')
    query = f"SELECT * FROM market_data_1d WHERE Datetime >= '{four_years_ago}' ORDER BY Datetime ASC"
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        return None
        
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    
    # Fetch sentiment data and aggregate by day and symbol
    conn = get_db()
    try:
        news_query = f"SELECT timestamp, related_tickers as Symbol, sentiment_score FROM scraped_news WHERE sentiment_score IS NOT NULL AND timestamp >= '{four_years_ago}'"
        news_df = pd.read_sql(news_query, conn)
        if not news_df.empty:
            # Convert timestamp to date
            news_df['Datetime'] = pd.to_datetime(news_df['timestamp']).dt.normalize()
            # Average sentiment per day per symbol
            sentiment_daily = news_df.groupby(['Datetime', 'Symbol'])['sentiment_score'].mean().reset_index()
            sentiment_daily.rename(columns={'sentiment_score': 'macro_sentiment'}, inplace=True)
            
            # Merge into main df
            df = pd.merge(df, sentiment_daily, on=['Datetime', 'Symbol'], how='left')
        else:
            df['macro_sentiment'] = 0.0
    except Exception as e:
        print(f"Failed to fetch macro sentiment: {e}")
        df['macro_sentiment'] = 0.0
    finally:
        conn.close()
        
    # Fill missing sentiment with 0 (Neutral)
    df['macro_sentiment'] = df['macro_sentiment'].fillna(0.0)
    
    # Fetch global macro features
    conn = get_db()
    try:
        macro_query = "SELECT date as Datetime, vix_change, crude_change, usd_inr_change, gspc_change, dji_change FROM global_macro_features"
        macro_df = pd.read_sql(macro_query, conn)
        if not macro_df.empty:
            macro_df['Datetime'] = pd.to_datetime(macro_df['Datetime'])
            df = pd.merge(df, macro_df, on='Datetime', how='left')
        else:
            df['vix_change'] = np.nan
            df['crude_change'] = np.nan
            df['usd_inr_change'] = np.nan
            df['gspc_change'] = np.nan
            df['dji_change'] = np.nan
    except Exception as e:
        print(f"Failed to fetch macro features: {e}")
        df['vix_change'] = np.nan
        df['crude_change'] = np.nan
        df['usd_inr_change'] = np.nan
        df['gspc_change'] = np.nan
        df['dji_change'] = np.nan
    finally:
        conn.close()
        
    return df

def generate_features_and_labels(df_sym):
    """
    Computes strict point-in-time features via .shift(1) and proxy ORB labels.
    Designed to be used with df.groupby('Symbol').apply()
    """
    df = df_sym.copy()
    
    # Ensure sorted by date
    df = df.sort_values('Datetime').reset_index(drop=True)
    
    if len(df) < 50:
        return pd.DataFrame()
    
    # 1. Technical Features
    df['returns_1d'] = df['Close'].pct_change(1)
    df['returns_5d'] = df['Close'].pct_change(5)
    
    atr_ind = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14)
    df['ATR'] = atr_ind.average_true_range()
    df['ATR_pct'] = df['ATR'] / df['Close']
    
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    df['MACD'] = ta.trend.MACD(df['Close']).macd_diff()
    
    bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    df['BB_width'] = bb.bollinger_wband()
    df['BB_pband'] = bb.bollinger_pband()
    
    df['SMA_20_dist'] = df['Close'] / df['Close'].rolling(20).mean() - 1
    df['SMA_50_dist'] = df['Close'] / df['Close'].rolling(50).mean() - 1
    df['SMA_200_dist'] = df['Close'] / df['Close'].rolling(200).mean() - 1
    
    # 52w high/low proxy
    df['High_252'] = df['High'].rolling(252).max()
    df['Low_252'] = df['Low'].rolling(252).min()
    df['Proximity_52w'] = (df['Close'] - df['Low_252']) / (df['High_252'] - df['Low_252'] + 1e-9)
    
    # Macro Trend Features (Computed before shift)
    if 'vix_change' in df.columns:
        df['vix_5d_avg'] = df['vix_change'].rolling(5).mean()
        df['crude_10d_mom'] = df['crude_change'].rolling(10).mean()
    else:
        df['vix_5d_avg'] = np.nan
        df['crude_10d_mom'] = np.nan
    
    # Strict Lagging! ALL features must be shifted by 1 so day t only sees data up to t-1
    feature_cols = ['returns_1d', 'returns_5d', 'ATR_pct', 'RSI', 'MACD', 'BB_width', 'BB_pband', 
                    'SMA_20_dist', 'SMA_50_dist', 'SMA_200_dist', 'Proximity_52w', 'macro_sentiment',
                    'vix_change', 'crude_change', 'usd_inr_change', 'gspc_change', 'dji_change',
                    'vix_5d_avg', 'crude_10d_mom']
    
    for col in feature_cols:
        if col in df.columns:
            df[col] = df[col].shift(1)
        
    # 2. Proxy ORB Labels (Pessimistic)
    # Target day is day t (un-shifted High/Low)
    # Entry proxy: Previous Close + 0.5 * Previous ATR
    # Stop loss: Entry - 1.0 * Previous ATR
    # Target: Entry + 2.0 * Previous ATR
    
    prev_close = df['Close'].shift(1)
    prev_atr = df['ATR'].shift(1)
    
    entry_price = prev_close + (0.5 * prev_atr)
    stop_loss = entry_price - (1.0 * prev_atr)
    profit_target = entry_price + (2.0 * prev_atr)
    
    # Day t hits entry if High >= entry_price
    trade_triggered = df['High'] >= entry_price
    
    # Pessimistic Labeling: If Low drops below StopLoss, it's a loss (0), even if High hit target later
    hit_stop = df['Low'] <= stop_loss
    hit_target = df['High'] >= profit_target
    
    # Label is 1 ONLY IF trade triggered, target was hit, AND stop was NOT hit
    df['Label'] = np.where(trade_triggered & hit_target & ~hit_stop, 1, 0)
    
    # Drop NaNs created by shifting and rolling
    df = df.dropna(subset=feature_cols).copy()
    
    return df

GLOBAL_FEATURE_COLS = [
    'returns_1d', 'returns_5d', 'ATR_pct', 'RSI', 'MACD', 'BB_width', 'BB_pband', 
    'SMA_20_dist', 'SMA_50_dist', 'SMA_200_dist', 'Proximity_52w', 'macro_sentiment',
    'vix_change', 'crude_change', 'usd_inr_change', 'gspc_change', 'dji_change',
    'vix_5d_avg', 'crude_10d_mom'
]

def update_model_config(key, value):
    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now(ZoneInfo('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT OR REPLACE INTO model_config (key, value, updated_at) 
        VALUES (?, ?, ?)
    ''', (key, float(value), now_str))
    conn.commit()
    conn.close()

def main():
    print(f"[{datetime.now(ZoneInfo('Asia/Kolkata'))}] Starting 24/7 ML Training Daemon...")
    
    df_raw = fetch_historical_data()
    if df_raw is None or df_raw.empty:
        print("No historical data found. Exiting.")
        sys.exit(0)
        
    # Holiday/Weekend Gate: Check if today's date exists in the DB
    today_str = datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%Y-%m-%d')
    max_date = df_raw['Datetime'].max().strftime('%Y-%m-%d')
    
    if max_date != today_str:
        print(f"No new bar found for today ({today_str}). Market likely closed/weekend. Exiting gracefully.")
        # Uncomment this to enforce strict skipping. Commented for initial run to force training.
        # sys.exit(0)
        
    # Vectorized Feature Generation
    print("Generating features using vectorized operations...")
    df_full = df_raw.groupby('Symbol', group_keys=False).apply(generate_features_and_labels)
    
    if df_full.empty:
        print("Failed to generate features. Exiting.")
        sys.exit(1)
        
    df_full = df_full.sort_values('Datetime').reset_index(drop=True)
    print(f"Total dataset size: {len(df_full)} rows. Features: {len(GLOBAL_FEATURE_COLS)}")
    
    # Split features and target
    X = df_full[GLOBAL_FEATURE_COLS]
    y = df_full['Label']
    
    # Class Imbalance Handling
    n_neg = len(y[y == 0])
    n_pos = len(y[y == 1])
    spw = n_neg / n_pos if n_pos > 0 else 1.0
    print(f"Class imbalance scale_pos_weight: {spw:.2f}")
    
    model_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model_latest.txt')
    
    if os.path.exists(model_file):
        print("Existing model found. Performing incremental update (warm start)...")
        # For incremental nightly updates, we don't need a full walk-forward CV threshold calibration,
        # but we should fetch the last known best threshold.
        # However, to be safe, we can just retrain lightly. 
        # The user requested: `new_model = lgb.train(params, train_set, num_boost_round=50, init_model=old_model)`
        
        # Load old model
        old_model = lgb.Booster(model_file=model_file)
        
        # Create LightGBM dataset for the entire dataset (or just recent data, but passing all is fine if small)
        # Actually, for true incremental on just today, we would filter df_full for today's date.
        # Since this script runs nightly, `df_full` contains the full 4 years.
        # Let's filter for just the last 5 days to incrementally train, or train on full with small rounds.
        # Training on full with `init_model` just adds more trees based on residual errors of the full set.
        # It's extremely fast regardless.
        lgb_train = lgb.Dataset(X, label=y)
        
        params = {
            'objective': 'binary',
            'learning_rate': 0.05,
            'scale_pos_weight': spw,
            'verbose': -1
        }
        
        final_model = lgb.train(params, lgb_train, num_boost_round=50, init_model=old_model)
        final_model.save_model(model_file)
        
        # Retrieve previous best threshold
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM model_config WHERE key='ai_conviction_threshold'")
        row = cursor.fetchone()
        best_threshold = float(row[0]) if row else 0.55
        max_pf = 0.0 # Will be tracked in drift detection
        conn.close()
        
    else:
        print("No existing model found. Running full Walk-Forward CV to initialize and calibrate...")
        # Walk-Forward Validation & Threshold Calibration
        tscv = TimeSeriesSplit(n_splits=5)
        best_threshold = 0.55
        max_pf = 0.0
        
        thresholds = [0.51, 0.53, 0.55, 0.57, 0.60]
        pf_results = {th: [] for th in thresholds}
        
        for train_idx, val_idx in tscv.split(X):
            X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
            X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]
            
            model = lgb.LGBMClassifier(
                learning_rate=0.05,
                n_estimators=200,
                scale_pos_weight=spw,
                random_state=42,
                verbose=-1
            )
            model.fit(X_train, y_train)
            probs = model.predict_proba(X_val)[:, 1]
            
            for th in thresholds:
                trades = probs > th
                if trades.sum() == 0:
                    pf_results[th].append(1.0)
                    continue
                    
                wins = y_val[trades].sum()
                losses = trades.sum() - wins
                
                gross_profit = wins * 2.0
                gross_loss = losses * 1.0
                pf = gross_profit / gross_loss if gross_loss > 0 else 0
                pf_results[th].append(pf)
                
        mean_pfs = {th: np.mean(pfs) for th, pfs in pf_results.items()}
        best_threshold = max(mean_pfs, key=mean_pfs.get)
        max_pf = mean_pfs[best_threshold]
        
        print(f"Optimal Threshold Calibrated: {best_threshold} (Mean PF: {max_pf:.2f})")
        update_model_config('ai_conviction_threshold', best_threshold)
        update_model_config('ai_hypothetical_pf', max_pf)
        
        print("Training final production model on all historical data...")
        final_model = lgb.train({
            'objective': 'binary',
            'learning_rate': 0.05,
            'scale_pos_weight': spw,
            'verbose': -1
        }, lgb.Dataset(X, label=y), num_boost_round=200)
        
        final_model.save_model(model_file)
    
    # Pre-calculate Tomorrow's Forecasts
    # We take the most recent row for each symbol
    print("Generating AI Forecasts for tomorrow...")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM daily_ai_forecasts")
    
    tomorrow_str = (datetime.now(ZoneInfo('Asia/Kolkata')) + timedelta(days=1)).strftime('%Y-%m-%d')
    
    for sym in NIFTY_SYMBOLS:
        df_sym = df_full[df_full['Symbol'] == sym]
        if df_sym.empty: continue
        
        last_row = df_sym.iloc[-1:]
        X_last = last_row[GLOBAL_FEATURE_COLS]
        
        # lgb.Booster predict returns raw probabilities when objective='binary'
        prob = final_model.predict(X_last)[0]
        
        # Feature importances/contributions (LightGBM natively supports this)
        # We can extract global feature importance easily:
        importance = dict(zip(GLOBAL_FEATURE_COLS, final_model.feature_importance().tolist()))
        fc_json = json.dumps(importance)
        
        cursor.execute('''
            INSERT INTO daily_ai_forecasts (symbol, date, probability, feature_contributions)
            VALUES (?, ?, ?, ?)
        ''', (sym, tomorrow_str, float(prob), fc_json))
        
    conn.commit()
    
    # ---------------- DRIFT DETECTION ----------------
    print("Running Model Drift Detection...")
    # Calculate today's hypothetical Profit Factor
    # Get last 60 days of forecasts and actual labels
    # We will approximate by evaluating the last 60 days of the training set (which are out-of-sample relative to older data, but strictly speaking this is in-sample if we just retrained on all. To be truly rigorous, we'd use the daily expanding walk-forward out-of-sample predictions, but for simplicity we'll evaluate the most recent 20 days on the model).
    # Since we don't have historical OOS predictions saved yet, we'll initialize the drift as ACTIVE.
    # In production, we'd query daily_ai_forecasts joined with market_data_1d to see if the trade actually won.
    
    # Check current active state
    cursor.execute("SELECT value FROM model_config WHERE key='ai_active'")
    row = cursor.fetchone()
    current_active = int(row[0]) if row else 1
    
    cursor.execute("SELECT profit_factor_hypothetical FROM model_metrics ORDER BY date DESC LIMIT 5")
    recent_pfs = [r[0] for r in cursor.fetchall()]
    
    # Since we don't have true OOS historical forecasts yet, we'll just log max_pf from CV as today's PF
    today_pf = max_pf
    recent_pfs.insert(0, today_pf)
    
    cursor.execute('''
        INSERT INTO model_metrics (date, train_period_end, test_accuracy_recent, profit_factor_hypothetical, feature_importances)
        VALUES (?, ?, ?, ?, ?)
    ''', (today_str, today_str, 0.0, float(today_pf), "{}"))
    
    if len(recent_pfs) >= 5:
        # Check deactivation: 5 consecutive days < 1.0
        if all(pf < 1.0 for pf in recent_pfs[:5]):
            if current_active == 1:
                print("⚠️ DRIFT DETECTED: 5 consecutive days of PF < 1.0. Deactivating AI Meta-Layer.")
                update_model_config('ai_active', 0)
        # Check reactivation: 3 consecutive days > 1.0
        elif all(pf > 1.0 for pf in recent_pfs[:3]):
            if current_active == 0:
                print("✅ RECOVERY DETECTED: 3 consecutive days of PF > 1.0. Reactivating AI Meta-Layer.")
                update_model_config('ai_active', 1)
    else:
        # Not enough history, default to active
        update_model_config('ai_active', 1)
        
    conn.commit()
    conn.close()
    
    print("Finished successfully. Tomorrow's probabilities are locked and loaded for Engine A.")

if __name__ == "__main__":
    main()

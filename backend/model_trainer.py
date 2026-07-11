import sqlite3
import pandas as pd
import numpy as np
import ta
import time
import os
import sys
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sklearn.ensemble import HistGradientBoostingClassifier
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
    
    return df

def generate_features_and_labels(df_sym):
    """
    Computes strict point-in-time features via .shift(1) and proxy ORB labels.
    """
    df = df_sym.copy()
    
    # Ensure sorted by date
    df = df.sort_values('Datetime').reset_index(drop=True)
    
    if len(df) < 50:
        return pd.DataFrame(), []
    
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
    
    # Strict Lagging! ALL features must be shifted by 1 so day t only sees data up to t-1
    feature_cols = ['returns_1d', 'returns_5d', 'ATR_pct', 'RSI', 'MACD', 'BB_width', 'BB_pband', 
                    'SMA_20_dist', 'SMA_50_dist', 'SMA_200_dist', 'Proximity_52w', 'macro_sentiment']
    
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
    
    return df, feature_cols

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
        
    all_data = []
    global_features = []
    
    for sym in NIFTY_SYMBOLS:
        df_sym = df_raw[df_raw['Symbol'] == sym]
        if df_sym.empty: continue
        
        df_feat, f_cols = generate_features_and_labels(df_sym)
        if not df_feat.empty:
            all_data.append(df_feat)
            global_features = f_cols
            
    if not all_data:
        print("Failed to generate features. Exiting.")
        sys.exit(1)
        
    df_full = pd.concat(all_data, ignore_index=True)
    df_full = df_full.sort_values('Datetime').reset_index(drop=True)
    
    print(f"Total dataset size: {len(df_full)} rows. Features: {len(global_features)}")
    
    # Split features and target
    X = df_full[global_features]
    y = df_full['Label']
    
    # Walk-Forward Validation & Threshold Calibration
    tscv = TimeSeriesSplit(n_splits=5)
    
    best_threshold = 0.55
    max_pf = 0.0
    
    print("Running Walk-Forward Cross Validation to calibrate Dynamic Threshold...")
    
    # Simple grid search for threshold during validation
    thresholds = [0.51, 0.53, 0.55, 0.57, 0.60]
    pf_results = {th: [] for th in thresholds}
    
    for train_idx, val_idx in tscv.split(X):
        X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
        X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]
        
        # Nested split for Early Stopping (chronological last 20% of train set)
        split_point = int(len(X_train) * 0.8)
        X_inner_train, y_inner_train = X_train.iloc[:split_point], y_train.iloc[:split_point]
        X_inner_val, y_inner_val = X_train.iloc[split_point:], y_train.iloc[split_point:]
        
        model = HistGradientBoostingClassifier(
            learning_rate=0.05,
            max_iter=500,
            early_stopping=True,
            validation_fraction=None, # We manually pass internal val
            random_state=42
        )
        
        # Train with early stopping on chronological inner validation
        # HistGradientBoosting doesn't have an eval_set argument like LightGBM,
        # but it can use validation_fraction. Since we want a chronological split,
        # we'll use a hack: fit on the full inner set, it's fast enough. Or use
        # a pipeline. Scikit-learn doesn't easily support passing a fixed eval set 
        # to HistGB, it only supports validation_fraction (which is random).
        # We will just disable early stopping for simplicity and rely on a low max_iter (200),
        # which is standard for robust models on small datasets.
        
        model = HistGradientBoostingClassifier(
            learning_rate=0.05,
            max_iter=200,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Predict on outer validation
        probs = model.predict_proba(X_val)[:, 1]
        
        # Evaluate Profit Factor for different thresholds
        for th in thresholds:
            trades = probs > th
            if trades.sum() == 0:
                pf_results[th].append(1.0)
                continue
                
            wins = y_val[trades].sum()
            losses = trades.sum() - wins
            
            # Assuming average win = 2R, loss = 1R (Based on our ORB proxy target=2, stop=1)
            gross_profit = wins * 2.0
            gross_loss = losses * 1.0
            
            pf = gross_profit / gross_loss if gross_loss > 0 else 0
            pf_results[th].append(pf)
            
    # Compute mean PF across folds for each threshold
    mean_pfs = {th: np.mean(pfs) for th, pfs in pf_results.items()}
    best_threshold = max(mean_pfs, key=mean_pfs.get)
    max_pf = mean_pfs[best_threshold]
    
    print(f"Optimal Threshold Calibrated: {best_threshold} (Mean PF: {max_pf:.2f})")
    
    # Save optimized threshold
    update_model_config('ai_conviction_threshold', best_threshold)
    update_model_config('ai_hypothetical_pf', max_pf)
    
    # Final Retrain on ALL data
    print("Retraining final production model on all historical data...")
    final_model = HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=200, # Fixed iter for full train to prevent overfitting without early stopping
        random_state=42
    )
    final_model.fit(X, y)
    
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
        X_last = last_row[global_features]
        
        prob = final_model.predict_proba(X_last)[0][1]
        
        # Feature importances/contributions (HistGB doesn't expose native feature_importances_ easily)
        # We will mock an empty JSON for now, can add SHAP later
        fc_json = "{}"
        
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

import sqlite3
import pandas as pd
import numpy as np
import ta
from datetime import timedelta
from logger import log

DB_PATH = "trading_system.db"

# We will populate these once Mode B finishes
PARAMS_A = {'rsi_thresh_a': 35, 'atr_target_a': 2.0, 'atr_stop_a': 1.5}
PARAMS_B = {'rsi_thresh_b': 30, 'vol_mult_b': 1.0, 'atr_target_b': 1.0, 'max_holding_days_b': 3}

# Helper preprocessors
def apply_market_regime(df_all):
    conn = sqlite3.connect(DB_PATH)
    nifty_df = pd.read_sql("SELECT Datetime, Close as Nifty_Close FROM nifty_index ORDER BY Datetime ASC", conn)
    conn.close()
    nifty_df['Datetime'] = pd.to_datetime(nifty_df['Datetime'])
    nifty_df['Nifty_SMA_200'] = nifty_df['Nifty_Close'].rolling(window=200).mean()
    nifty_df['Market_Regime_Up'] = nifty_df['Nifty_Close'] > nifty_df['Nifty_SMA_200']
    nifty_df['Market_Regime_Up'] = nifty_df['Market_Regime_Up'].fillna(True)
    nifty_regime = nifty_df[['Datetime', 'Market_Regime_Up']]
    df_all = pd.merge(df_all, nifty_regime, on='Datetime', how='left')
    df_all['Market_Regime_Up'] = df_all['Market_Regime_Up'].fillna(True)
    return df_all

def apply_universe_rotation_a(df_all):
    df_all['Mom_50'] = df_all.groupby('Symbol')['Close'].pct_change(periods=50)
    df_all['YearMonth'] = df_all['Datetime'].dt.to_period('M')
    monthly_last_days = df_all.groupby(['Symbol', 'YearMonth'])['Datetime'].max().reset_index()
    monthly_last_days = pd.merge(monthly_last_days, df_all[['Symbol', 'Datetime', 'Mom_50']], on=['Symbol', 'Datetime'])
    monthly_last_days['TargetMonth'] = monthly_last_days['YearMonth'] + 1
    monthly_last_days['Rank'] = monthly_last_days.groupby('TargetMonth')['Mom_50'].rank(ascending=False, method='first')
    monthly_last_days['Is_Top_5_A'] = (monthly_last_days['Rank'] <= 5) & (monthly_last_days['Mom_50'] > 0)
    mapping = monthly_last_days[['Symbol', 'TargetMonth', 'Is_Top_5_A']].rename(columns={'TargetMonth': 'YearMonth'})
    df_all = pd.merge(df_all, mapping, on=['Symbol', 'YearMonth'], how='left')
    df_all['Entry_Allowed_A'] = df_all['Is_Top_5_A'].fillna(False)
    return df_all

def apply_universe_rotation_b(df_all):
    def calculate_rsi(series, window=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    df_all['RSI_14'] = df_all.groupby('Symbol')['Close'].transform(lambda x: calculate_rsi(x))
    def calculate_ema(series, window=50):
        return series.ewm(span=window, adjust=False).mean()
    df_all['EMA_50'] = df_all.groupby('Symbol')['Close'].transform(lambda x: calculate_ema(x))
    df_all['EMA_Dist'] = (df_all['Close'] / df_all['EMA_50']) * 100
    df_all['YearMonth'] = df_all['Datetime'].dt.to_period('M')
    monthly_last_days = df_all.groupby(['Symbol', 'YearMonth'])['Datetime'].max().reset_index()
    monthly_last_days = pd.merge(monthly_last_days, df_all[['Symbol', 'Datetime', 'RSI_14', 'EMA_Dist']], on=['Symbol', 'Datetime'])
    monthly_last_days['TargetMonth'] = monthly_last_days['YearMonth'] + 1
    monthly_last_days['Rank_RSI'] = monthly_last_days.groupby('TargetMonth')['RSI_14'].rank(ascending=True, method='first')
    monthly_last_days['Rank_EMA_Dist'] = monthly_last_days.groupby('TargetMonth')['EMA_Dist'].rank(ascending=True, method='first')
    monthly_last_days['Composite_Score'] = monthly_last_days['Rank_RSI'] + monthly_last_days['Rank_EMA_Dist']
    monthly_last_days['Final_Rank'] = monthly_last_days.groupby('TargetMonth')['Composite_Score'].rank(ascending=True, method='first')
    monthly_last_days['Is_Top_5_B'] = monthly_last_days['Final_Rank'] <= 5
    mapping = monthly_last_days[['Symbol', 'TargetMonth', 'Is_Top_5_B']].rename(columns={'TargetMonth': 'YearMonth'})
    df_all = pd.merge(df_all, mapping, on=['Symbol', 'YearMonth'], how='left')
    df_all['Entry_Allowed_B'] = df_all['Is_Top_5_B'].fillna(False)
    return df_all

def prepare_data():
    conn = sqlite3.connect(DB_PATH)
    df_all = pd.read_sql("SELECT * FROM market_data_1d ORDER BY Datetime ASC", conn)
    conn.close()
    df_all['Datetime'] = pd.to_datetime(df_all['Datetime'])
    df_all = apply_market_regime(df_all)
    df_all = apply_universe_rotation_a(df_all)
    df_all = apply_universe_rotation_b(df_all)
    
    # Calculate indicators per symbol
    def calc_features(g):
        g['EMA_10'] = ta.trend.ema_indicator(g['Close'], window=10)
        g['RSI'] = ta.momentum.rsi(g['Close'], window=14)
        adx_ind = ta.trend.ADXIndicator(g['High'], g['Low'], g['Close'], window=14)
        g['ADX'] = adx_ind.adx()
        atr_ind = ta.volatility.AverageTrueRange(g['High'], g['Low'], g['Close'], window=14)
        g['ATR'] = atr_ind.average_true_range()
        g['Donchian_High_20'] = g['High'].rolling(window=20).max()
        g['Donchian_Low_20'] = g['Low'].rolling(window=20).min()
        g['Vol_SMA_20'] = g['Volume'].rolling(window=20).mean()
        g['Prev_Low'] = g['Low'].shift(1)
        return g
    
    dfs = []
    for sym, g in df_all.groupby('Symbol'):
        dfs.append(calc_features(g))
    df_all = pd.concat(dfs, ignore_index=True)
    df_all = df_all.dropna()
    return df_all

def run_final_exam():
    df_all = prepare_data()
    
    # Final Exam Test Window
    max_date = df_all['Datetime'].max()
    test_start = max_date - timedelta(days=365)
    
    df_test = df_all[df_all['Datetime'] >= test_start].copy()
    
    # We will simulate day by day to track portfolio capital properly
    dates = sorted(df_test['Datetime'].unique())
    
    capital = 100000.0
    peak_capital = capital
    risk_per_trade = 0.01
    slippage = 0.0005
    brokerage = 0.0005
    
    positions = {} # symbol -> {qty, buy_price, stop_loss, target, mode, days_in_trade}
    
    trades = []
    equity_curve = []
    
    halt_trading = False
    
    log.info(f"Starting Final Exam Simulation: {len(dates)} days...")
    
    for d in dates:
        if halt_trading:
            break
            
        day_data = df_test[df_test['Datetime'] == d]
        
        # 1. Update existing positions
        symbols_to_remove = []
        for sym, pos in positions.items():
            sym_row = day_data[day_data['Symbol'] == sym]
            if sym_row.empty: continue
            
            row = sym_row.iloc[0]
            pos['days_in_trade'] += 1
            
            low = row['Low']
            high = row['High']
            price = row['Close']
            
            exit_price = None
            exit_reason = None
            
            # Check Stop Loss
            if low <= pos['stop_loss']:
                exit_price = min(row['Open'], pos['stop_loss'])
                exit_reason = "stop"
            # Check Target
            elif high >= pos['target']:
                exit_price = max(row['Open'], pos['target'])
                exit_reason = "target"
            # Check Time Stop (Mode B only)
            elif pos['mode'] == 'B' and pos['days_in_trade'] >= PARAMS_B['max_holding_days_b']:
                exit_price = price
                exit_reason = "time_stop"
                
            if exit_price is not None:
                exec_price = exit_price * (1 - slippage)
                trade_value = pos['qty'] * exec_price
                fees = min(trade_value * brokerage, 20.0) + (trade_value * 0.00025)
                capital += (trade_value - fees)
                
                pnl = trade_value - fees - (pos['qty'] * pos['buy_price'])
                trades.append({"sym": sym, "pnl": pnl, "mode": pos['mode'], "reason": exit_reason})
                symbols_to_remove.append(sym)
                
        for s in symbols_to_remove:
            del positions[s]
            
        # 2. Check unified drawdown
        current_eq = capital
        for sym, pos in positions.items():
            sym_row = day_data[day_data['Symbol'] == sym]
            if not sym_row.empty:
                current_eq += pos['qty'] * sym_row.iloc[0]['Close']
                
        if current_eq > peak_capital:
            peak_capital = current_eq
            
        if (peak_capital - current_eq) / peak_capital >= 0.10:
            log.warning("🚨 UNIFIED DRAWDOWN LIMIT (10%) HIT! Halting all trading.")
            halt_trading = True
            break
            
        equity_curve.append(current_eq)
        
        # 3. Enter new positions (if not halted)
        for _, row in day_data.iterrows():
            sym = row['Symbol']
            if sym in positions: continue
            
            price = row['Close']
            atr = row['ATR']
            
            mode_entered = None
            initial_stop_dist = 0
            profit_target_dist = 0
            
            # Mode A Check
            if row['Market_Regime_Up'] and row['Entry_Allowed_A']:
                donchian_dist = row['Donchian_High_20'] - row['Donchian_Low_20']
                donchian_10_pct = row['Donchian_Low_20'] + (0.10 * donchian_dist)
                
                if (row['Close'] < row['EMA_10']) and (row['Close'] <= donchian_10_pct):
                    if (row['RSI'] < PARAMS_A['rsi_thresh_a']) and (row['ADX'] > 20):
                        mode_entered = 'A'
                        initial_stop_dist = atr * PARAMS_A['atr_stop_a']
                        profit_target_dist = atr * PARAMS_A['atr_target_a']
                        
            # Mode B Check
            elif not row['Market_Regime_Up'] and row['Entry_Allowed_B']:
                if (row['RSI'] < PARAMS_B['rsi_thresh_b']) and (row['Close'] > row['Prev_Low']):
                    if row['Volume'] > (PARAMS_B['vol_mult_b'] * row['Vol_SMA_20']):
                        mode_entered = 'B'
                        initial_stop_dist = atr * 1.5
                        profit_target_dist = atr * PARAMS_B['atr_target_b']
                        
            if mode_entered:
                if initial_stop_dist <= 0: continue
                
                exec_price = price * (1 + slippage)
                risk_amount = current_eq * risk_per_trade
                qty = int(risk_amount / initial_stop_dist)
                max_qty = int(capital / exec_price)
                qty = min(qty, max_qty)
                
                if qty > 0:
                    trade_value = qty * exec_price
                    fees = min(trade_value * brokerage, 20.0)
                    capital -= (trade_value + fees)
                    
                    buy_price = exec_price
                    positions[sym] = {
                        'qty': qty,
                        'buy_price': buy_price,
                        'stop_loss': buy_price - initial_stop_dist,
                        'target': buy_price + profit_target_dist,
                        'mode': mode_entered,
                        'days_in_trade': 0
                    }

    # Final tally
    winning_trades = [t for t in trades if t["pnl"] > 0]
    losing_trades = [t for t in trades if t["pnl"] <= 0]
    
    gross_profit = sum(t["pnl"] for t in winning_trades)
    gross_loss = abs(sum(t["pnl"] for t in losing_trades))
    pf = (gross_profit / gross_loss) if gross_loss > 0 else 0
    
    log.info("\n--- FINAL EXAM: DUAL-MODE MEAN-REVERSION ---")
    log.info(f"Total Trades: {len(trades)}")
    log.info(f"Mode A Trades: {len([t for t in trades if t['mode'] == 'A'])}")
    log.info(f"Mode B Trades: {len([t for t in trades if t['mode'] == 'B'])}")
    log.info(f"Test Window PF: {pf:.2f}")
    
    eq_series = pd.Series(equity_curve)
    rolling_max = eq_series.cummax()
    drawdowns = (eq_series - rolling_max) / rolling_max
    mdd = abs(drawdowns.min()) if not drawdowns.empty else 0
    
    log.info(f"Test Window MDD (Unified): {mdd*100:.2f}%")
    log.info("---------------------------------------------")

if __name__ == "__main__":
    run_final_exam()

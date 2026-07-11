import sqlite3
import pandas as pd
import numpy as np
import ta
from walk_forward_v7 import compute_regimes, load_data
from logger import log

BEST_ORB = {'orb_bars': 6, 'orb_target': 2.0, 'orb_stop': 1.0}
BEST_VWAP = None

def prepare_intraday_data():
    df_all = load_data()
    df_all = df_all[df_all['Symbol'] != '^NSEI'].copy()
    df_all = compute_regimes(df_all)
    
    # Calculate indicators per symbol
    def calc_features(g):
        g['ATR'] = ta.volatility.AverageTrueRange(g['High'], g['Low'], g['Close'], window=14).average_true_range()
        g['RSI'] = ta.momentum.rsi(g['Close'], window=14)
        return g
        
    dfs = []
    for sym, g in df_all.groupby('Symbol'):
        dfs.append(calc_features(g))
    df_all = pd.concat(dfs, ignore_index=True)
    
    return df_all

def run_intraday_final_exam():
    df_all = prepare_intraday_data()
    
    unique_dates = sorted(df_all['Date'].unique())
    if len(unique_dates) < 50:
        log.warning("Not enough data for final exam!")
        return
        
    # Validation Window is Days 41-50
    dates_val = unique_dates[40:50]
    
    df_val = df_all[df_all['Date'].isin(dates_val)].copy()
    
    capital = 100000.0
    peak_capital = capital
    risk_per_trade = 0.01
    slippage = 0.0005
    brokerage = 0.0005
    
    trades = []
    equity_curve = [capital]
    halt_trading = False
    
    log.info(f"Starting Intraday Combined Final Exam: {len(dates_val)} days...")
    
    for d in dates_val:
        if halt_trading:
            break
            
        day_data = df_val[df_val['Date'] == d].copy()
        
        # Calculate VWAP for all symbols today
        day_data['Cum_Vol'] = day_data.groupby('Symbol')['Volume'].cumsum()
        day_data['Cum_Vol_Price'] = day_data.groupby('Symbol').apply(
            lambda x: (x['Volume'] * (x['High'] + x['Low'] + x['Close']) / 3).cumsum()
        ).reset_index(level=0, drop=True)
        day_data['VWAP'] = day_data['Cum_Vol_Price'] / day_data['Cum_Vol']
        
        # Calculate ORB high/low
        orb_bars = BEST_ORB['orb_bars']
        def get_orb(g):
            if len(g) >= orb_bars:
                return pd.Series({'ORB_High': g.iloc[:orb_bars]['High'].max(), 'ORB_Low': g.iloc[:orb_bars]['Low'].min()})
            return pd.Series({'ORB_High': np.nan, 'ORB_Low': np.nan})
            
        orb_stats = day_data.groupby('Symbol').apply(get_orb).reset_index()
        day_data = pd.merge(day_data, orb_stats, on='Symbol')
        
        # To simulate properly, we step through intraday times
        times = sorted(day_data['Datetime'].unique())
        
        positions = {} # sym: {qty, entry, stop, target, mode}
        
        for t in times:
            t_data = day_data[day_data['Datetime'] == t]
            
            # 1. Update Positions
            symbols_to_remove = []
            for sym, pos in positions.items():
                sym_row = t_data[t_data['Symbol'] == sym]
                if sym_row.empty: continue
                
                row = sym_row.iloc[0]
                price = row['Close']
                low = row['Low']
                high = row['High']
                
                exit_price = None
                exit_reason = None
                
                # EOD Liquidation at 15:25
                if row['Datetime'].hour == 15 and row['Datetime'].minute >= 25:
                    exit_price = price
                    exit_reason = "eod_stop"
                elif low <= pos['stop_loss']:
                    exit_price = min(row['Open'], pos['stop_loss'])
                    exit_reason = "stop"
                elif high >= pos['target']:
                    exit_price = max(row['Open'], pos['target'])
                    exit_reason = "target"
                    
                if exit_price is not None:
                    exec_price = exit_price * (1 - slippage)
                    trade_value = pos['qty'] * exec_price
                    fees = min(trade_value * brokerage, 20.0) + (trade_value * 0.00025)
                    capital += (trade_value - fees)
                    
                    pnl = trade_value - fees - (pos['qty'] * pos['buy_price'])
                    trades.append({"sym": sym, "pnl": pnl, "mode": pos['mode'], "reason": exit_reason, "date": d})
                    symbols_to_remove.append(sym)
                    
            for s in symbols_to_remove:
                del positions[s]
                
            # 2. Check Unified MDD
            current_eq = capital
            for sym, pos in positions.items():
                sym_row = t_data[t_data['Symbol'] == sym]
                if not sym_row.empty:
                    current_eq += pos['qty'] * sym_row.iloc[0]['Close']
                    
            if current_eq > peak_capital:
                peak_capital = current_eq
                
            if (peak_capital - current_eq) / peak_capital >= 0.10:
                log.warning("🚨 UNIFIED INTRADAY DRAWDOWN LIMIT (10%) HIT! Halting all trading.")
                halt_trading = True
                break
                
            equity_curve.append(current_eq)
            
            # 3. Enter Positions
            # Don't enter after 15:00
            if t.hour >= 15: continue
            
            for _, row in t_data.iterrows():
                sym = row['Symbol']
                if sym in positions: continue
                
                # Check if we already traded this symbol today (one trade per day per stock rule)
                if any(tr['sym'] == sym and tr['date'] == d for tr in trades):
                    continue
                
                price = row['Close']
                atr = row['ATR']
                if pd.isna(atr): continue
                
                mode_entered = None
                initial_stop_dist = 0
                profit_target_dist = 0
                
                # Check ORB
                if row['Regime'] == 'ORB':
                    # Need to be past the ORB formation time
                    # We can use row index or time check. ORB bars is e.g. 3 (15 mins)
                    # We just need price > ORB_High
                    if pd.notna(row['ORB_High']) and price > row['ORB_High']:
                        mode_entered = 'ORB'
                        initial_stop_dist = atr * BEST_ORB['orb_stop']
                        profit_target_dist = atr * BEST_ORB['orb_target']
                        
                elif row['Regime'] == 'VWAP' and BEST_VWAP is not None:
                    # Check VWAP Dip
                    # Need to wait 5 bars (25 mins) for VWAP to stabilize
                    # We'll just enforce a time check > 09:40
                    if t.hour > 9 or (t.hour == 9 and t.minute > 40):
                        vwap = row['VWAP']
                        if (vwap - price) > (BEST_VWAP['vwap_dev_atr'] * atr):
                            if row['RSI'] < BEST_VWAP['vwap_rsi']:
                                mode_entered = 'VWAP'
                                initial_stop_dist = atr * BEST_VWAP['vwap_stop']
                                profit_target_dist = vwap - price # Target is VWAP
                                
                if mode_entered:
                    if initial_stop_dist <= 0: continue
                    exec_price = price * (1 + slippage)
                    risk_amount = capital * risk_per_trade
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
                            'mode': mode_entered
                        }

    # Liquidation at end of test
    winning_trades = [t for t in trades if t["pnl"] > 0]
    losing_trades = [t for t in trades if t["pnl"] <= 0]
    
    gross_profit = sum(t["pnl"] for t in winning_trades)
    gross_loss = abs(sum(t["pnl"] for t in losing_trades))
    pf = (gross_profit / gross_loss) if gross_loss > 0 else 0
    
    log.info("\n--- FINAL EXAM: INTRADAY DUAL-MODE ---")
    log.info(f"Total Trades: {len(trades)}")
    log.info(f"Mode ORB Trades: {len([t for t in trades if t['mode'] == 'ORB'])}")
    log.info(f"Mode VWAP Trades: {len([t for t in trades if t['mode'] == 'VWAP'])}")
    log.info(f"Val Window PF: {pf:.2f}")
    
    eq_series = pd.Series(equity_curve)
    rolling_max = eq_series.cummax()
    drawdowns = (eq_series - rolling_max) / rolling_max
    mdd = abs(drawdowns.min()) if not drawdowns.empty else 0
    
    log.info(f"Val Window MDD (Unified): {mdd*100:.2f}%")
    log.info("--------------------------------------")

if __name__ == "__main__":
    run_intraday_final_exam()

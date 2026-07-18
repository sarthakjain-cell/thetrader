import pandas as pd
import numpy as np
import yfinance as yf
import ta
import time
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from feature_engine import compute_features
from logger import log
import warnings
warnings.filterwarnings('ignore')

NIFTY_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "ITC.NS",
    "LT.NS", "BHARTIARTL.NS", "HINDUNILVR.NS"
]

def fetch_data(symbol):
    df = yf.download(symbol, period='60d', interval='5m', progress=False)
    if df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Datetime', 'datetime': 'Datetime'}, inplace=True)
    if df['Datetime'].dt.tz is None:
        df['Datetime'] = df['Datetime'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
    else:
        df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata')
        
    df['Date'] = df['Datetime'].dt.date
    return df

class Backtester:
    def __init__(self, initial_capital=100000.0, stop_mult=1.0, target_mult=2.0, trail_enable=True):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.peak_capital = initial_capital
        self.positions = {}
        self.trades = []
        
        self.best_orb = {'orb_bars': 6, 'orb_target': target_mult, 'orb_stop': stop_mult}
        self.risk_per_trade = 0.01
        self.trail_enable = trail_enable
        
    def _compute_dynamic_slippage(self, range_pct, avg_range_pct):
        baseline = 0.0005
        if avg_range_pct == 0: return baseline
        excess_pct = max(0, (range_pct / avg_range_pct) - 1.0) * 100
        additional = excess_pct * 0.0001
        return baseline + additional

    def run(self, sym, df):
        df = compute_features(df)
        
        daily_firsts = df.groupby('Date').first()
        daily_firsts['OpenRange'] = daily_firsts['High'] - daily_firsts['Low']
        daily_firsts['AvgOpenRange'] = daily_firsts['OpenRange'].rolling(10).mean().shift(1)
        
        avg_5m_range = ((df['High'] - df['Low']) / df['Close']).mean()
        
        current_date = None
        regime = "WAITING"
        orb_high = None
        bars_today = 0
        
        for i in range(14, len(df)):
            bar = df.iloc[i]
            prev_bar = df.iloc[i-1]
            bar_date = bar['Date']
            
            if bar_date != current_date:
                if sym in self.positions:
                    self._close_position(sym, prev_bar['Close'], bar['Datetime'], "EOD")
                
                current_date = bar_date
                regime = "WAITING"
                orb_high = None
                bars_today = 0
                
                first_range = bar['High'] - bar['Low']
                try:
                    avg_open_range = daily_firsts.loc[bar_date]['AvgOpenRange']
                except:
                    avg_open_range = float('inf')
                    
                if pd.isna(avg_open_range):
                    avg_open_range = float('inf')
                    
                if first_range > avg_open_range and bar['Close'] > bar['Open']:
                    regime = "ORB"
                else:
                    regime = "VWAP"
                    
            bars_today += 1
            
            if regime == "ORB" and bars_today == self.best_orb['orb_bars']:
                today_data = df[df['Date'] == bar_date].iloc[:bars_today]
                orb_high = today_data['High'].max()
                
            if sym in self.positions:
                pos = self.positions[sym]
                high = bar['High']
                low = bar['Low']
                
                if self.trail_enable:
                    if pos['direction'] == 'LONG':
                        risk_dist = pos['entry_price'] - pos['stop_loss']
                        if risk_dist > 0 and high >= (pos['entry_price'] + risk_dist) and pos['stop_loss'] < pos['entry_price']:
                            pos['stop_loss'] = pos['entry_price']
                    else:
                        risk_dist = pos['stop_loss'] - pos['entry_price']
                        if risk_dist > 0 and low <= (pos['entry_price'] - risk_dist) and pos['stop_loss'] > pos['entry_price']:
                            pos['stop_loss'] = pos['entry_price']
                        
                exit_price = None
                reason = None
                if pos['direction'] == 'LONG':
                    if low <= pos['stop_loss']:
                        exit_price = min(bar['Open'], pos['stop_loss'])
                        reason = "STOP"
                    elif high >= pos['target']:
                        exit_price = max(bar['Open'], pos['target'])
                        reason = "TARGET"
                else:
                    if high >= pos['stop_loss']:
                        exit_price = max(bar['Open'], pos['stop_loss'])
                        reason = "STOP"
                    elif low <= pos['target']:
                        exit_price = min(bar['Open'], pos['target'])
                        reason = "TARGET"
                        
                if exit_price is not None:
                    self._close_position(sym, exit_price, bar['Datetime'], reason)
                    continue
            
            if sym not in self.positions and bars_today >= 14:
                if bar['Datetime'].hour >= 15:
                    continue
                    
                price = bar['Close']
                adx = bar.get('ADX_14', 0)
                ema9 = bar.get('EMA_9', 0)
                ema21 = bar.get('EMA_21', 0)
                vwap = bar.get('VWAP', 0)
                
                is_hammer = bar.get('CDL_Hammer', 0) == 1
                is_engulf = bar.get('CDL_Engulfing_Bull', 0) == 1
                is_shoot = bar.get('CDL_Shooting_Star', 0) == 1
                is_marubozu = bar.get('CDL_Marubozu', 0) == 1
                
                vol_avg = bar.get('Volume_SMA_20', 1)
                vol_spike = bar['Volume'] / vol_avg if vol_avg > 0 else 1.0
                
                dynamic_regime = regime
                if price > ema21 and adx > 25 and regime != 'ORB':
                    dynamic_regime = 'EMA_TREND'
                    
                signal = None
                direction = None
                
                if dynamic_regime == 'EMA_TREND':
                    if (ema9 * 0.998) <= price <= (ema9 * 1.002) and (is_hammer or is_engulf):
                        signal = "BUY"
                        direction = 'LONG'
                elif dynamic_regime == 'ORB' and orb_high is not None:
                    if price > orb_high and (is_marubozu or vol_spike > 1.5):
                        signal = "BUY"
                        direction = 'LONG'
                elif dynamic_regime == 'VWAP':
                    if price < (vwap * 0.998) and (is_hammer or is_engulf):
                        signal = "BUY"
                        direction = 'LONG'
                    elif price > (vwap * 1.002) and is_shoot:
                        signal = "SELL"
                        direction = 'SHORT'
                        
                if signal:
                    atr = bar.get('ATR_14', 5.0)
                    if pd.isna(atr): atr = price * 0.005
                    range_pct = (bar['High'] - bar['Low']) / price
                    slippage = self._compute_dynamic_slippage(range_pct, avg_5m_range)
                    
                    exec_price = price * (1 + slippage) if direction == 'LONG' else price * (1 - slippage)
                    stop_dist = atr * self.best_orb['orb_stop']
                    
                    if stop_dist > 0:
                        risk_amt = self.capital * self.risk_per_trade
                        qty = int(risk_amt / stop_dist)
                        max_qty = int(self.capital / exec_price)
                        qty = min(qty, max_qty)
                        
                        if qty > 0:
                            trade_value = qty * exec_price
                            brokerage = min(trade_value * 0.0005, 20.0)
                            self.capital -= (trade_value + brokerage)
                            
                            stop_loss = exec_price - stop_dist if direction == 'LONG' else exec_price + stop_dist
                            target = exec_price + (atr * self.best_orb['orb_target']) if direction == 'LONG' else exec_price - (atr * self.best_orb['orb_target'])
                            
                            self.positions[sym] = {
                                'entry_time': bar['Datetime'],
                                'entry_price': exec_price,
                                'qty': qty,
                                'stop_loss': stop_loss,
                                'target': target,
                                'direction': direction,
                                'regime': dynamic_regime
                            }
                            
    def _close_position(self, sym, exit_price, exit_time, reason):
        pos = self.positions.pop(sym)
        qty = pos['qty']
        entry = pos['entry_price']
        direction = pos['direction']
        
        trade_value = qty * exit_price
        brokerage = min(trade_value * 0.0005, 20.0) + (trade_value * 0.00025)
        
        if direction == 'LONG':
            pnl = trade_value - brokerage - (qty * entry)
            self.capital += (trade_value - brokerage)
        else:
            pnl = (qty * entry) - trade_value - brokerage
            self.capital += (qty * entry) + pnl
            
        self.peak_capital = max(self.peak_capital, self.capital)
        
        self.trades.append({
            'symbol': sym,
            'direction': direction,
            'regime': pos['regime'],
            'entry_time': pos['entry_time'],
            'exit_time': exit_time,
            'pnl': pnl,
            'reason': reason
        })

if __name__ == "__main__":
    print("Loading historical data...")
    cache = {}
    for sym in NIFTY_SYMBOLS:
        df = fetch_data(sym)
        if df is not None and not df.empty:
            cache[sym] = df
            
    print(f"Data loaded for {len(cache)} symbols. Starting optimization...")
    
    scenarios = [
        (1.0, 2.0, True),  # Original
        (1.5, 3.0, False), # Wider stop, wider target, no trailing
        (2.0, 1.5, False), # Very wide stop, tight target (high win rate)
        (1.0, 1.5, True)   # Tight stop, moderate target, trailing
    ]
    
    best_pf = 0
    best_scenario = None
    
    for stop_m, target_m, trail in scenarios:
        tester = Backtester(initial_capital=100000.0, stop_mult=stop_m, target_mult=target_m, trail_enable=trail)
        for sym, df in cache.items():
            tester.run(sym, df)
            
        if len(tester.trades) > 0:
            trades_df = pd.DataFrame(tester.trades)
            wins = trades_df[trades_df['pnl'] > 0]
            losses = trades_df[trades_df['pnl'] <= 0]
            
            gross_profit = wins['pnl'].sum() if len(wins) > 0 else 0
            gross_loss = abs(losses['pnl'].sum()) if len(losses) > 0 else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
            win_rate = len(wins) / len(tester.trades) * 100
            
            print(f"\n[Stop: {stop_m}x ATR | Target: {target_m}x ATR | Trail: {trail}]")
            print(f"Trades: {len(tester.trades)} | Win Rate: {win_rate:.1f}% | PF: {profit_factor:.2f} | Net PnL: Rs {trades_df['pnl'].sum():.2f}")
            
            if profit_factor > best_pf:
                best_pf = profit_factor
                best_scenario = (stop_m, target_m, trail)
                
    print(f"\nOptimization Complete. Best PF: {best_pf:.2f} with Stop={best_scenario[0]}, Target={best_scenario[1]}, Trail={best_scenario[2]}")

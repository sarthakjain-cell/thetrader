import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from logger import log
from feature_engine import compute_features

# Import all strategies
from strategy_001_orb import Strategy001ORB
from strategy_002_vwap import Strategy002VWAP
from strategy_003_momentum import Strategy003Momentum
from strategy_004_meanreversion import Strategy004MeanReversion
from strategy_005_rangefade import Strategy005RangeFade
from strategy_006_volclimax import Strategy006VolumeClimax
from strategy_008_gapfill import Strategy008GapFill

SYMBOLS = ["RELIANCE.NS", "HDFCBANK.NS", "TCS.NS"]
CAPITAL = 1_000_000.0

class BacktestEngine:
    def __init__(self):
        self.strategies = [
            Strategy001ORB(),
            Strategy002VWAP(),
            Strategy003Momentum(),
            Strategy004MeanReversion(),
            Strategy005RangeFade(),
            Strategy006VolumeClimax(),
            Strategy008GapFill()
        ]
        
    def fetch_historical_data(self, symbol, days=59):
        log.info(f"Downloading 5-minute data for {symbol}...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = yf.download(symbol, start=start_date, end=end_date, interval="5m", progress=False)
        if df.empty:
            log.error(f"No data for {symbol}")
            return df
            
        # Flatten MultiIndex columns if necessary
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
            
        df = df.reset_index()
        # Rename Date to Datetime if it exists
        if 'Date' in df.columns:
            df.rename(columns={'Date': 'Datetime'}, inplace=True)
            
        # Standardize column names
        df.columns = [c.capitalize() if c != 'Datetime' else c for c in df.columns]
        
        # Calculate features
        df = compute_features(df)
        return df

    def run_backtest(self, symbol, df):
        results = []
        
        for strategy in self.strategies:
            strat_id = strategy.strategy_id
            capital = CAPITAL
            position = None
            trades = []
            
            # Context stub
            context = {"sentiment": {}, "macro_alerts": [], "active_negative_stocks": set()}
            
            for i in range(len(df)):
                current_bar = df.iloc[i]
                
                if position:
                    # Manage
                    res = strategy.manage_position(symbol, position, current_bar)
                    if res.get("action") == "UPDATE_STOP":
                        position['stop_loss'] = res["new_stop"]
                    elif res.get("action") == "CLOSE":
                        exit_price = res.get("exit_price", current_bar['Close'])
                        trade_value = position['qty'] * exit_price
                        pnl = trade_value - (position['qty'] * position['entry_price'])
                        capital += (trade_value) # Simplified, no brokerage here
                        
                        trades.append({
                            "type": "SELL",
                            "pnl": pnl,
                            "reason": res.get("reason", "Exit")
                        })
                        position = None
                else:
                    # Evaluate
                    signal_dict = strategy.evaluate(symbol, current_bar, context)
                    if signal_dict["signal"] == "BUY":
                        price = current_bar['Close']
                        qty = int((capital * 0.10) / price) # 10% allocation per trade
                        
                        if qty > 0:
                            position = {
                                "entry_price": price,
                                "qty": qty,
                                "stop_loss": signal_dict.get("stop_loss", price*0.99),
                                "target": signal_dict.get("target", price*1.02)
                            }
                            capital -= (qty * price)
                            
            # End of loop square off
            if position:
                exit_price = df.iloc[-1]['Close']
                trade_value = position['qty'] * exit_price
                pnl = trade_value - (position['qty'] * position['entry_price'])
                trades.append({
                    "type": "SELL",
                    "pnl": pnl,
                    "reason": "EOD Square Off"
                })
                
            # Calculate Stats
            winning_trades = [t for t in trades if t["pnl"] > 0]
            losing_trades = [t for t in trades if t["pnl"] <= 0]
            
            win_rate = (len(winning_trades) / len(trades) * 100) if trades else 0.0
            gross_profit = sum(t["pnl"] for t in winning_trades)
            gross_loss = abs(sum(t["pnl"] for t in losing_trades))
            net_profit = gross_profit - gross_loss
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
            
            results.append({
                "Strategy": strat_id,
                "Symbol": symbol,
                "Trades": len(trades),
                "Win Rate": f"{win_rate:.1f}%",
                "Profit Factor": f"{profit_factor:.2f}",
                "Net PnL": f"Rs. {net_profit:.2f}"
            })
            
        return results

    def simulate_all(self):
        all_results = []
        for sym in SYMBOLS:
            df = self.fetch_historical_data(sym)
            if not df.empty:
                res = self.run_backtest(sym, df)
                all_results.extend(res)
                
        # Print tabular results
        results_df = pd.DataFrame(all_results)
        print("\n=== EPIC 16 MULTI-STRATEGY BACKTEST RESULTS (LAST 60 DAYS) ===")
        print(results_df.to_string(index=False))

if __name__ == "__main__":
    engine = BacktestEngine()
    engine.simulate_all()

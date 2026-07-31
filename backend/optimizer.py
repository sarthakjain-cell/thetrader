import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import optuna
from logger import log
from feature_engine import compute_features

# Import strategies
from strategy_001_orb import Strategy001ORB
from strategy_002_vwap import Strategy002VWAP

DB_PATH = "trading_system.db"

class WalkForwardOptimizer:
    def __init__(self, symbol: str, db_path=DB_PATH):
        self.symbol = symbol
        self.db_path = db_path
        
    def load_historical_data(self, days_back=60):
        """Loads historical 5m bars for the symbol."""
        conn = sqlite3.connect(self.db_path)
        cutoff = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        query = f"SELECT * FROM intraday_5m WHERE symbol = ? AND datetime >= ? ORDER BY datetime ASC"
        df = pd.read_sql(query, conn, params=(self.symbol, cutoff))
        conn.close()
        
        if len(df) == 0:
            return df
            
        # Standardize column names for feature_engine
        df = df.rename(columns={'datetime': 'Datetime', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        df = df.set_index('Datetime')
        
        return compute_features(df)
        
    def backtest_strategy(self, df: pd.DataFrame, strategy, params: dict) -> float:
        """Simulates trading and returns the profit factor."""
        strategy.set_parameters(params)
        
        capital = 100000.0
        position = None
        total_pnl = 0
        wins = 0
        losses = 0
        
        for timestamp, row in df.iterrows():
            # Time-based exit at 15:15
            if position and timestamp.hour == 15 and timestamp.minute >= 15:
                pnl = (row['Close'] - position['entry_price']) * position['qty']
                total_pnl += pnl
                if pnl > 0: wins += 1
                else: losses += 1
                position = None
                continue
                
            if position:
                # Manage
                res = strategy.manage_position(self.symbol, position, row)
                if res['action'] == 'CLOSE':
                    pnl = (res['exit_price'] - position['entry_price']) * position['qty']
                    total_pnl += pnl
                    if pnl > 0: wins += 1
                    else: losses += 1
                    position = None
                elif res['action'] == 'UPDATE_STOP':
                    position['stop_loss'] = res['new_stop']
            else:
                # Time filter: Don't enter after 14:30
                if timestamp.hour >= 14 and timestamp.minute >= 30:
                    continue
                    
                context = {'ai_forecasts': {self.symbol: 0.6}} # Mock AI conviction
                sig = strategy.evaluate(self.symbol, row, context)
                
                if sig['signal'] == 'BUY':
                    risk_amount = capital * 0.01 # 1% risk
                    if sig['stop_loss'] and sig['stop_loss'] < row['Close']:
                        risk_per_share = row['Close'] - sig['stop_loss']
                        qty = max(1, int(risk_amount / risk_per_share))
                        
                        position = {
                            'entry_price': row['Close'],
                            'qty': qty,
                            'stop_loss': sig['stop_loss'],
                            'target': sig['target']
                        }
                        
        profit_factor = wins / max(1, losses)
        # If no trades, penalize
        if (wins + losses) == 0: return -1.0
        
        # We optimize for profit factor combined with total PnL
        score = profit_factor * (total_pnl / capital)
        return score

    def optimize(self, strategy_class, n_trials=50) -> dict:
        """Runs Optuna to find the best parameters."""
        df = self.load_historical_data(days_back=30) # Train on last 30 days
        
        if len(df) < 100:
            log.warning(f"Not enough data for {self.symbol}")
            return {}
            
        def objective(trial):
            strategy = strategy_class()
            default_params = strategy.get_default_parameters()
            
            # Dynamically suggest params based on default keys
            trial_params = {}
            for k, v in default_params.items():
                if isinstance(v, float):
                    # Suggest within +/- 50% of default, ensuring low <= high
                    trial_params[k] = trial.suggest_float(k, min(v * 0.5, v * 1.5), max(v * 0.5, v * 1.5))
                elif isinstance(v, int):
                    trial_params[k] = trial.suggest_int(k, min(int(v*0.5), int(v*1.5)), max(int(v*0.5), int(v*1.5)))
                else:
                    trial_params[k] = v
                    
            return self.backtest_strategy(df, strategy, trial_params)
            
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials)
        
        best_params = study.best_params
        log.info(f"[{strategy_class().name}] Optimal Params for {self.symbol}: {best_params} (Score: {study.best_value:.4f})")
        return best_params

def save_optimized_parameters(symbol: str, strategy_id: str, params: dict):
    """Saves the optimal parameters to model_config in the DB."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    import json
    key = f"{symbol}_{strategy_id}_params"
    value_json = json.dumps(params)
    
    cursor.execute('''
        INSERT OR REPLACE INTO model_config (key, value, updated_at)
        VALUES (?, ?, ?)
    ''', (key, value_json, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    opt = WalkForwardOptimizer("RELIANCE.NS")
    
    print("Optimizing S001_ORB...")
    best_orb = opt.optimize(Strategy001ORB, n_trials=20)
    if best_orb:
        save_optimized_parameters("RELIANCE.NS", "S001_ORB", best_orb)
        
    print("Optimizing S002_VWAP...")
    best_vwap = opt.optimize(Strategy002VWAP, n_trials=20)
    if best_vwap:
        save_optimized_parameters("RELIANCE.NS", "S002_VWAP", best_vwap)
        
    print("Optimization Complete.")

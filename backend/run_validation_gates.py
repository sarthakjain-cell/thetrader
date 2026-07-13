import pandas as pd
from walk_forward import load_data, run_strategy_backtest
from logger import log

from strategy_001_orb import Strategy001ORB
from strategy_003_momentum import Strategy003Momentum
from strategy_004_meanreversion import Strategy004MeanReversion
from strategy_005_rangefade import Strategy005RangeFade

def run_gates():
    df = load_data()
    if df.empty:
        print("No historical data found.")
        return
        
    last_date = df['Datetime'].max()
    df_60d = df[df['Datetime'] >= last_date - pd.Timedelta(days=60)]
    
    strategies = [
        Strategy001ORB(),
        Strategy003Momentum(),
        Strategy004MeanReversion(),
        Strategy005RangeFade()
    ]
    
    print("\n" + "="*50)
    print("WALK-FORWARD VALIDATION GATES")
    print("Criteria: Profit Factor > 1.5")
    print("="*50)
    
    for strategy in strategies:
        res = run_strategy_backtest(df_60d, strategy)
        pf = res["profit_factor"]
        
        status = "PASS" if pf > 1.5 and res["total_trades"] > 0 else "FAIL"
        
        print(f"\n{strategy.strategy_id} ({strategy.name})")
        print(f"Total Trades : {res['total_trades']}")
        print(f"Win Rate     : {res['win_rate']*100:.1f}%")
        print(f"Net Profit   : ${res['net_profit']:.2f}")
        print(f"Profit Factor: {pf:.2f}  ---> [{status}]")
        
if __name__ == "__main__":
    run_gates()

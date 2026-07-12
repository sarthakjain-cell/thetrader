import os
import sys
import numpy as np
import pandas as pd
import lightgbm as lgb
import optuna
from sklearn.model_selection import TimeSeriesSplit
from model_trainer import fetch_historical_data, generate_features_and_labels, GLOBAL_FEATURE_COLS, get_db

def run_weekend_optimization():
    print("========== STARTING OPTUNA WEEKEND RETRAIN ==========")
    df_raw = fetch_historical_data()
    if df_raw.empty:
        print("No historical data found. Exiting.")
        sys.exit(1)
        
    print("Generating vectorized features...")
    df_full = df_raw.groupby('Symbol', group_keys=False).apply(generate_features_and_labels)
    df_full = df_full.sort_values('Datetime').reset_index(drop=True)
    
    X = df_full[GLOBAL_FEATURE_COLS]
    y = df_full['Label']
    
    n_neg = len(y[y == 0])
    n_pos = len(y[y == 1])
    spw = n_neg / n_pos if n_pos > 0 else 1.0
    print(f"Class imbalance scale_pos_weight: {spw:.2f}")
    
    def objective(trial):
        params = {
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
            'num_leaves': trial.suggest_int('num_leaves', 15, 63),
            'min_child_samples': trial.suggest_int('min_child_samples', 20, 100),
            'scale_pos_weight': spw,
            'verbose': -1,
            'random_state': 42
        }
        
        tscv = TimeSeriesSplit(n_splits=3)
        pfs = []
        
        for train_idx, val_idx in tscv.split(X):
            X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
            X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]
            
            model = lgb.LGBMClassifier(**params)
            model.fit(X_train, y_train)
            probs = model.predict_proba(X_val)[:, 1]
            
            trades = probs > 0.55
            if trades.sum() == 0:
                pfs.append(1.0)
                continue
                
            wins = y_val[trades].sum()
            losses = trades.sum() - wins
            
            gross_profit = wins * 2.0
            gross_loss = losses * 1.0
            pf = gross_profit / gross_loss if gross_loss > 0 else 0
            pfs.append(pf)
            
        return np.mean(pfs)

    print("Starting Optuna Trial optimization...")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=30)
    
    best_params = study.best_params
    best_params['scale_pos_weight'] = spw
    best_params['verbose'] = -1
    print(f"Best Params Found: {best_params} (Best PF: {study.best_value:.2f})")
    
    print("Training completely fresh model across full history using optimal params...")
    final_model = lgb.train(
        best_params, 
        lgb.Dataset(X, label=y), 
        num_boost_round=200
    )
    
    model_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model_latest.txt')
    final_model.save_model(model_file)
    print("Weekend Retrain Complete. Model securely overwritten and ready for Monday incremental updates.")

if __name__ == "__main__":
    run_weekend_optimization()

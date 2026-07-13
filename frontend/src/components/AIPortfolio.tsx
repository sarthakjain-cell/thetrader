import React from 'react';
import styles from './AIPortfolio.module.css';
import { StrategyPerformance } from '../types';

interface Position {
  symbol: string;
  qty: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  strategy_id?: string;
}

interface AIPortfolioProps {
  positions: Position[];
  account: any;
  strategies?: StrategyPerformance[];
}

export const AIPortfolio: React.FC<AIPortfolioProps> = ({ positions, account, strategies = [] }) => {
  const totalPnl = positions.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0);
  const isPositive = totalPnl >= 0;

  return (
    <div className={styles.portfolioContainer}>
      <div className={styles.header}>
        <div className={styles.title}>Multi-Strategy AI Matrix</div>
        <div className={styles.totalPnl}>
          <span className={styles.pnlLabel}>Live Float Returns</span>
          <span className={`${styles.pnlValue} ${isPositive ? styles.positive : styles.negative}`}>
            {isPositive ? '+' : ''}₹{totalPnl.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Strategies Leaderboard */}
      <div className={styles.sectionTitle}>Active AI Engines ({strategies.length})</div>
      <div className={styles.strategyList}>
        {strategies.length === 0 ? (
          <div className={styles.emptyState}>Booting AI Engines...</div>
        ) : (
          strategies.map((strat) => (
            <div key={strat.strategy_id} className={styles.strategyCard}>
              <div className={styles.stratHeader}>
                <div className={styles.stratName}>
                  <span className={styles.activeDot}></span>
                  {strat.name}
                </div>
                <div className={`${styles.stratPnl} ${strat.net_pnl >= 0 ? styles.positive : styles.negative}`}>
                  {strat.net_pnl >= 0 ? '+' : ''}₹{strat.net_pnl.toFixed(2)}
                </div>
              </div>
              <div className={styles.stratStats}>
                <div className={styles.statBox}>
                  <div className={styles.statVal}>{strat.total_trades}</div>
                  <div className={styles.statLabel}>Trades</div>
                </div>
                <div className={styles.statBox}>
                  <div className={styles.statVal}>{(strat.win_rate * 100).toFixed(1)}%</div>
                  <div className={styles.statLabel}>Win Rate</div>
                </div>
                <div className={styles.statBox}>
                  <div className={styles.statVal}>{strat.profit_factor.toFixed(2)}</div>
                  <div className={styles.statLabel}>Profit Factor</div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <div className={styles.sectionTitle}>Live Paper Positions</div>
      <div className={styles.listContainer}>
        {positions.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.boxIcon}>📦</div>
            <div className={styles.emptyTitle}>No Positions Active</div>
            <div className={styles.emptyDesc}>The AI is waiting for the perfect entry.</div>
          </div>
        ) : (
          positions.map(p => {
            const pnlPositive = (p.unrealized_pnl || 0) >= 0;
            const pnlColorClass = pnlPositive ? styles.positive : styles.negative;
            const pnlArrow = pnlPositive ? '↑' : '↓';

            return (
              <div key={p.symbol} className={styles.row}>
                <div className={styles.leftCol}>
                  <div className={styles.symbol}>{p.symbol.split('.')[0]}</div>
                  <div className={styles.qtyInfo}>
                    {p.qty} Qty • Avg ₹{p.entry_price.toFixed(2)}
                    {p.strategy_id && <span className={styles.stratTag}>{p.strategy_id}</span>}
                  </div>
                </div>
                <div className={styles.rightCol}>
                  <div className={styles.ltp}>₹{p.current_price.toFixed(2)}</div>
                  <div className={`${styles.change} ${pnlColorClass}`}>
                    {pnlArrow} ₹{Math.abs(p.unrealized_pnl || 0).toFixed(2)}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};


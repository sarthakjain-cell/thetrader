import React from 'react';
import styles from './AIPortfolio.module.css';

interface Position {
  symbol: string;
  qty: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
}

interface AIPortfolioProps {
  positions: Position[];
  account: any;
}

export const AIPortfolio: React.FC<AIPortfolioProps> = ({ positions, account }) => {
  const totalPnl = positions.reduce((sum, p) => sum + p.unrealized_pnl, 0);
  const isPositive = totalPnl >= 0;

  return (
    <div className={styles.portfolioContainer}>
      {positions.length > 0 && (
        <div className={styles.header}>
          <div className={styles.title}>My Portfolio</div>
          <div className={styles.totalPnl}>
            <span className={styles.pnlLabel}>Total Returns</span>
            <span className={`${styles.pnlValue} ${isPositive ? styles.positive : styles.negative}`}>
              {isPositive ? '+' : ''}₹{totalPnl.toFixed(2)}
            </span>
          </div>
        </div>
      )}

      <div className={styles.listContainer}>
        {positions.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.boxIcon}>📦</div>
            <div className={styles.emptyTitle}>No Positions Active</div>
            <div className={styles.emptyDesc}>The AI is waiting for the perfect entry.</div>
          </div>
        ) : (
          positions.map(p => {
            const pnlPositive = p.unrealized_pnl >= 0;
            const pnlColorClass = pnlPositive ? styles.positive : styles.negative;
            const pnlArrow = pnlPositive ? '↑' : '↓';

            return (
              <div key={p.symbol} className={styles.row}>
                <div className={styles.leftCol}>
                  <div className={styles.symbol}>{p.symbol.split('.')[0]}</div>
                  <div className={styles.qtyInfo}>
                    {p.qty} Qty • Avg ₹{p.entry_price.toFixed(2)}
                  </div>
                </div>
                <div className={styles.rightCol}>
                  <div className={styles.ltp}>₹{p.current_price.toFixed(2)}</div>
                  <div className={`${styles.change} ${pnlColorClass}`}>
                    {pnlArrow} ₹{Math.abs(p.unrealized_pnl).toFixed(2)}
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

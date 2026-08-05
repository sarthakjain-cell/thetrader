import React from 'react';
import { motion } from 'framer-motion';
import { Settings } from 'lucide-react';
import styles from './AIPortfolio.module.css';
import { StrategyPerformance } from '../types';

interface StrategiesLeaderboardProps {
  strategies: StrategyPerformance[];
}

export const StrategiesLeaderboard: React.FC<StrategiesLeaderboardProps> = ({ strategies }) => {
  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };
  
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div style={{ marginTop: '24px' }}>
      <div className={styles.sectionTitle}>Active AI Engines ({strategies.length})</div>
      <motion.div variants={containerVariants} initial="hidden" animate="show" className={styles.strategyList}>
        {strategies.length === 0 ? (
          <motion.div variants={itemVariants} className={styles.emptyState}>
            <Settings size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
            <div className={styles.emptyTitle}>Booting AI Engines...</div>
            <div className={styles.emptyDesc}>The genetic algorithm is synthesizing strategies for today's market conditions.</div>
          </motion.div>
        ) : (
          strategies.map((strat) => (
            <motion.div variants={itemVariants} key={strat.strategy_id} className={styles.strategyCard}>
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
            </motion.div>
          ))
        )}
      </motion.div>
    </div>
  );
};

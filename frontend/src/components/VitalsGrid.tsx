import React from 'react';
import { AccountInfo } from '../types';
import styles from './VitalsGrid.module.css';
import CountingNumber from './CountingNumber';
import { motion } from 'framer-motion';
import GlassPanel from './GlassPanel';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 100, damping: 15 } }
};

interface Props {
  account: AccountInfo | null;
}

export const VitalsGrid: React.FC<Props> = ({ account }) => {
  if (!account) return <div className={styles.grid}>Loading Vitals...</div>;

  const mddPercent = (account.current_drawdown * 100).toFixed(2);
  const pnl = account.daily_pnl || 0;
  const isPositive = pnl >= 0;

  return (
    <motion.div className={styles.grid} variants={containerVariants} initial="hidden" animate="visible">
      <motion.div variants={itemVariants}>
        <GlassPanel as="article">
        <h3 className={styles.label}>Account Equity</h3>
        <div className={styles.value}>
          ₹<CountingNumber 
            value={account.equity} 
            format={(val) => val.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} 
          />
        </div>
      </GlassPanel>
      </motion.div>

      <motion.div variants={itemVariants}>
      <GlassPanel as="article">
        <h3 className={styles.label}>Daily P&L</h3>
        <div className={`${styles.value} ${isPositive ? 'value-up' : 'value-down'}`}>
          {isPositive ? '+' : ''}₹<CountingNumber 
            value={pnl} 
            format={(val) => val.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} 
          />
        </div>
      </GlassPanel>
      </motion.div>
      
      <motion.div variants={itemVariants}>
      <GlassPanel as="article">
        <h3 className={styles.label}>Current Drawdown</h3>
        <div className={styles.value} style={{ color: account.current_drawdown > 0 ? 'var(--accent-negative)' : 'var(--text-primary)' }}>
          {mddPercent}%
        </div>
        <div className={styles.subtext}>Limit: {(account.max_drawdown_limit * 100).toFixed(1)}%</div>
      </GlassPanel>
      </motion.div>
    </motion.div>
  );
};

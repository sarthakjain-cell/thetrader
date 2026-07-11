import React from 'react';
import styles from './KillBanner.module.css';

interface Props {
  isTriggered: boolean;
}

export const KillBanner: React.FC<Props> = ({ isTriggered }) => {
  if (!isTriggered) return null;

  return (
    <div className={styles.banner} role="alert" aria-live="assertive">
      <strong>SYSTEM HALTED</strong>
      <span>Maximum Drawdown Limit Exceeded. All positions liquidated.</span>
    </div>
  );
};

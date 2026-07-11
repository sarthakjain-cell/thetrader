import React from 'react';
import { ConnectionStatus } from '../types';
import styles from './StatusIndicator.module.css';

interface Props {
  status: ConnectionStatus;
  lastUpdated: number | null;
}

export const StatusIndicator: React.FC<Props> = ({ status, lastUpdated }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'CONNECTED': return 'var(--accent-positive)';
      case 'RECONNECTING': return 'var(--accent-neutral)';
      case 'ERROR':
      case 'CLOSED': return 'var(--accent-negative)';
      default: return 'var(--text-muted)';
    }
  };

  const isStale = lastUpdated && (Date.now() - lastUpdated > 10000);

  return (
    <div className={styles.container}>
      <div 
        className={`${styles.dot} ${status === 'CONNECTED' ? styles.pulse : ''}`} 
        style={{ backgroundColor: getStatusColor() }} 
      />
      <span className={styles.text}>
        {status === 'CONNECTED' && isStale ? 'STALE DATA' : status}
      </span>
    </div>
  );
};

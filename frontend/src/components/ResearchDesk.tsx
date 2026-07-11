import React from 'react';
import { ResearchTip } from '../types';
import styles from './ResearchDesk.module.css';

interface Props {
  tips: ResearchTip[];
}

export const ResearchDesk: React.FC<Props> = ({ tips }) => {
  return (
    <div className={styles.container}>
      <h2 className={styles.header}>Research Desk (Engine B)</h2>
      
      {tips.length === 0 ? (
        <div className={styles.empty}>No tips generated yet today.</div>
      ) : (
        <div className={styles.tipsList}>
          {tips.map((tip, idx) => (
            <article key={idx} className={styles.card}>
              <div className="flex-between" style={{ marginBottom: 'var(--space-2)' }}>
                <strong style={{ fontSize: 'var(--text-lg)' }}>{tip.symbol}</strong>
                <span className={`${styles.badge} ${styles[tip.confidence.toLowerCase()]}`}>
                  {tip.confidence}
                </span>
              </div>
              
              <div className={styles.rationale}>
                {tip.rationale}
              </div>
              
              <div className={styles.scoreContainer}>
                <div className={styles.scoreHeader}>
                  <span>Conviction Score</span>
                  <strong>{tip.score.toFixed(2)}</strong>
                </div>
                <div className={styles.progressBar}>
                  <div 
                    className={styles.progressFill} 
                    style={{ 
                      width: `${Math.min(100, Math.max(0, tip.score * 100))}%`,
                      backgroundColor: tip.confidence === 'High' ? 'var(--accent-positive)' : 
                                       tip.confidence === 'Medium' ? 'var(--accent-neutral)' : 'var(--accent-negative)'
                    }} 
                  />
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};

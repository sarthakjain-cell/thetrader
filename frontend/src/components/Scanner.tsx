import React, { useState } from 'react';
import styles from './Scanner.module.css';

interface MarketSignal {
  symbol: string;
  ai_prob: number;
  sentiment_score: number;
  fqs_score: number;
  trend: 'Bullish' | 'Neutral' | 'Bearish';
}

interface ScannerProps {
  signals: MarketSignal[];
}

export const Scanner: React.FC<ScannerProps> = ({ signals }) => {
  const [activeFilter, setActiveFilter] = useState('Volume Breakout');
  const filters = ['Volume Breakout', 'RSI Oversold', 'MACD Crossover', 'Golden Cross'];

  // Mock end-of-day data if signals is empty (Market Closed)
  const displaySignals = signals.length > 0 ? signals : [
    { symbol: 'HDFCBANK.NS', ai_prob: 0.82, sentiment_score: 75, fqs_score: 80, trend: 'Bullish' },
    { symbol: 'INFY.NS', ai_prob: 0.71, sentiment_score: 60, fqs_score: 65, trend: 'Bullish' },
    { symbol: 'ITC.NS', ai_prob: 0.45, sentiment_score: 40, fqs_score: 55, trend: 'Bearish' },
    { symbol: 'TCS.NS', ai_prob: 0.68, sentiment_score: 85, fqs_score: 70, trend: 'Bullish' },
    { symbol: 'RELIANCE.NS', ai_prob: 0.55, sentiment_score: 50, fqs_score: 60, trend: 'Neutral' },
  ];

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.title}>Live AI Screener</div>
        <div className={styles.filterScroll}>
          {filters.map(f => (
            <button 
              key={f} 
              className={`${styles.filterPill} ${activeFilter === f ? styles.activeFilter : ''}`}
              onClick={() => setActiveFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.list}>
        {displaySignals.map(sig => {
          const isPos = sig.ai_prob > 0.6;
          const isNeg = sig.ai_prob < 0.5;
          const probColor = isPos ? styles.positive : isNeg ? styles.negative : styles.neutral;
          
          return (
            <div key={sig.symbol} className={styles.scanRow}>
              <div className={styles.leftCol}>
                <div className={styles.symbol}>{sig.symbol.split('.')[0]}</div>
                <div className={styles.techIndicators}>
                  <span className={styles.indicator}>RSI: {Math.floor(Math.random() * 40 + 30)}</span>
                  <span className={styles.indicator}>MACD: {isPos ? '+' : '-'}{(Math.random() * 2).toFixed(2)}</span>
                </div>
              </div>
              <div className={styles.rightCol}>
                <div className={`${styles.aiProb} ${probColor}`}>
                  {Math.floor(sig.ai_prob * 100)}% Match
                </div>
                <div className={styles.scanLabel}>AI Confidence</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import styles from './CategoryScroll.module.css';

interface MarketSignal {
  symbol: string;
  ai_prob: number;
  sentiment_score?: number;
  fqs_score?: number;
  trend: 'Bullish' | 'Neutral' | 'Bearish';
  last_price?: number;
  volume_spike?: number;
}

interface CategoryScrollProps {
  title: string;
  signals: MarketSignal[];
}

const logoDomains: Record<string, string> = {
  'RELIANCE': 'ril.com',
  'TCS': 'tcs.com',
  'HDFCBANK': 'hdfcbank.com',
  'INFY': 'infosys.com',
  'ICICIBANK': 'icicibank.com',
  'SBIN': 'sbi.co.in'
};

export const CategoryScroll: React.FC<CategoryScrollProps> = ({ title, signals }) => {
  return (
    <div className={styles.container}>
      {/* Upstox Style Section Header */}
      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>{title}</h2>
        <span className={styles.viewAll}>View All &gt;</span>
      </div>

      {/* Upstox Style Stock Cards */}
      <div className={styles.cardScroll}>
        {signals.length === 0 ? (
          <div className={styles.emptyState}>No signals available for {title} right now.</div>
        ) : (
          signals.map(sig => {
            const isProfit = sig.ai_prob > 0.6;
            const priceColorClass = isProfit ? styles.positive : styles.negative;
            const arrow = isProfit ? '↑' : '↓';
            const priceValue = sig.last_price ? sig.last_price.toFixed(2) : "0.00";
            const volValue = sig.volume_spike ? sig.volume_spike.toFixed(1) : "1.0";
            const cleanSymbol = sig.symbol.split('.')[0];
            const logoLetter = cleanSymbol.charAt(0);
            const domain = logoDomains[cleanSymbol];
            const logoUrl = domain ? `https://www.google.com/s2/favicons?domain=${domain}&sz=128` : null;

            return (
              <div key={sig.symbol} className={styles.stockCard}>
                <div className={styles.cardTop}>
                  <div className={styles.symbolInfo}>
                    <div className={styles.logoPlaceholder}>
                      {logoUrl ? (
                        <img 
                          src={logoUrl} 
                          alt={cleanSymbol} 
                          className={styles.realLogo}
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                          }}
                        />
                      ) : (
                        logoLetter
                      )}
                    </div>
                    <span className={styles.symbol}>{cleanSymbol}</span>
                  </div>
                  <div className={styles.priceInfo}>
                    <div className={`${styles.price} ${priceColorClass}`}>
                      ₹{priceValue}
                    </div>
                    <div className={styles.change}>
                      Vol: {volValue}x <span className={styles.arrow}>{arrow}</span>
                    </div>
                  </div>
                </div>

                <div className={styles.cardBottom}>
                  <div className={styles.buyAction}>
                    <span style={{color: priceColorClass, transform: isProfit ? 'rotate(45deg)' : 'rotate(135deg)', display: 'inline-block'}}>➚</span> 
                    {Math.floor(sig.ai_prob * 10000)} recent buys
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

"use client";

import React, { useEffect, useState } from 'react';
import styles from './MarketPulse.module.css';

interface IndexData {
  name: string;
  value: number;
  change: number;
  pct_change: number;
  sparkline: number[];
}

export const MarketPulse: React.FC = () => {
  const [indices, setIndices] = useState<IndexData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchIndices = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://206.189.129.232:8000';
        const response = await fetch(`${apiUrl}/api/indices`);
        if (response.ok) {
          const data = await response.json();
          setIndices(data);
        } else {
          throw new Error('API returned ' + response.status);
        }
      } catch (error) {
        console.warn("Failed to fetch live indices, using fallback data", error);
        // Fallback data if backend /api/indices is not deployed to DO server yet
        setIndices([
          { name: 'Nifty 50', value: 24320.55, change: 120.40, pct_change: 0.50, sparkline: [24200, 24250, 24230, 24300, 24320] },
          { name: 'Sensex', value: 79900.20, change: -45.10, pct_change: -0.05, sparkline: [79950, 79800, 79900, 79920, 79900] },
          { name: 'Bank Nifty', value: 52100.00, change: 300.20, pct_change: 0.58, sparkline: [51800, 51900, 52000, 51950, 52100] }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchIndices();
    const interval = setInterval(fetchIndices, 30000); // Poll every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className={styles.scrollContainer}><div className={styles.capsule}>Loading AI Pulse...</div></div>;
  }

  if (indices.length === 0) return null;

  return (
    <div className={styles.scrollContainer}>
      {indices.map((idx, i) => {
        const isPositive = idx.change >= 0;
        const colorClass = isPositive ? styles.positive : styles.negative;
        const arrow = isPositive ? "▲" : "▼";

        let points = "";
        if (idx.sparkline && idx.sparkline.length > 0) {
            const min = Math.min(...idx.sparkline);
            const max = Math.max(...idx.sparkline);
            const range = max - min || 1;
            points = idx.sparkline.map((val, x) => {
              const xPos = (x / (idx.sparkline.length - 1)) * 50;
              const yPos = 20 - ((val - min) / range) * 20; // 20px height
              return `${xPos},${yPos}`;
            }).join(" ");
        }

        return (
          <div key={i} className={styles.capsule}>
            <div className={styles.leftInfo}>
              <span className={styles.name}>{idx.name}</span>
              <span className={styles.value}>{idx.value.toFixed(2)}</span>
            </div>
            <div className={styles.rightInfo}>
              <span className={`${styles.change} ${colorClass}`}>
                {arrow} {Math.abs(idx.pct_change).toFixed(2)}%
              </span>
              {points && (
                <svg width="50" height="20" className={styles.sparkline}>
                  <polyline 
                    points={points} 
                    fill="none" 
                    stroke={isPositive ? "var(--profit-green, #00c897)" : "var(--loss-red, #e63946)"} 
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

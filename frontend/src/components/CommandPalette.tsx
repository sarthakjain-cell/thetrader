"use client";

import React, { useState, useEffect } from 'react';
import styles from './CommandPalette.module.css';

export const CommandPalette: React.FC = () => {
  const [query, setQuery] = useState('');
  const [placeholderIndex, setPlaceholderIndex] = useState(0);

  const placeholders = [
    "Search for stocks...",
    "Search for mutual funds...",
    "Find momentum breakouts...",
    "Scan top AI targets..."
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholderIndex((prev) => (prev + 1) % placeholders.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className={styles.container}>
      <div className={styles.searchBar}>
        <span className={styles.icon}>🔍</span>
        
        {query === '' && (
          <div className={styles.placeholderWrapper}>
            <span key={placeholderIndex} className={styles.animatedText}>
              {placeholders[placeholderIndex]}
            </span>
          </div>
        )}

        <input 
          type="text" 
          className={styles.input}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {query && <span className={styles.aiBadge}>AI Processing...</span>}
      </div>
    </div>
  );
};

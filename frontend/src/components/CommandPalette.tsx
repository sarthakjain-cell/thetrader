"use client";

import React, { useState } from 'react';
import styles from './CommandPalette.module.css';

export const CommandPalette: React.FC = () => {
  const [query, setQuery] = useState('');

  return (
    <div className={styles.container}>
      <div className={styles.searchBar}>
        <span className={styles.icon}>🔍</span>
        <input 
          type="text" 
          className={styles.input}
          placeholder="Ask AlgoTrade... (e.g., 'Should I buy Reliance?', 'Show me oil stocks')"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {query && <span className={styles.aiBadge}>AI Processing...</span>}
      </div>
    </div>
  );
};

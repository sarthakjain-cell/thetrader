"use client";

import React, { useState, useEffect, useRef } from 'react';
import styles from './CommandPalette.module.css';
import { POPULAR_STOCKS } from '../utils/stockDictionary';

interface CommandPaletteProps {
  onSearch?: (symbol: string) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ onSearch }) => {
  const [query, setQuery] = useState('');
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const placeholders = [
    "Search for stocks...",
    "Search for mutual funds...",
    "Find momentum breakouts...",
    "Scan top AI targets..."
  ];

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredStocks = query 
    ? POPULAR_STOCKS.filter(s => 
        s.symbol.toLowerCase().includes(query.toLowerCase()) || 
        s.name.toLowerCase().includes(query.toLowerCase())
      ).slice(0, 6)
    : [];

  const handleSelect = (symbol: string) => {
    setQuery('');
    setShowResults(false);
    if (onSearch) onSearch(symbol);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && query.trim() !== '') {
      // If exact match or top result exists
      if (filteredStocks.length > 0) {
        handleSelect(filteredStocks[0].symbol);
      } else {
        // Allow arbitrary raw symbols (e.g. "SUZLON")
        handleSelect(query.toUpperCase() + (query.toUpperCase().endsWith('.NS') ? '' : '.NS'));
      }
    }
  };

  return (
    <div className={styles.container} ref={wrapperRef}>
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
          onChange={(e) => {
            setQuery(e.target.value);
            setShowResults(true);
          }}
          onFocus={() => setShowResults(true)}
          onKeyDown={handleKeyDown}
        />
        {query && <span className={styles.aiBadge}>Press Enter ↵</span>}
      </div>

      {showResults && query && (
        <div className={styles.resultsDropdown}>
          {filteredStocks.length > 0 ? (
            filteredStocks.map((stock) => (
              <div 
                key={stock.symbol} 
                className={styles.resultItem}
                onClick={() => handleSelect(stock.symbol)}
              >
                <div className={styles.resultSymbol}>{stock.symbol.split('.')[0]}</div>
                <div className={styles.resultName}>{stock.name}</div>
              </div>
            ))
          ) : (
            <div 
              className={styles.resultItem}
              onClick={() => handleSelect(query.toUpperCase() + (query.toUpperCase().endsWith('.NS') ? '' : '.NS'))}
            >
              <div className={styles.resultSymbol}>Search NSE for "{query.toUpperCase()}"</div>
              <div className={styles.resultName}>Press Enter to scan</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

import React, { memo, useEffect, useState, useRef } from 'react';
import { Trade } from '../types';
import RippleButton from './RippleButton';
import GlassPanel from './GlassPanel';

interface Props {
  trades: Trade[];
  onTradeClick?: (trade: Trade) => void;
}

const TradeRow = memo(({ 
  t, 
  onClick, 
  isNew,
  index
}: { 
  t: Trade, 
  onClick?: () => void,
  isNew: boolean,
  index: number
}) => {
  const pnlColor = t.pnl >= 0 ? 'text-positive' : 'text-negative';
  
  // Staggered delay for rows that enter at the same time
  const animationStyle = isNew ? {
    animation: `row-enter 400ms ease-out ${index * 50}ms both, ${t.pnl >= 0 ? 'highlight-green' : 'highlight-red'} 1000ms ease-out ${index * 50}ms both`
  } : {};

  return (
    <tr onClick={onClick} style={{ cursor: onClick ? 'pointer' : 'default', ...animationStyle }} className="clickable-row">
      <td><strong>{t.symbol}</strong></td>
      <td>{t.entry_time.split(' ')[1] || t.entry_time}</td>
      <td>{t.exit_time.split(' ')[1] || t.exit_time}</td>
      <td>₹{t.entry_price.toFixed(2)}</td>
      <td>₹{t.exit_price.toFixed(2)}</td>
      <td className={pnlColor}>
        <strong>{t.pnl >= 0 ? '+' : ''}₹{t.pnl.toFixed(2)}</strong>
      </td>
    </tr>
  );
});

export const TradesTable: React.FC<Props> = ({ trades, onTradeClick }) => {
  const [recentIds, setRecentIds] = useState<Set<string>>(new Set());
  const prevTradesRef = useRef<Trade[]>([]);

  useEffect(() => {
    // Only track new trades if we already had some trades loaded (avoid animating on initial mount)
    if (prevTradesRef.current.length > 0 && trades.length > prevTradesRef.current.length) {
      const newIds = new Set<string>();
      
      // Assume new trades are appended or prepended. We'll just find trades not in prev.
      // For performance in huge arrays, we check length diff and slice if they are appended.
      // A simple symbol+time string is our unique ID.
      const prevIdSet = new Set(prevTradesRef.current.map(t => `${t.symbol}-${t.entry_time}`));
      
      trades.forEach((t) => {
        const id = `${t.symbol}-${t.entry_time}`;
        if (!prevIdSet.has(id)) {
          newIds.add(id);
        }
      });
      
      if (newIds.size > 0) {
        setRecentIds(newIds);
        // Clean up animation state after it finishes (1500ms max)
        setTimeout(() => setRecentIds(new Set()), 1500);
      }
    }
    prevTradesRef.current = trades;
  }, [trades]);
  const downloadCSV = () => {
    if (trades.length === 0) return;
    const headers = "Symbol,Entry Time,Exit Time,Entry Price,Exit Price,P&L\n";
    const rows = trades.map(t => 
      `${t.symbol},${t.entry_time},${t.exit_time},${t.entry_price},${t.exit_price},${t.pnl}`
    ).join("\n");
    const blob = new Blob([headers + rows], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trades_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <GlassPanel style={{ overflow: 'hidden', marginBottom: 'var(--space-6)' }}>
      <div className="flex-between" style={{ padding: 'var(--space-4)', borderBottom: '1px solid var(--panel-border)' }}>
        <h3>Today's Trades</h3>
        <RippleButton 
          onClick={downloadCSV}
          style={{
            background: 'var(--accent-info)', color: 'white', border: 'none', 
            padding: '4px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: 'var(--text-xs)'
          }}>
          Export CSV
        </RippleButton>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Entry Time</th>
              <th>Exit Time</th>
              <th>Entry Price</th>
              <th>Exit Price</th>
              <th>Realized P&L</th>
            </tr>
          </thead>
          <tbody>
            {trades.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No completed trades today</td>
              </tr>
            ) : (
              trades.map((t, i) => (
                <TradeRow 
                  key={`${t.symbol}-${t.entry_time}`} 
                  t={t} 
                  index={i}
                  isNew={recentIds.has(`${t.symbol}-${t.entry_time}`)}
                  onClick={() => onTradeClick && onTradeClick(t)} 
                />
              ))
            )}
          </tbody>
        </table>
      </div>
    </GlassPanel>
  );
};

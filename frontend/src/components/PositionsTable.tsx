import React, { memo } from 'react';
import { Position } from '../types';
import GlassPanel from './GlassPanel';

interface Props {
  positions: Position[];
}

const PositionRow = memo(({ pos }: { pos: Position }) => {
  const pnlColor = pos.unrealized_pnl >= 0 ? 'text-positive' : 'text-negative';
  return (
    <tr>
      <td><strong>{pos.symbol}</strong></td>
      <td>{pos.quantity}</td>
      <td>₹{pos.entry_price.toFixed(2)}</td>
      <td>₹{pos.current_price.toFixed(2)}</td>
      <td className={pnlColor}>
        <strong>{pos.unrealized_pnl >= 0 ? '+' : ''}₹{pos.unrealized_pnl.toFixed(2)}</strong>
      </td>
    </tr>
  );
}, (prev, next) => {
  return prev.pos.current_price === next.pos.current_price && prev.pos.quantity === next.pos.quantity;
});

export const PositionsTable: React.FC<Props> = ({ positions }) => {
  return (
    <GlassPanel style={{ overflow: 'hidden', marginBottom: 'var(--space-6)' }}>
      <h3 style={{ padding: 'var(--space-4)', borderBottom: '1px solid var(--panel-border)' }}>Open Positions</h3>
      <div style={{ overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Qty</th>
              <th>Entry Price</th>
              <th>Current Price</th>
              <th>Unrealized P&L</th>
            </tr>
          </thead>
          <tbody>
            {positions.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No open positions</td>
              </tr>
            ) : (
              positions.map((p, i) => <PositionRow key={`${p.symbol}-${i}`} pos={p} />)
            )}
          </tbody>
        </table>
      </div>
    </GlassPanel>
  );
};

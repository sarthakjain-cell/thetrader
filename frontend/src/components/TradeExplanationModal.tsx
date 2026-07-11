import React from 'react';


interface Trade {
  id: number;
  symbol: string;
  entry_time: string;
  exit_time: string;
  entry_price: number;
  exit_price: number;
  qty: number;
  pnl: number;
  reason: string;
  notes?: string;
}

interface Props {
  trade: Trade | null;
  onClose: () => void;
}

export default function TradeExplanationModal({ trade, onClose }: Props) {
  if (!trade) return null;

  const isWin = trade.pnl >= 0;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: 'var(--space-4)',
      animation: 'fadeIn 0.2s ease-out'
    }} onClick={onClose}>
      <div style={{
        background: 'var(--panel-bg)',
        border: '1px solid var(--panel-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-6)',
        maxWidth: '500px',
        width: '100%',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        position: 'relative'
      }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px' }}>
          <h2 style={{ fontSize: 'var(--text-xl)', margin: 0 }}>Trade Intelligence: {trade.symbol}</h2>
          <button 
            style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.5rem' }} 
            onClick={onClose}
          >
            &times;
          </button>
        </div>
        
        <div>
          <div style={{ color: isWin ? 'var(--neon-green)' : 'var(--neon-red)', marginBottom: '1rem', fontWeight: 'bold', fontSize: '1.2rem' }}>
            Outcome: {isWin ? 'PROFIT' : 'LOSS'} of ₹{Math.abs(trade.pnl).toFixed(2)}
          </div>
          
          <p style={{ marginBottom: '1rem', color: 'var(--text-muted)' }}>
            <strong>Execution:</strong> Bought {trade.qty} shares at ₹{trade.entry_price.toFixed(2)}, exited at ₹{trade.exit_price.toFixed(2)}.
          </p>
          
          <div style={{ marginTop: '1.5rem' }}>
            <h3 style={{ fontSize: 'var(--text-lg)', marginBottom: '0.5rem', color: 'var(--accent-primary)' }}>Bot's Reasoning</h3>
            <div style={{
              background: 'rgba(255, 255, 255, 0.03)',
              padding: '1rem',
              borderRadius: 'var(--radius-md)',
              borderLeft: '3px solid var(--neon-blue)',
              lineHeight: '1.5',
              fontFamily: 'monospace',
              fontSize: '0.9rem'
            }}>
              {trade.notes || "Standard execution parameters met. No specific macro notes recorded."}
            </div>
          </div>
          
          <div style={{ marginTop: '1.5rem' }}>
            <h3 style={{ fontSize: 'var(--text-lg)', marginBottom: '0.5rem', color: 'var(--accent-primary)' }}>Exit Trigger</h3>
            <p style={{ textTransform: 'capitalize', color: 'var(--text-muted)' }}>
              {trade.reason.replace('_', ' ')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

import React from 'react';

interface InfoModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeTab: 'dashboard' | 'charts' | 'news';
}

export const InfoModal: React.FC<InfoModalProps> = ({ isOpen, onClose, activeTab }) => {
  if (!isOpen) return null;

  const getContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <>
            <h3 style={{ marginTop: 0, color: 'var(--accent-primary)' }}>📊 Dashboard</h3>
            <p><strong>Account Vitals:</strong> Displays your total equity, daily P&L, win rate, and maximum drawdown limits.</p>
            <p><strong>Open Positions:</strong> Shows all active trades currently held by the technical engine. You can monitor the entry price, current price, and unrealized profit/loss here.</p>
          </>
        );
      case 'charts':
        return (
          <>
            <h3 style={{ marginTop: 0, color: 'var(--accent-primary)' }}>📈 Charts</h3>
            <p><strong>Trading Chart:</strong> A real-time candlestick chart of the currently active stock. It automatically overlays green (buy) and red (sell) markers indicating where the algorithm executed trades today.</p>
            <p><strong>Equity Curve:</strong> Tracks the overall growth (or drawdown) of your account balance over time, allowing you to visually monitor algorithmic performance.</p>
          </>
        );
      case 'news':
        return (
          <>
            <h3 style={{ marginTop: 0, color: 'var(--accent-primary)' }}>📰 News & AI</h3>
            <p><strong>Trades Table:</strong> A historical log of every trade executed today, including the exact entry/exit times, prices, and net profit.</p>
            <p><strong>AI Research Desk:</strong> Displays live market sentiment. The AI (Engine B) reads financial news, generates a conviction score, and recommends high-probability stock movements based on real-time headlines.</p>
          </>
        );
    }
  };

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
    }}>
      <div style={{
        background: 'var(--panel-bg)',
        border: '1px solid var(--panel-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-6)',
        maxWidth: '400px',
        width: '100%',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        position: 'relative'
      }}>
        <button 
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: '1.25rem'
          }}
        >
          ✕
        </button>
        {getContent()}
      </div>
    </div>
  );
};

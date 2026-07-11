import React, { useState } from 'react';
import { useAlerts } from '../contexts/AlertContext';

export const AlertLog: React.FC = () => {
  const { alerts, clearAlerts } = useAlerts();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div style={{ position: 'relative' }}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        style={{
          background: 'var(--panel-bg)',
          border: '1px solid var(--panel-border)',
          color: 'var(--text-primary)',
          padding: 'var(--space-2) var(--space-4)',
          borderRadius: 'var(--radius-md)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-2)'
        }}
      >
        <span>🔔</span> Alerts
        {alerts.length > 0 && (
          <span style={{ 
            background: 'var(--accent-negative)', 
            color: 'white', 
            borderRadius: '50%', 
            padding: '2px 6px', 
            fontSize: '0.6rem',
            fontWeight: 'bold' 
          }}>
            {alerts.length}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="glass-panel" style={{
          position: 'absolute',
          top: '100%',
          right: 0,
          marginTop: 'var(--space-2)',
          width: '350px',
          maxHeight: '400px',
          overflowY: 'auto',
          zIndex: 50,
          boxShadow: 'var(--shadow-md)',
        }}>
          <div className="flex-between" style={{ padding: 'var(--space-3)', borderBottom: '1px solid var(--panel-border)' }}>
            <h4 style={{ margin: 0 }}>Notification Log</h4>
            <button onClick={clearAlerts} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>Clear</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {alerts.length === 0 ? (
              <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>No recent alerts</div>
            ) : (
              alerts.map((a, i) => (
                <div key={i} style={{ 
                  padding: 'var(--space-3)', 
                  borderBottom: '1px solid rgba(255,255,255,0.05)',
                  borderLeft: `3px solid ${a.type === 'critical' ? 'var(--accent-negative)' : 'var(--accent-info)'}`,
                  fontSize: 'var(--text-sm)'
                }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginBottom: '4px' }}>
                    {new Date(a.timestamp).toLocaleTimeString()}
                  </div>
                  {a.message}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

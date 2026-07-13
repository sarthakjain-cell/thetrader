import React, { useState } from 'react';
import { useAlerts } from '../contexts/AlertContext';
import { motion, AnimatePresence } from 'framer-motion';

export const AlertLog: React.FC = () => {
  const { alerts, clearAlerts } = useAlerts();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        style={{
          background: isOpen ? 'rgba(255,255,255,0.1)' : 'transparent',
          border: '1px solid rgba(255,255,255,0.05)',
          color: 'var(--text-primary)',
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.2s',
          position: 'relative'
        }}
      >
        <span style={{ fontSize: '1.2rem' }}>🔔</span>
        {alerts.length > 0 && (
          <span style={{ 
            position: 'absolute',
            top: '-2px',
            right: '-2px',
            background: 'var(--accent-negative)', 
            color: 'white', 
            borderRadius: '50%', 
            width: '18px',
            height: '18px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.65rem',
            fontWeight: 'bold',
            boxShadow: '0 0 10px rgba(255,51,102,0.5)'
          }}>
            {alerts.length > 9 ? '9+' : alerts.length}
          </span>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              style={{
                position: 'fixed',
                inset: 0,
                background: 'rgba(0, 0, 0, 0.4)',
                backdropFilter: 'blur(4px)',
                zIndex: 9998,
                cursor: 'pointer'
              }}
            />
            <motion.div 
              initial={{ x: '100%', opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: '100%', opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              style={{
                position: 'fixed',
                top: 0,
                right: 0,
                height: '100vh',
                width: '100%',
                maxWidth: '400px',
                background: 'rgba(15, 15, 20, 0.98)',
                borderLeft: '1px solid rgba(255, 255, 255, 0.08)',
                boxShadow: '-8px 0 32px rgba(0, 0, 0, 0.5)',
                zIndex: 9999,
                display: 'flex',
                flexDirection: 'column',
                paddingTop: '48px' /* Avoid Android status bar/notch */
              }}
            >
              <div style={{ 
                padding: '16px 24px', 
                borderBottom: '1px solid rgba(255, 255, 255, 0.08)', 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600 }}>Notifications</h3>
                  {alerts.length > 0 && (
                    <span style={{ background: 'var(--accent-negative)', padding: '2px 8px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 'bold' }}>
                      {alerts.length} New
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '16px' }}>
                  <button onClick={clearAlerts} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.85rem' }}>
                    Clear All
                  </button>
                  <button onClick={() => setIsOpen(false)} style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '1.2rem' }}>
                    ✕
                  </button>
                </div>
              </div>

              <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
                {alerts.length === 0 ? (
                  <div style={{ 
                    height: '100%', 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    color: 'rgba(255,255,255,0.3)'
                  }}>
                    <span style={{ fontSize: '3rem', marginBottom: '16px' }}>📭</span>
                    <p style={{ margin: 0, fontSize: '1.1rem' }}>No new notifications</p>
                    <p style={{ margin: '8px 0 0 0', fontSize: '0.85rem', textAlign: 'center' }}>
                      When the AI executes a trade, it will appear here.
                    </p>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {alerts.map((a, i) => (
                      <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                        key={i} 
                        style={{ 
                          background: 'rgba(255,255,255,0.02)',
                          padding: '16px', 
                          borderRadius: '12px',
                          border: '1px solid rgba(255,255,255,0.05)',
                          borderLeft: `4px solid ${a.type === 'critical' ? 'var(--accent-negative)' : 'var(--accent-info)'}`,
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                          <span style={{ 
                            fontSize: '0.75rem', 
                            fontWeight: 'bold',
                            color: a.type === 'critical' ? 'var(--accent-negative)' : 'var(--accent-info)',
                            textTransform: 'uppercase',
                            letterSpacing: '1px'
                          }}>
                            {a.type === 'critical' ? 'Alert' : 'Info'}
                          </span>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                            {new Date(a.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.95rem', lineHeight: '1.4', color: 'rgba(255,255,255,0.9)' }}>
                          {a.message}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};

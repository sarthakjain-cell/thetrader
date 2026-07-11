import React from 'react';
import { DashboardState } from '../types';
import GlassPanel from './GlassPanel';
import { motion } from 'framer-motion';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1, transition: { type: 'spring', stiffness: 200, damping: 20 } }
};

interface Props {
  state: DashboardState;
}

export default function ScannerTab({ state }: Props) {
  const isClosed = state.market_status === 'CLOSED';

  if (!isClosed && (!state.market_signals || state.market_signals.length === 0)) {
    return (
      <div style={{ padding: 'var(--space-6)', textAlign: 'center', color: 'var(--text-muted)' }}>
        Waiting for initial market scan...
      </div>
    );
  }

  if (isClosed) {
    return (
      <div style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        {/* Pre-Market Intelligence Card */}
        {state.pre_market_intelligence && state.pre_market_intelligence.length > 0 && (
          <div>
            <h2 style={{ marginBottom: 'var(--space-4)', fontSize: 'var(--text-xl)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              🌅 Pre-Market Briefing
            </h2>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: 'var(--space-4)'
            }}>
              {state.pre_market_intelligence.map(intel => (
                <GlassPanel key={intel.symbol} style={{ padding: 'var(--space-3)' }}>
                  <div className="flex-between" style={{ marginBottom: '8px' }}>
                    <strong>{intel.symbol.replace('.NS', '')}</strong>
                    <span style={{ fontSize: '10px', padding: '2px 6px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px' }}>
                      52w Prox: {intel.proximity_52w}
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                    S: {intel.support?.toFixed(1) || 'N/A'} | R: {intel.resistance?.toFixed(1) || 'N/A'}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Pattern: <span style={{ color: intel.pattern !== 'None' ? 'var(--neon-green)' : 'inherit' }}>{intel.pattern}</span>
                  </div>
                </GlassPanel>
              ))}
            </div>
          </div>
        )}

        {/* Night Terminal */}
        <div>
          <h2 style={{ marginBottom: 'var(--space-4)', fontSize: 'var(--text-xl)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="pulse-glow" style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--neon-blue)', display: 'inline-block' }}></span>
            Night Mode / Training Terminal
          </h2>
          <GlassPanel style={{ 
            padding: 'var(--space-4)', 
            background: '#0a0a0c', 
            fontFamily: 'monospace',
            height: '300px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column-reverse' // Auto-scroll to bottom by reversing
          }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {state.after_hours_research && state.after_hours_research.length > 0 ? (
                state.after_hours_research.map((log) => {
                  const timeStr = log.timestamp.split(' ')[1];
                  let color = 'var(--text-muted)';
                  if (log.confidence === 'High') color = 'var(--neon-green)';
                  if (log.confidence === 'Low') color = 'var(--neon-red)';
                  
                  return (
                    <div key={log.id} style={{ fontSize: '13px', lineHeight: '1.4', animation: 'fadeIn 0.5s ease-out' }}>
                      <span style={{ color: 'var(--text-muted)' }}>[{timeStr}]</span>{' '}
                      <strong style={{ color: '#fff' }}>{log.symbol.replace('.NS', '')}</strong>:{' '}
                      <span style={{ color }}>{log.finding}</span>
                    </div>
                  );
                })
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                  &gt; Initializing after-hours research engine...<br/>
                  &gt; Awaiting data...
                </div>
              )}
            </div>
          </GlassPanel>
        </div>
      </div>
    );
  }

  // Map symbols to tiles (Market Open)
  return (
    <div style={{ padding: 'var(--space-4)' }}>
      <h2 style={{ marginBottom: 'var(--space-4)', fontSize: 'var(--text-xl)' }}>Live Bot Brain</h2>
      <motion.div variants={containerVariants} initial="hidden" animate="visible" style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
        gap: 'var(--space-4)'
      }}>
        {state.market_signals.map((sig) => {
          let bgColor = 'var(--bg-surface)';
          let pulseClass = '';
          let isHighConviction = sig.ai_prob !== undefined && sig.ai_prob > 0.55;
          
          if (sig.signal === 'BUY') {
            pulseClass = isHighConviction ? 'pulse-platinum' : '';
          } 

          return (
            <motion.div key={sig.symbol} variants={itemVariants} style={{ height: '100%' }}>
            <GlassPanel style={{ 
                padding: 'var(--space-3)', 
                background: bgColor,
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-2)',
                height: '100%',
                animation: pulseClass ? 'pulse-platinum 2s infinite ease-in-out' : 'none'
            }}>
              <div className="flex-between">
                <strong style={{ fontSize: 'var(--text-md)' }}>{sig.symbol.replace('.NS', '')}</strong>
                <span style={{ fontSize: 'var(--text-xs)', color: sig.sentiment >= 0 ? 'var(--neon-green)' : 'var(--neon-red)' }}>
                  {sig.sentiment > 0 ? '+' : ''}{sig.sentiment.toFixed(2)}
                </span>
              </div>
              
              <div className="flex-between">
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Price</span>
                <span style={{ fontSize: 'var(--text-sm)', fontWeight: 'bold' }}>{sig.last_price.toFixed(1)}</span>
              </div>
              
              <div className="flex-between">
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>Action</span>
                <span style={{ 
                  fontSize: 'var(--text-xs)', 
                  fontWeight: 'bold',
                  color: sig.signal === 'BUY' ? 'var(--gold)' : (sig.signal === 'VETO' ? 'var(--loss)' : 'var(--text-muted)')
                }}>
                  {sig.signal}
                </span>
              </div>
              
              <div style={{ marginTop: 'auto', paddingTop: '4px', borderTop: '1px solid var(--panel-border)', fontSize: '10px', color: 'var(--text-muted)' }}>
                RSI: {sig.rsi.toFixed(0)} | Vol: {sig.volume_spike.toFixed(1)}x
              </div>
              {sig.ai_prob !== undefined && sig.ai_prob !== null && (
                <div style={{ paddingTop: '6px', fontSize: '10px' }}>
                  <div className="flex-between" style={{ color: 'var(--platinum)', marginBottom: '4px' }}>
                    <span>AI Conviction</span>
                    <strong>{(sig.ai_prob * 100).toFixed(0)}%</strong>
                  </div>
                  <div style={{ height: '4px', width: '100%', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${sig.ai_prob * 100}%` }}
                      transition={{ duration: 1, ease: "easeOut" }}
                      style={{ height: '100%', background: 'var(--info)' }}
                    />
                  </div>
                </div>
              )}
            </GlassPanel>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}

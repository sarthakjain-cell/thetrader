import React from 'react';

export const EventsTab: React.FC = () => {
  return (
    <div style={{ padding: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div style={{ fontSize: '1.2rem', color: '#8b949e', fontWeight: 600 }}>2026</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fff', fontSize: '0.9rem', cursor: 'pointer' }}>
          <span>=</span> Filters
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        
        {/* EVENT 1 */}
        <div style={{ display: 'flex', gap: '16px' }}>
          <div style={{ 
            width: '48px', 
            height: '48px', 
            border: '1px solid rgba(255,255,255,0.1)', 
            borderRadius: '8px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(255,255,255,0.02)'
          }}>
            <div style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>27</div>
            <div style={{ fontSize: '0.75rem', color: '#8b949e' }}>May</div>
          </div>
          <div style={{ flex: 1, borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '16px' }}>
            <div style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '4px' }}>Annual Result</div>
            <div style={{ fontSize: '0.85rem', color: '#8b949e' }}>Release date</div>
          </div>
        </div>

        {/* EVENT 2 */}
        <div style={{ display: 'flex', gap: '16px' }}>
          <div style={{ 
            width: '48px', 
            height: '48px', 
            border: '1px solid rgba(255,255,255,0.1)', 
            borderRadius: '8px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(255,255,255,0.02)'
          }}>
            <div style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>27</div>
            <div style={{ fontSize: '0.75rem', color: '#8b949e' }}>Jan</div>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '4px' }}>Quarterly Result</div>
            <div style={{ fontSize: '0.85rem', color: '#8b949e' }}>Release date</div>
          </div>
        </div>

      </div>

      <div style={{ marginTop: '24px', color: '#00c853', fontWeight: 600, fontSize: '0.9rem', cursor: 'pointer' }}>
        View More
      </div>

      {/* PROMO CARD */}
      <div style={{ 
        marginTop: '32px',
        padding: '16px',
        borderRadius: '12px',
        border: '1px solid rgba(255,255,255,0.05)',
        background: 'rgba(255,255,255,0.02)',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        cursor: 'pointer'
      }}>
        <div style={{ fontSize: '2rem' }}>📅</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.85rem', color: '#8b949e', marginBottom: '4px' }}>Events calendar</div>
          <div style={{ fontSize: '0.95rem', fontWeight: 600 }}>View upcoming events in other stocks</div>
        </div>
        <div style={{ color: '#8b949e' }}>&gt;</div>
      </div>

    </div>
  );
};

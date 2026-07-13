import React from 'react';

interface TechnicalsTabProps {
  trend: string;
}

export const TechnicalsTab: React.FC<TechnicalsTabProps> = ({ trend }) => {
  const isBullish = trend === 'Bullish' || trend === 'Strong Buy';
  
  // Create gradient segments for the meter
  const segments = Array.from({ length: 30 }).map((_, i) => {
    // Colors from Red -> Gray -> Green
    let color = '';
    if (i < 10) color = `rgba(255, 51, 102, ${1 - (i/15)})`; // Red fading out
    else if (i < 20) color = `rgba(139, 148, 158, 0.5)`; // Neutral gray
    else color = `rgba(0, 200, 83, ${(i-15)/15})`; // Green fading in
    
    return color;
  });

  // Calculate pointer position based on trend
  const pointerIndex = isBullish ? 25 : (trend === 'Neutral' ? 15 : 5);

  return (
    <div style={{ padding: '16px' }}>
      {/* METER SECTION */}
      <div style={{ 
        background: 'rgba(255,255,255,0.02)', 
        borderRadius: '12px', 
        padding: '24px 16px',
        border: '1px solid rgba(255,255,255,0.05)',
        marginBottom: '24px'
      }}>
        <div style={{ fontSize: '0.9rem', color: '#8b949e', marginBottom: '8px' }}>
          Based on technicals, this stock is
        </div>
        <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: isBullish ? '#00c853' : '#ff3366', marginBottom: '24px' }}>
          {trend}
        </div>

        {/* Gradient Bars */}
        <div style={{ position: 'relative', height: '40px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', gap: '4px', height: '24px' }}>
            {segments.map((color, i) => (
              <div key={i} style={{ flex: 1, background: color, borderRadius: '2px' }} />
            ))}
          </div>
          {/* Pointer Triangle */}
          <div style={{
            position: 'absolute',
            bottom: '0px',
            left: `${(pointerIndex / 30) * 100}%`,
            transform: 'translateX(-50%)',
            width: 0, 
            height: 0, 
            borderLeft: '6px solid transparent',
            borderRight: '6px solid transparent',
            borderBottom: '8px solid #fff'
          }} />
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.85rem', color: '#8b949e' }}>Bearish</span>
            <span style={{ fontWeight: 600 }}>2</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ fontSize: '0.85rem', color: '#8b949e' }}>Neutral</span>
            <span style={{ fontWeight: 600 }}>2</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
            <span style={{ fontSize: '0.85rem', color: '#8b949e' }}>Bullish</span>
            <span style={{ fontWeight: 600, color: '#00c853' }}>9</span>
          </div>
        </div>
      </div>

      {/* INDICATORS TABLE */}
      <h3 style={{ fontSize: '1.1rem', marginBottom: '16px', fontWeight: 600 }}>Indicators ⓘ</h3>
      <div style={{ 
        background: 'rgba(255,255,255,0.02)', 
        borderRadius: '12px', 
        border: '1px solid rgba(255,255,255,0.05)',
        marginBottom: '24px'
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1.5fr', padding: '16px', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '0.75rem', color: '#8b949e', letterSpacing: '1px', textTransform: 'uppercase' }}>
          <div>Indicator</div>
          <div>Value</div>
          <div>Verdict</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1.5fr', padding: '16px', borderBottom: '1px solid rgba(255,255,255,0.05)', alignItems: 'center' }}>
          <div style={{ fontSize: '0.9rem' }}>RSI (14)</div>
          <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>+61.05</div>
          <div style={{ fontSize: '0.9rem', color: '#8b949e' }}>Neutral</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1.5fr', padding: '16px', borderBottom: '1px solid rgba(255,255,255,0.05)', alignItems: 'center' }}>
          <div style={{ fontSize: '0.9rem' }}>MACD (12,26,9)</div>
          <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>+0.10</div>
          <div style={{ fontSize: '0.9rem', color: '#00c853' }}>Bullish</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1.5fr', padding: '16px', alignItems: 'center' }}>
          <div style={{ fontSize: '0.9rem' }}>Beta</div>
          <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>+1.32</div>
          <div style={{ fontSize: '0.9rem', color: '#8b949e' }}>Highly volatile</div>
        </div>
      </div>

      {/* SUPPORT & RESISTANCE */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '1.1rem', margin: 0, fontWeight: 600 }}>Support and Resistance ⓘ</h3>
        <span style={{ color: '#8b949e', transform: 'rotate(180deg)', display: 'inline-block' }}>^</span>
      </div>
    </div>
  );
};

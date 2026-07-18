import React, { useState, useEffect } from 'react';

interface OverviewTabProps {
  symbol: string;
  onLoaded?: (fundamentals: any) => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({ symbol, onLoaded }) => {
  const [expanded, setExpanded] = useState(false);
  const [financialPeriod, setFinancialPeriod] = useState<'Quarterly'|'Yearly'>('Quarterly');
  
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  const cleanSymbol = symbol.split('.')[0];
  const [shareholdingTab, setShareholdingTab] = useState('Current');

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        setLoading(true);
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://206.189.129.232:8000';
        const res = await fetch(`${baseUrl}/api/insights/${symbol}`);
        if (res.ok) {
          const json = await res.json();
          setData(json);
          if (onLoaded && json.fundamentals) {
            onLoaded(json.fundamentals);
          }
        }
      } catch (e) {
        console.error("Failed to fetch insights", e);
      } finally {
        setLoading(false);
      }
    };
    fetchInsights();
  }, [symbol]);

  const similarStocks = [
    { name: 'TCS', price: 3845.20, change: '+1.2%' },
    { name: 'INFY', price: 1450.80, change: '-0.5%' },
    { name: 'WIPRO', price: 460.10, change: '+2.1%' },
    { name: 'HCLTECH', price: 1320.50, change: '+0.8%' }
  ];

  if (loading || !data) {
    return <div style={{ padding: '32px', textAlign: 'center', color: '#8b949e' }}>Loading Fundamental Data...</div>;
  }

  const { fundamentals, financials, shareholding } = data;

  // Format large numbers
  const formatNum = (num: number) => {
    if (!num) return '-';
    if (num >= 1e11) return `₹${(num / 1e7).toFixed(0)}Cr`;
    if (num >= 1e7) return `₹${(num / 1e7).toFixed(2)}Cr`;
    if (num >= 1e5) return `₹${(num / 1e5).toFixed(2)}L`;
    return num.toLocaleString();
  };

  // Safe getter
  const getF = (key: string, suffix: string = '') => fundamentals[key] ? `${fundamentals[key]}${suffix}` : '-';

  return (
    <div style={{ padding: '16px' }}>
      
      {/* ---------------- PERFORMANCE ---------------- */}
      <h3 style={{ fontSize: '1.1rem', marginBottom: '16px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
        Performance <span style={{ color: '#8b949e', fontSize: '0.9rem' }}>ⓘ</span>
      </h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', marginBottom: '32px' }}>
        {/* Today Range */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#8b949e', marginBottom: '8px' }}>
            <span>Today's Low</span>
            <span>Today's High</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.95rem', fontWeight: 600, marginBottom: '8px' }}>
            <span>{fundamentals.todays_low || '-'}</span>
            <span>{fundamentals.todays_high || '-'}</span>
          </div>
          <div style={{ height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', position: 'relative' }}>
            {fundamentals.todays_high > fundamentals.todays_low && (
              <div style={{
                position: 'absolute', top: '100%', 
                left: `${Math.min(100, Math.max(0, ((fundamentals.prev_close - fundamentals.todays_low) / (fundamentals.todays_high - fundamentals.todays_low)) * 100))}%`, 
                transform: 'translateX(-50%)',
                width: 0, height: 0, borderLeft: '6px solid transparent', borderRight: '6px solid transparent', borderBottom: '8px solid #fff', marginTop: '4px'
              }} />
            )}
          </div>
        </div>

        {/* 52 Week Range */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#8b949e', marginBottom: '8px' }}>
            <span>52 Week Low</span>
            <span>52 Week High</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.95rem', fontWeight: 600, marginBottom: '8px' }}>
            <span>{fundamentals["52_week_low"] || '-'}</span>
            <span>{fundamentals["52_week_high"] || '-'}</span>
          </div>
          <div style={{ height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', position: 'relative' }}>
            {fundamentals["52_week_high"] > fundamentals["52_week_low"] && (
              <div style={{
                position: 'absolute', top: '100%', 
                left: `${Math.min(100, Math.max(0, ((fundamentals.prev_close - fundamentals["52_week_low"]) / (fundamentals["52_week_high"] - fundamentals["52_week_low"])) * 100))}%`, 
                transform: 'translateX(-50%)',
                width: 0, height: 0, borderLeft: '6px solid transparent', borderRight: '6px solid transparent', borderBottom: '8px solid #fff', marginTop: '4px'
              }} />
            )}
          </div>
        </div>

        {/* Key Pricing metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#8b949e', marginBottom: '4px' }}>Open</div>
            <div style={{ fontSize: '0.95rem', fontWeight: 600 }}>{getF('open')}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#8b949e', marginBottom: '4px' }}>Prev. Close</div>
            <div style={{ fontSize: '0.95rem', fontWeight: 600 }}>{getF('prev_close')}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#8b949e', marginBottom: '4px' }}>Volume</div>
            <div style={{ fontSize: '0.95rem', fontWeight: 600 }}>{formatNum(fundamentals.volume).replace('₹', '')}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#8b949e', marginBottom: '4px' }}>Lower circuit</div>
            <div style={{ fontSize: '0.95rem', fontWeight: 600 }}>{(fundamentals.prev_close * 0.8).toFixed(2)}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#8b949e', marginBottom: '4px' }}>Upper circuit</div>
            <div style={{ fontSize: '0.95rem', fontWeight: 600 }}>{(fundamentals.prev_close * 1.2).toFixed(2)}</div>
          </div>
        </div>
      </div>


      {/* ---------------- FUNDAMENTALS ---------------- */}
      <h3 style={{ fontSize: '1.1rem', marginBottom: '16px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
        Fundamentals <span style={{ color: '#8b949e', fontSize: '0.9rem' }}>ⓘ</span>
      </h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px 24px', marginBottom: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#8b949e', fontSize: '0.9rem' }}>Mkt Cap</span>
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{formatNum(fundamentals.mkt_cap)}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#8b949e', fontSize: '0.9rem' }}>ROE</span>
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{fundamentals.roe ? `${(fundamentals.roe * 100).toFixed(2)}%` : '-'}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#8b949e', fontSize: '0.9rem' }}>P/E Ratio(TTM)</span>
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{fundamentals.pe_ratio ? fundamentals.pe_ratio.toFixed(2) : '-'}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#8b949e', fontSize: '0.9rem' }}>EPS(TTM)</span>
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{getF('eps')}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#8b949e', fontSize: '0.9rem' }}>P/B Ratio</span>
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{fundamentals.pb_ratio ? fundamentals.pb_ratio.toFixed(2) : '-'}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#8b949e', fontSize: '0.9rem' }}>Div Yield</span>
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{fundamentals.div_yield ? `${(fundamentals.div_yield * 100).toFixed(2)}%` : '0.00%'}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#8b949e', fontSize: '0.9rem' }}>Industry P/E</span>
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{fundamentals.industry_pe || '-'}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#8b949e', fontSize: '0.9rem' }}>Book Value</span>
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{fundamentals.book_value ? fundamentals.book_value.toFixed(2) : '-'}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#8b949e', fontSize: '0.9rem' }}>Debt to Equity</span>
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{fundamentals.debt_to_equity ? fundamentals.debt_to_equity.toFixed(2) : '-'}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#8b949e', fontSize: '0.9rem' }}>Face Value</span>
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{getF('face_value')}</span>
        </div>
      </div>

      
      {/* ---------------- FINANCIAL PERFORMANCE ---------------- */}
      <h3 style={{ fontSize: '1.1rem', marginBottom: '16px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
        Financial performance
      </h3>
      
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
        <button 
          onClick={() => setFinancialPeriod('Quarterly')}
          style={{ 
            background: financialPeriod === 'Quarterly' ? 'transparent' : 'rgba(255,255,255,0.05)', 
            border: financialPeriod === 'Quarterly' ? '1px solid #fff' : '1px solid transparent', 
            color: '#fff', borderRadius: '16px', padding: '6px 16px', fontSize: '0.85rem', cursor: 'pointer'
          }}
        >
          Quarterly
        </button>
      </div>

      {financials && financials.length > 0 ? (
        <>
          <div style={{ marginBottom: '16px', fontSize: '0.8rem', color: '#8b949e', fontWeight: 'bold' }}>{financials[financials.length-1].label}</div>
          
          <div style={{ display: 'flex', gap: '32px', marginBottom: '24px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: '#8b949e', letterSpacing: '1px' }}>
                <span style={{ width: '8px', height: '8px', background: '#6e7681', borderRadius: '2px' }} /> REVENUE
              </div>
              <div style={{ fontSize: '1.1rem', fontWeight: 'bold', marginTop: '4px' }}>
                {formatNum(financials[financials.length-1].rev)}
              </div>
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: '#8b949e', letterSpacing: '1px' }}>
                <span style={{ width: '8px', height: '8px', background: '#00c853', borderRadius: '2px' }} /> PROFIT
              </div>
              <div style={{ fontSize: '1.1rem', fontWeight: 'bold', marginTop: '4px' }}>
                {formatNum(financials[financials.length-1].prof)}
              </div>
            </div>
          </div>

          {/* Bar Chart (CSS-based) */}
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', height: '180px', borderBottom: '1px dashed rgba(255,255,255,0.1)', marginBottom: '12px', paddingBottom: '0px', position: 'relative' }}>
            
            {/* Y Axis Lines */}
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, borderTop: '1px dashed rgba(255,255,255,0.1)', zIndex: 0 }} />
            <div style={{ position: 'absolute', top: '50%', left: 0, right: 0, borderTop: '1px dashed rgba(255,255,255,0.1)', zIndex: 0 }} />
            
            {/* Bars */}
            {financials.map((d: any, i: number) => {
              const maxVal = Math.max(...financials.map((f:any) => f.rev));
              const revPct = maxVal > 0 ? (d.rev / maxVal) * 100 : 0;
              const profPct = maxVal > 0 ? (Math.max(0, d.prof) / maxVal) * 100 : 0;
              const active = i === financials.length - 1;
              return (
                <div key={i} style={{ display: 'flex', gap: '2px', alignItems: 'flex-end', height: '100%', zIndex: 2, paddingBottom: '1px' }}>
                  <div style={{ width: '12px', height: `${revPct}%`, background: active ? '#8b949e' : '#484f58', borderRadius: '2px 2px 0 0' }} />
                  <div style={{ width: '12px', height: `${profPct}%`, background: '#00c853', borderRadius: '2px 2px 0 0' }} />
                </div>
              );
            })}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#8b949e', marginBottom: '32px' }}>
            {financials.map((f: any, i: number) => (
              <span key={i} style={i === financials.length - 1 ? { fontWeight: 'bold', color: '#fff' } : {}}>{f.label.split('-')[1] + '/' + f.label.split('-')[0].slice(2)}</span>
            ))}
          </div>
        </>
      ) : (
        <div style={{ color: '#8b949e', fontSize: '0.9rem', marginBottom: '32px' }}>Financial statements not available for this stock.</div>
      )}

      
      {/* ---------------- SHAREHOLDING PATTERN ---------------- */}
      <h3 style={{ fontSize: '1.1rem', marginBottom: '16px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
        Shareholding pattern
      </h3>
      
      <div style={{ display: 'flex', gap: '12px', overflowX: 'auto', marginBottom: '24px', scrollbarWidth: 'none', paddingBottom: '4px' }}>
        {['Current'].map(tab => (
          <div 
            key={tab}
            onClick={() => setShareholdingTab(tab)}
            style={{
              padding: '6px 16px',
              borderRadius: '20px',
              border: shareholdingTab === tab ? '1px solid #fff' : '1px solid rgba(255,255,255,0.2)',
              color: shareholdingTab === tab ? '#fff' : '#c9d1d9',
              fontSize: '0.85rem',
              cursor: 'pointer',
              whiteSpace: 'nowrap'
            }}
          >
            {tab}
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', marginBottom: '32px' }}>
        {[
          { label: 'Promoters', val: shareholding.Promoters },
          { label: 'Institutions (DII/FII)', val: shareholding.Institutions },
          { label: 'Retail & Others', val: shareholding.Retail }
        ].map(item => (
          <div key={item.label} style={{ display: 'grid', gridTemplateColumns: '150px 1fr 60px', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontSize: '0.9rem', color: '#c9d1d9' }}>{item.label}</span>
            <div style={{ height: '8px', background: 'transparent', borderRadius: '4px' }}>
              <div style={{ height: '100%', width: `${item.val}%`, background: '#00c853', borderRadius: '4px' }} />
            </div>
            <span style={{ fontSize: '0.9rem', fontWeight: 600, textAlign: 'right' }}>{item.val}%</span>
          </div>
        ))}
      </div>


      {/* ---------------- ABOUT COMPANY ---------------- */}
      <h3 style={{ fontSize: '1.1rem', marginBottom: '16px', fontWeight: 600 }}>About company</h3>
      <div style={{ marginBottom: '32px' }}>
        <p style={{ 
          fontSize: '0.9rem', 
          lineHeight: '1.6', 
          color: '#c9d1d9',
          display: '-webkit-box',
          WebkitLineClamp: expanded ? 'unset' : 4,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
          margin: 0
        }}>
          {fundamentals.about || `${cleanSymbol} is a major publicly listed company.`}
        </p>
        <button 
          onClick={() => setExpanded(!expanded)}
          style={{ 
            background: 'transparent', border: 'none', 
            color: '#fff', fontWeight: 600, 
            padding: '8px 0', marginTop: '8px', 
            cursor: 'pointer', fontSize: '0.9rem'
          }}
        >
          {expanded ? 'Read less' : 'Read more'}
        </button>
      </div>

      {/* ---------------- SIMILAR STOCKS ---------------- */}
      <h3 style={{ fontSize: '1.1rem', marginBottom: '16px', fontWeight: 600 }}>Similar stocks</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingBottom: '32px' }}>
        {similarStocks.map((s, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ 
                width: '32px', height: '32px', 
                borderRadius: '6px', 
                background: 'rgba(255,255,255,0.1)', 
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 'bold', fontSize: '0.8rem'
              }}>
                {s.name[0]}
              </div>
              <span style={{ fontSize: '0.95rem' }}>{s.name}</span>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.95rem', fontWeight: 500 }}>₹{s.price.toFixed(2)}</div>
              <div style={{ fontSize: '0.8rem', color: s.change.startsWith('+') ? '#00c853' : '#ff3366' }}>
                {s.change}
              </div>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};

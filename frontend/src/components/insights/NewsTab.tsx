import React, { useEffect, useState } from 'react';

interface NewsItem {
  id: number;
  timestamp: string;
  source: string;
  headline: string;
  content: string;
  affected_sector: string;
  action_signal: string;
  confidence_score: number;
}

interface NewsTabProps {
  symbol: string;
}

export const NewsTab: React.FC<NewsTabProps> = ({ symbol }) => {
  const cleanSymbol = symbol.split('.')[0];
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/news?category=${cleanSymbol}`);
        const data = await res.json();
        setNews(data);
      } catch (err) {
        console.error("Failed to fetch news", err);
      } finally {
        setLoading(false);
      }
    };
    fetchNews();
  }, [cleanSymbol]);

  const getSignalColor = (signal: string) => {
    if (signal?.includes('BUY')) return '#2ea043';
    if (signal?.includes('SELL')) return '#f85149';
    return '#8b949e';
  };

  const getSignalBg = (signal: string) => {
    if (signal?.includes('BUY')) return 'rgba(46,160,67,0.1)';
    if (signal?.includes('SELL')) return 'rgba(248,81,73,0.1)';
    return 'rgba(139,148,158,0.1)';
  };

  return (
    <div style={{ padding: '0 16px', maxHeight: '500px', overflowY: 'auto' }}>
      <div style={{ 
        padding: '16px 0', 
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ fontSize: '0.9rem', color: '#c9d1d9', fontWeight: 500 }}>
          AI-Enriched Contextual News for {cleanSymbol}
        </div>
        <div style={{ fontSize: '0.75rem', color: '#8b949e', background: 'rgba(255,255,255,0.05)', padding: '4px 8px', borderRadius: '12px' }}>
          Powered by FinBERT
        </div>
      </div>

      {loading ? (
        <div style={{ padding: '32px', textAlign: 'center', color: '#8b949e' }}>Loading AI News...</div>
      ) : news.length === 0 ? (
        <div style={{ padding: '32px', textAlign: 'center', color: '#8b949e' }}>No recent news found for {cleanSymbol}.</div>
      ) : (
        news.map((item, i) => (
          <div key={i} style={{ 
            padding: '16px 0', 
            borderBottom: '1px solid rgba(255,255,255,0.05)',
            transition: 'background 0.2s',
          }}>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.8rem', color: '#8b949e', fontWeight: 500 }}>{item.source}</span>
              <span style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#8b949e' }} />
              <span style={{ fontSize: '0.8rem', color: '#8b949e' }}>
                {new Date(item.timestamp).toLocaleDateString()} {new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
              </span>
              
              {/* Badges */}
              <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
                <span style={{ 
                  fontSize: '0.75rem', 
                  color: '#a5d6ff', 
                  background: 'rgba(56,139,253,0.1)', 
                  border: '1px solid rgba(56,139,253,0.4)',
                  padding: '2px 8px', 
                  borderRadius: '12px',
                  fontWeight: 500
                }}>
                  {item.affected_sector || "General Market"}
                </span>
                
                <span style={{ 
                  fontSize: '0.75rem', 
                  color: getSignalColor(item.action_signal), 
                  background: getSignalBg(item.action_signal), 
                  border: \`1px solid \${getSignalColor(item.action_signal)}40\`,
                  padding: '2px 8px', 
                  borderRadius: '12px',
                  fontWeight: 600,
                  boxShadow: item.action_signal?.includes('BUY') || item.action_signal?.includes('SELL') ? \`0 0 8px \${getSignalBg(item.action_signal)}\` : 'none'
                }}>
                  AI Tip: {item.action_signal || "⚪ HOLD"}
                </span>
              </div>
            </div>
            
            <div style={{ fontSize: '0.95rem', color: '#e6edf3', lineHeight: '1.5', fontWeight: 500, marginBottom: '6px' }}>
              {item.headline}
            </div>
            
            {item.content && item.content.length > 5 && item.content !== item.headline && (
              <div style={{ fontSize: '0.85rem', color: '#8b949e', lineHeight: '1.5', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {item.content}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
};

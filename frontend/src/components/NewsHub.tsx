import React, { useState, useEffect } from 'react';
import styles from './NewsHub.module.css';

export interface NewsItem {
  id: number;
  headline: string;
  source: string;
  timestamp: string;
  related_tickers: string;
  sentiment_label: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
  content: string;
  affected_sector: string;
  action_signal: string;
}

export const NewsHub: React.FC = () => {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://206.189.129.232:8000';
        const res = await fetch(`${baseUrl}/api/news?limit=20`);
        const data = await res.json();
        if (Array.isArray(data)) {
          setNews(data);
        }
      } catch (err) {
        console.error("Failed to fetch news", err);
      } finally {
        setLoading(false);
      }
    };
    fetchNews();
  }, []);

  const getTimeAgo = (ts: string) => {
    try {
      // The DB returns 'YYYY-MM-DD HH:MM:SS' in local IST. Convert to standard ISO for Safari/iOS
      const dateStr = ts.replace(' ', 'T');
      const diff = new Date().getTime() - new Date(dateStr).getTime();
      
      if (diff < 0) return 'Just now';

      const hours = Math.floor(diff / (1000 * 60 * 60));
      if (hours < 1) {
        const mins = Math.floor(diff / (1000 * 60));
        return `${mins || 1} mins ago`;
      }
      if (hours < 24) return `${hours} hrs ago`;
      return `${Math.floor(hours / 24)} days ago`;
    } catch {
      return ts.split('T')[0] || ts.split(' ')[0];
    }
  };

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
    <div className={styles.container}>
      <div className={styles.header}>AI-Enriched Market News</div>
      <div className={styles.newsList}>
        {loading ? (
          <div className={styles.emptyState}>Loading live news...</div>
        ) : news.length === 0 ? (
          <div className={styles.emptyState}>No recent news found.</div>
        ) : (
          news.map(item => {
            return (
              <div 
                key={item.id} 
                className={`${styles.newsCard} ${expandedId === item.id ? styles.expandedCard : ''}`}
                onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
              >
                <div className={styles.topRow}>
                  <span className={styles.source}>{item.source || 'AI Scraper'}</span>
                  <span className={styles.time}>{getTimeAgo(item.timestamp)}</span>
                </div>
                
                {/* Sector and AI Badges */}
                <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
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
                    border: `1px solid ${getSignalColor(item.action_signal)}40`,
                    padding: '2px 8px', 
                    borderRadius: '12px',
                    fontWeight: 600,
                    boxShadow: item.action_signal?.includes('BUY') || item.action_signal?.includes('SELL') ? `0 0 8px ${getSignalBg(item.action_signal)}` : 'none'
                  }}>
                    AI Tip: {item.action_signal || "⚪ HOLD"}
                  </span>
                </div>

                <div className={styles.headline}>{item.headline}</div>
                
                {expandedId === item.id && (
                  <div className={styles.detailsContainer}>
                    <div className={styles.detailsContext}>
                      <strong>Context:</strong> {item.content ? item.content : "No additional context provided."}
                    </div>
                    <div className={styles.detailsImpact}>
                      <strong>Market/Stock Affected:</strong> {item.related_tickers === 'GENERAL_MARKET' ? 'Indian Equities (Broad Market)' : item.related_tickers.split('.')[0]}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

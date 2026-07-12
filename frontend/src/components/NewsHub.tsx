import React, { useState, useEffect } from 'react';
import styles from './NewsHub.module.css';

export interface NewsItem {
  id: number;
  headline: string;
  source: string;
  timestamp: string;
  related_tickers: string;
  sentiment_label: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
}

export const NewsHub: React.FC = () => {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

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
      // Handle the ISO string without Z
      const dateStr = ts.includes('Z') ? ts : ts + 'Z';
      const diff = new Date().getTime() - new Date(dateStr).getTime();
      const hours = Math.floor(diff / (1000 * 60 * 60));
      if (hours < 1) {
        const mins = Math.floor(diff / (1000 * 60));
        return `${mins || 1} mins ago`;
      }
      if (hours < 24) return `${hours} hrs ago`;
      return `${Math.floor(hours / 24)} days ago`;
    } catch {
      return ts.split('T')[0];
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>Stocks in the News</div>
      <div className={styles.newsList}>
        {loading ? (
          <div className={styles.emptyState}>Loading live news...</div>
        ) : news.length === 0 ? (
          <div className={styles.emptyState}>No recent news found.</div>
        ) : (
          news.map(item => {
            const isPos = item.sentiment_label === 'POSITIVE';
            const isNeg = item.sentiment_label === 'NEGATIVE';
            const arrowColor = isPos ? styles.positive : isNeg ? styles.negative : styles.neutral;
            const arrowIcon = isPos ? '↑' : isNeg ? '↓' : '→';

            return (
              <div key={item.id} className={styles.newsCard}>
                <div className={styles.topRow}>
                  <span className={styles.source}>{item.source || 'AI Scraper'}</span>
                  <span className={styles.time}>{getTimeAgo(item.timestamp)}</span>
                </div>
                <div className={styles.headline}>{item.headline}</div>
                
                {/* UPSTOX STYLE IMPACT BOX */}
                {item.related_tickers && (
                  <div className={styles.impactBox}>
                    <span className={styles.impactSymbol}>{item.related_tickers.split('.')[0]}</span>
                    <span className={`${styles.impactArrow} ${arrowColor}`}>{arrowIcon}</span>
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

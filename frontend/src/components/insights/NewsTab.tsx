import React from 'react';

interface NewsTabProps {
  symbol: string;
}

export const NewsTab: React.FC<NewsTabProps> = ({ symbol }) => {
  const cleanSymbol = symbol.split('.')[0];
  
  const news = [
    {
      source: 'NSE Bulk Trades',
      time: '3 days ago',
      headline: `JUNOMONETA FINSOL sold 49.8M shares of ${cleanSymbol} at avg price Rs 10.42.`
    },
    {
      source: 'ScoutQuest',
      time: '5 days ago',
      headline: `${cleanSymbol} clears outstanding debt; Matrimony's billings rise 7.8% YoY.\nSmartworks adds 1.63 lakh sq ft in Pune; Embassy Q1 pre-sales triple, collections up 54% YoY.`
    },
    {
      source: 'ScoutQuest',
      time: '6 days ago',
      headline: `${cleanSymbol} cleared outstanding debt for 2 of 14 banks under a settlement.\nThis aligns with its goal to become debt-free this quarter, marking progress.`
    },
    {
      source: 'NDTV Profit',
      time: '7 days ago',
      headline: `Experts recommend holding Anant Raj & Canara Bank, citing rangebound prices and support levels.\nBuy Eternal & Siemens Energy; sell Swiggy. ${cleanSymbol} hold advised; no fresh buys suggested.`
    }
  ];

  return (
    <div style={{ padding: '0 16px' }}>
      <div style={{ 
        padding: '16px 0', 
        borderBottom: '1px solid rgba(255,255,255,0.05)'
      }}>
        <div style={{ fontSize: '0.9rem', color: '#c9d1d9', lineHeight: '1.4' }}>
          HRTI Pvt Ltd sold 43,636,642 shares of {cleanSymbol} Ltd at an avg price of ₹10.3.
        </div>
      </div>

      {news.map((item, i) => (
        <div key={i} style={{ 
          padding: '16px 0', 
          borderBottom: '1px solid rgba(255,255,255,0.05)'
        }}>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: '#8b949e' }}>{item.source}</span>
            <span style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#8b949e' }} />
            <span style={{ fontSize: '0.8rem', color: '#8b949e' }}>{item.time}</span>
          </div>
          <div style={{ fontSize: '0.9rem', color: '#c9d1d9', lineHeight: '1.5', whiteSpace: 'pre-line' }}>
            {item.headline}
          </div>
        </div>
      ))}
    </div>
  );
};

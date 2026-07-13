import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { OverviewTab } from './insights/OverviewTab';
import { TechnicalsTab } from './insights/TechnicalsTab';
import { NewsTab } from './insights/NewsTab';
import { EventsTab } from './insights/EventsTab';
import { useAlerts } from '../contexts/AlertContext';
import { OrderPad } from './OrderPad';

interface StockInsightsModalProps {
  symbol: string;
  currentPrice: number;
  trend: string;
  onClose: () => void;
}

export const StockInsightsModal: React.FC<StockInsightsModalProps> = ({ 
  symbol, 
  currentPrice, 
  trend,
  onClose 
}) => {
  const [activeTab, setActiveTab] = useState<'Overview' | 'Technicals' | 'News' | 'Events'>('Overview');
  const [showOrderPad, setShowOrderPad] = useState<'BUY' | 'SELL' | null>(null);
  
  const tabs = ['Overview', 'Technicals', 'News', 'Events'];

  const isBullish = trend === 'Bullish' || trend === 'Strong Buy';
  const priceColor = isBullish ? '#00c853' : '#ff3366';
  
  // Synthetic daily change for the visual effect
  const dailyChangePct = isBullish ? '+1.24%' : '-0.70%';
  const dailyChangeAbs = isBullish ? '+(12.45)' : '-(0.07)';

  return (
    <AnimatePresence>
      <motion.div 
        initial={{ y: '100%', opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: '100%', opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        style={{
          position: 'fixed',
          inset: 0,
          background: '#0b0e14', // Solid dark background like a broker app
          zIndex: 10000,
          display: 'flex',
          flexDirection: 'column',
          color: '#fff',
          fontFamily: 'Inter, sans-serif'
        }}
      >
        {/* TOP HEADER */}
        <div style={{ 
          padding: '48px 16px 16px 16px', // Clear Android notch 
          background: '#12151c',
          borderBottom: '1px solid rgba(255,255,255,0.05)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
            <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#fff', fontSize: '1.5rem', cursor: 'pointer', padding: '0 8px 0 0' }}>
              ←
            </button>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 600 }}>{symbol.split('.')[0]}</h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                <span style={{ fontSize: '1rem', fontWeight: 'bold' }}>₹{currentPrice.toFixed(2)}</span>
                <span style={{ fontSize: '0.85rem', color: priceColor }}>{dailyChangeAbs} ({dailyChangePct})</span>
              </div>
            </div>
            
            <div style={{ marginLeft: 'auto', display: 'flex', gap: '16px' }}>
              <span style={{ fontSize: '1.2rem', cursor: 'pointer' }}>⏰</span>
              <span style={{ fontSize: '1.2rem', cursor: 'pointer' }}>🔖</span>
              <span style={{ fontSize: '1.2rem', cursor: 'pointer' }}>🔍</span>
            </div>
          </div>

          {/* TABS */}
          <div style={{ display: 'flex', gap: '24px', overflowX: 'auto', paddingBottom: '4px', scrollbarWidth: 'none' }}>
            {tabs.map(tab => (
              <div 
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                style={{
                  paddingBottom: '8px',
                  cursor: 'pointer',
                  fontWeight: activeTab === tab ? 600 : 400,
                  color: activeTab === tab ? '#fff' : '#8b949e',
                  borderBottom: activeTab === tab ? '2px solid #fff' : '2px solid transparent',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.2s'
                }}
              >
                {tab}
              </div>
            ))}
          </div>
        </div>

        {/* CONTENT AREA */}
        <div style={{ flex: 1, overflowY: 'auto', background: '#0b0e14' }}>
          {activeTab === 'Overview' && <OverviewTab symbol={symbol} />}
          {activeTab === 'Technicals' && <TechnicalsTab trend={trend} />}
          {activeTab === 'News' && <NewsTab symbol={symbol} />}
          {activeTab === 'Events' && <EventsTab />}
        </div>

        {/* BOTTOM ACTION BAR (Buy / Sell) */}
        <div style={{
          padding: '16px',
          background: '#12151c',
          borderTop: '1px solid rgba(255,255,255,0.05)',
          display: 'flex',
          gap: '12px'
        }}>
          <button style={{ 
            background: 'rgba(255,255,255,0.05)', 
            border: 'none', 
            color: '#fff', 
            padding: '12px 24px', 
            borderRadius: '8px',
            fontWeight: 600
          }}>
            SIP
          </button>
          <button 
            onClick={() => setShowOrderPad('SELL')}
            style={{ 
            flex: 1,
            background: 'rgba(255,51,102,0.1)', 
            border: '1px solid rgba(255,51,102,0.2)',
            color: '#ff3366', 
            padding: '12px', 
            borderRadius: '8px',
            fontWeight: 600,
            cursor: 'pointer'
          }}>
            Sell
          </button>
          <button 
            onClick={() => setShowOrderPad('BUY')}
            style={{ 
            flex: 1,
            background: 'rgba(0, 200, 83, 0.1)', 
            border: '1px solid rgba(0, 200, 83, 0.2)',
            color: '#00c853', 
            padding: '12px', 
            borderRadius: '8px',
            fontWeight: 600,
            cursor: 'pointer'
          }}>
            Buy
          </button>
        </div>

        {/* ORDER PAD SLIDE OVERLAY */}
        <AnimatePresence>
          {showOrderPad && (
            <>
              {/* Dim Backdrop */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setShowOrderPad(null)}
                style={{
                  position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 15000
                }}
              />
              <OrderPad 
                symbol={symbol}
                action={showOrderPad}
                currentPrice={currentPrice}
                onClose={() => {
                  setShowOrderPad(null);
                  onClose();
                }}
              />
            </>
          )}
        </AnimatePresence>
      </motion.div>
    </AnimatePresence>
  );
};

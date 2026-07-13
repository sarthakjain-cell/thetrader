import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAlerts } from '../contexts/AlertContext';

interface OrderPadProps {
  symbol: string;
  action: 'BUY' | 'SELL';
  currentPrice: number;
  onClose: () => void;
}

export const OrderPad: React.FC<OrderPadProps> = ({ symbol, action, currentPrice, onClose }) => {
  const [qty, setQty] = useState(10);
  const [orderType, setOrderType] = useState('MARKET');
  const [productType, setProductType] = useState('INTRADAY');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { addAlert } = useAlerts();

  const color = action === 'BUY' ? '#00c853' : '#ff3366';
  const bgColor = action === 'BUY' ? 'rgba(0, 200, 83, 0.1)' : 'rgba(255, 51, 102, 0.1)';

  const executeOrder = async () => {
    setIsSubmitting(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://206.189.129.232:8000';
      const res = await fetch(`${baseUrl}/api/order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, action, price: currentPrice, qty })
      });
      const data = await res.json();
      if (data.status === 'success') {
        addAlert({ type: 'success', message: `${action} order for ${qty} shares of ${symbol.split('.')[0]} executed.` });
        onClose(); // Close the pad
      } else {
        addAlert({ type: 'error', message: data.message || `Failed to ${action}` });
      }
    } catch (e) {
      addAlert({ type: 'error', message: "Network error placing order." });
    }
    setIsSubmitting(false);
  };

  return (
    <motion.div
      initial={{ y: '100%' }}
      animate={{ y: 0 }}
      exit={{ y: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 300 }}
      style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        height: '75%',
        background: '#12151c',
        borderTopLeftRadius: '24px',
        borderTopRightRadius: '24px',
        boxShadow: '0 -10px 40px rgba(0,0,0,0.5)',
        zIndex: 20000,
        display: 'flex',
        flexDirection: 'column',
        color: '#fff',
        padding: '24px'
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.2rem', color: color }}>{action} {symbol.split('.')[0]}</h2>
          <div style={{ fontSize: '0.9rem', color: '#8b949e', marginTop: '4px' }}>NSE • ₹{currentPrice.toFixed(2)}</div>
        </div>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#8b949e', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
      </div>

      {/* Product Type Toggle */}
      <div style={{ display: 'flex', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', padding: '4px', marginBottom: '24px' }}>
        {['INTRADAY', 'DELIVERY'].map(pt => (
          <div 
            key={pt}
            onClick={() => setProductType(pt)}
            style={{ 
              flex: 1, textAlign: 'center', padding: '10px', borderRadius: '6px', fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer',
              background: productType === pt ? '#21262d' : 'transparent',
              color: productType === pt ? '#fff' : '#8b949e',
              transition: 'all 0.2s'
            }}
          >
            {pt}
          </div>
        ))}
      </div>

      {/* Inputs */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '32px' }}>
        <div style={{ flex: 1 }}>
          <label style={{ display: 'block', fontSize: '0.85rem', color: '#8b949e', marginBottom: '8px' }}>Qty</label>
          <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', border: `1px solid ${color}` }}>
            <button onClick={() => setQty(Math.max(1, qty - 1))} style={{ padding: '12px 16px', background: 'transparent', border: 'none', color: '#fff', fontSize: '1.2rem' }}>-</button>
            <input 
              type="number" 
              value={qty} 
              onChange={e => setQty(Number(e.target.value))} 
              style={{ flex: 1, background: 'transparent', border: 'none', color: '#fff', textAlign: 'center', fontSize: '1.1rem', fontWeight: 'bold', outline: 'none' }}
            />
            <button onClick={() => setQty(qty + 1)} style={{ padding: '12px 16px', background: 'transparent', border: 'none', color: '#fff', fontSize: '1.2rem' }}>+</button>
          </div>
        </div>
        
        <div style={{ flex: 1 }}>
          <label style={{ display: 'block', fontSize: '0.85rem', color: '#8b949e', marginBottom: '8px' }}>Price</label>
          <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', padding: '12px', border: '1px solid rgba(255,255,255,0.1)' }}>
            <span style={{ color: orderType === 'MARKET' ? '#8b949e' : '#fff', fontSize: '1.1rem', fontWeight: 'bold' }}>
              {orderType === 'MARKET' ? 'MARKET' : currentPrice.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Order Type */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: 'auto' }}>
        {['MARKET', 'LIMIT'].map(ot => (
          <div 
            key={ot}
            onClick={() => setOrderType(ot)}
            style={{
              padding: '6px 16px',
              borderRadius: '20px',
              border: orderType === ot ? `1px solid ${color}` : '1px solid rgba(255,255,255,0.2)',
              color: orderType === ot ? color : '#8b949e',
              fontSize: '0.85rem', cursor: 'pointer'
            }}
          >
            {ot}
          </div>
        ))}
      </div>

      {/* Summary & Submit */}
      <div style={{ marginTop: 'auto', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
          <span style={{ color: '#8b949e', fontSize: '0.9rem' }}>Margin Required</span>
          <span style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>₹{(currentPrice * qty * (productType === 'INTRADAY' ? 0.2 : 1)).toFixed(2)}</span>
        </div>
        
        <button 
          onClick={executeOrder}
          disabled={isSubmitting}
          style={{
            width: '100%',
            padding: '16px',
            background: color,
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            fontSize: '1.1rem',
            fontWeight: 'bold',
            cursor: isSubmitting ? 'wait' : 'pointer',
            opacity: isSubmitting ? 0.7 : 1,
            boxShadow: `0 4px 12px ${bgColor}`
          }}
        >
          {isSubmitting ? 'Processing...' : `SWIPE TO ${action}`}
        </button>
      </div>
    </motion.div>
  );
};

"use client";

import React, { useState, useEffect } from 'react';
import styles from './page.module.css';

interface ConfigState {
  max_daily_loss: number;
  max_trades: number;
  ai_active: boolean;
  orb_active: boolean;
  vwap_active: boolean;
  kill_switch: boolean;
}

export default function ProfilePage() {
  const [config, setConfig] = useState<ConfigState>({
    max_daily_loss: 3000,
    max_trades: 5,
    ai_active: true,
    orb_active: true,
    vwap_active: true,
    kill_switch: false
  });
  
  const [isSaving, setIsSaving] = useState(false);
  const [geminiKey, setGeminiKey] = useState('');

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://206.189.129.232:8000';
      const res = await fetch(`${baseUrl}/api/config`);
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
      }
    } catch (err) {
      console.error("Failed to fetch config", err);
    }
  };

  const saveConfig = async (newConfig: ConfigState) => {
    setIsSaving(true);
    setConfig(newConfig); // Optimistic UI update
    
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://206.189.129.232:8000';
      await fetch(`${baseUrl}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig)
      });
    } catch (err) {
      console.error("Failed to save config", err);
    }
    setIsSaving(false);
  };

  const handleToggle = (key: keyof ConfigState) => {
    const updated = { ...config, [key]: !config[key] };
    saveConfig(updated);
  };

  const handleInputChange = (key: keyof ConfigState, value: string) => {
    const num = parseInt(value) || 0;
    setConfig({ ...config, [key]: num });
  };

  const handleInputBlur = () => {
    saveConfig(config);
  };

  const handleKillSwitch = () => {
    if (window.confirm("EMERGENCY HALT: Are you sure you want to kill all AI trading for today? This cannot be undone from the app.")) {
      saveConfig({ ...config, kill_switch: true });
    }
  };

  const handleSaveKey = async () => {
    if (!geminiKey) return;
    setIsSaving(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://206.189.129.232:8000';
      const res = await fetch(`${baseUrl}/api/keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gemini_key: geminiKey })
      });
      if (res.ok) {
        alert('Key securely saved! The AI is now ready.');
        setGeminiKey('');
      } else {
        alert('Failed to save key. Please try again.');
      }
    } catch (err) {
      alert('Network error while saving key.');
    }
    setIsSaving(false);
  };

  return (
    <div className={styles.pageContainer}>
      
      {/* Header */}
      <div className={styles.headerSection}>
        <div className={styles.avatarLarge}>
          <span>SJ</span>
        </div>
        <h1>Sarthak Jain</h1>
        <p>Command Center</p>
        <div className={styles.badge}>PRO Tier Active</div>
      </div>

      {/* API Connections */}
      <div className={styles.sectionGroup}>
        <span className={styles.sectionTitle}>API Connections</span>
        <div className={styles.listGroup}>
          <div className={styles.listItem} style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', marginBottom: '8px' }}>
              <span className={styles.listItemLabel}>Gemini AI Key</span>
            </div>
            <div style={{ display: 'flex', width: '100%', gap: '10px' }}>
              <input 
                type="password" 
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder="Paste Gemini API key here..." 
                className={styles.inputField}
                style={{ flex: 1, textAlign: 'left', minWidth: 0 }}
              />
              <button 
                onClick={handleSaveKey}
                disabled={isSaving || !geminiKey}
                className={styles.saveButton}
                style={{ marginTop: 0 }}
              >
                Save
              </button>
            </div>
            <p className={styles.helperText} style={{ marginLeft: 0, marginTop: '8px' }}>
              Required for Chatbot and NLP features.
            </p>
          </div>
        </div>
      </div>

      {/* AI Strategy Toggles */}
      <div className={styles.sectionGroup}>
        <span className={styles.sectionTitle}>Engine Configuration</span>
        <div className={styles.listGroup}>
          <div className={styles.listItem}>
            <div className={styles.listItemRow}>
              <span className={styles.listItemLabel}>Machine Learning Oracle</span>
              <div 
                className={styles.toggleSwitch} 
                data-active={config.ai_active}
                onClick={() => handleToggle('ai_active')}
              >
                <div className={styles.toggleKnob} />
              </div>
            </div>
            <p className={styles.helperText} style={{marginLeft: 0, marginTop: '8px'}}>
              Uses LightGBM predictions to veto low-probability setups.
            </p>
          </div>
          
          <div className={styles.listItem}>
            <div className={styles.listItemRow}>
              <span className={styles.listItemLabel}>Strategy: ORB Breakout</span>
              <div 
                className={styles.toggleSwitch} 
                data-active={config.orb_active}
                onClick={() => handleToggle('orb_active')}
              >
                <div className={styles.toggleKnob} />
              </div>
            </div>
          </div>
          
          <div className={styles.listItem}>
            <div className={styles.listItemRow}>
              <span className={styles.listItemLabel}>Strategy: VWAP Reversion</span>
              <div 
                className={styles.toggleSwitch} 
                data-active={config.vwap_active}
                onClick={() => handleToggle('vwap_active')}
              >
                <div className={styles.toggleKnob} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Limits */}
      <div className={styles.sectionGroup}>
        <span className={styles.sectionTitle}>Live Risk Limits</span>
        <div className={styles.listGroup}>
          <div className={styles.listItem}>
            <div className={styles.listItemRow}>
              <span className={styles.listItemLabel}>Max Daily Drawdown (INR)</span>
              <input 
                type="number" 
                className={styles.inputField}
                value={config.max_daily_loss}
                onChange={(e) => handleInputChange('max_daily_loss', e.target.value)}
                onBlur={handleInputBlur}
              />
            </div>
          </div>
          <div className={styles.listItem}>
            <div className={styles.listItemRow}>
              <span className={styles.listItemLabel}>Max Trades Per Day</span>
              <input 
                type="number" 
                className={styles.inputField}
                value={config.max_trades}
                onChange={(e) => handleInputChange('max_trades', e.target.value)}
                onBlur={handleInputBlur}
              />
            </div>
          </div>
        </div>
        <p className={styles.helperText}>
          Changes are synced instantly to the backend MetaAllocator. {isSaving && <span style={{color: 'var(--accent-gold)'}}>Saving...</span>}
        </p>
      </div>

      {/* Emergency Kill Switch */}
      <div className={styles.sectionGroup} style={{ marginTop: '16px' }}>
        <button 
          className={styles.killButton}
          onClick={handleKillSwitch}
          disabled={config.kill_switch}
          style={{ opacity: config.kill_switch ? 0.5 : 1, cursor: config.kill_switch ? 'not-allowed' : 'pointer' }}
        >
          {config.kill_switch ? 'Engine Halted for Today' : 'Emergency Halt Engine'}
        </button>
      </div>
      
    </div>
  );
}

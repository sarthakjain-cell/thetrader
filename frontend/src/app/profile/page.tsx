"use client";

import React, { useState } from 'react';
import { User, ChevronRight, Settings, Shield, Bell } from 'lucide-react';
import styles from './page.module.css';

export default function ProfilePage() {
  const [geminiKey, setGeminiKey] = useState('');
  const [isSaving, setIsSaving] = useState(false);

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
      
      {/* Centered Identity Area (No Box) */}
      <div className={styles.headerSection}>
        <div className={styles.avatarLarge}>
          <span>SJ</span>
        </div>
        <h1>Sarthak Jain</h1>
        <p>sjain16089@gmail.com</p>
        <div className={styles.badge}>PRO Plan Active</div>
      </div>

      {/* API Connector - iOS Style Grouped List */}
      <div className={styles.sectionGroup}>
        <span className={styles.sectionTitle}>API & Broker Connections</span>
        <div className={styles.listGroup}>
          <div className={styles.listItem} style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', marginBottom: '8px' }}>
              <span className={styles.itemLabel}>Gemini AI Key</span>
              <span className={styles.itemValue} style={{ color: '#EF4444' }}>Not Connected</span>
            </div>
            <div style={{ display: 'flex', width: '100%', gap: '10px' }}>
              <input 
                type="password" 
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder="Paste your paid Gemini API key here..." 
                style={{
                  flex: 1,
                  background: 'rgba(0,0,0,0.2)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  padding: '8px 12px',
                  color: 'white',
                  fontSize: '14px',
                  outline: 'none'
                }}
              />
              <button 
                onClick={handleSaveKey}
                disabled={isSaving || !geminiKey}
                style={{
                  background: isSaving || !geminiKey ? 'rgba(59, 130, 246, 0.5)' : '#3B82F6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '8px 16px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: isSaving || !geminiKey ? 'not-allowed' : 'pointer',
                  transition: 'background 0.2s'
              }}>
                {isSaving ? 'Saving...' : 'Save'}
              </button>
            </div>
            <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', marginTop: '8px' }}>
              This key will be securely updated on the server and used to power the AI Copilot and Engine B.
            </p>
          </div>
          
          <div className={styles.listItem}>
            <div className={styles.listItemRow}>
              <span className={styles.listItemLabel}>Upstox Broker</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className={styles.itemValue}>Paper Trading Mode</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Management Defaults */}
      <div className={styles.sectionGroup}>
        <span className={styles.sectionTitle}>Risk Management</span>
        <div className={styles.listGroup}>
          <div className={styles.listItem}>
            <div className={styles.listItemRow}>
              <span className={styles.listItemLabel}>Max Daily Loss (INR)</span>
              <input 
                type="number" 
                className={styles.inputField}
                defaultValue={2000}
                readOnly
              />
            </div>
          </div>
          <div className={styles.listItem}>
            <div className={styles.listItemRow}>
              <span className={styles.listItemLabel}>Default Position Size</span>
              <input 
                type="number" 
                className={styles.inputField}
                defaultValue={1}
                readOnly
              />
            </div>
          </div>
        </div>
        <p className={styles.helperText}>
          Risk limits are enforced at the server level via config.py and cannot be modified from the mobile client for security reasons.
        </p>
      </div>

      {/* Help & Support */}
      <div className={styles.sectionGroup}>
        <span className={styles.sectionTitle}>Support</span>
        <a href="#" className={styles.helpLink}>
          <span>📚 Strategy Walkthroughs</span>
          <span className={styles.helpLinkChevron}>›</span>
        </a>
        <a href="#" className={styles.helpLink}>
          <span>💬 Contact Support</span>
          <span className={styles.helpLinkChevron}>›</span>
        </a>
        <a href="#" className={styles.helpLink}>
          <span>📜 Terms of Service</span>
          <span className={styles.helpLinkChevron}>›</span>
        </a>
      </div>
      
    </div>
  );
}

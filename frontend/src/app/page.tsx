"use client";

import React from 'react';
import { useAlgoStream } from '../hooks/useAlgoStream';
import { KillBanner } from '../components/KillBanner';
import { StatusIndicator } from '../components/StatusIndicator';
import { VitalsGrid } from '../components/VitalsGrid';
import { PositionsTable } from '../components/PositionsTable';
import { TradesTable } from '../components/TradesTable';
import { TradingChart } from '../components/TradingChart';
import { EquityCurve } from '../components/EquityCurve';
import { AlertLog } from '../components/AlertLog';
import { ResearchDesk } from '../components/ResearchDesk';
import { SettingsModal } from '../components/SettingsModal';
import { InfoModal } from '../components/InfoModal';
import TradeExplanationModal from '../components/TradeExplanationModal';
import ScannerTab from '../components/ScannerTab';
import { ResearchTab } from '../components/ResearchTab';
import RippleButton from '../components/RippleButton';
import { BottomNav } from '../components/BottomNav';
import { Trade } from '../types';
import { useAlerts } from '../contexts/AlertContext';
import styles from './page.module.css';

export default function Home() {
  const [settingsOpen, setSettingsOpen] = React.useState(false);
  const [infoOpen, setInfoOpen] = React.useState(false);
  const [selectedTrade, setSelectedTrade] = React.useState<Trade | null>(null);
  const [activeTab, setActiveTab] = React.useState<'dashboard' | 'scanner' | 'charts' | 'news'>('dashboard');
  const { addAlert } = useAlerts();
  const state = useAlgoStream('http://206.189.129.232:8000/api/stream', addAlert);

  // Determine active symbol for charting (default to first open position)
  const activeSymbol = state.positions.length > 0 ? state.positions[0].symbol : '';

  return (
    <>
      <KillBanner isTriggered={state.account?.is_kill_triggered || false} />
      <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <InfoModal isOpen={infoOpen} onClose={() => setInfoOpen(false)} activeTab={activeTab} />
      <TradeExplanationModal trade={selectedTrade} onClose={() => setSelectedTrade(null)} />
      
      <div className={styles.main}>
        <div className={styles.content}>
          <header className={styles.topbar}>
            <div className={styles.titleWrapper}>
              <h1 className={styles.title}><span className={styles.logo}>⚡</span> AlgoTrade</h1>
              <div className={styles.status}>
                <span className={`${styles.statusDot} ${styles[state.status.toLowerCase()]}`} />
                <span className={styles.hideOnMobile}>{state.status}</span>
              </div>
            </div>
            
            <div className={styles.headerRight}>
              <button 
                className="btn-secondary" 
                onClick={() => setInfoOpen(true)}
                title="Tab Information"
                style={{ width: '36px', height: '36px', padding: 0, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', fontStyle: 'italic', fontFamily: 'serif' }}
              >
                i
              </button>
              <button 
                className="btn-primary" 
                onClick={() => setSettingsOpen(true)}
                style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                ⚙️ <span className={styles.hideOnMobile}>Settings</span>
              </button>
              <div className={styles.hideOnMobile}>
                <AlertLog />
              </div>
            </div>
          </header>

          <main className={styles.dashboard}>
            <div className={styles.tabsContainer}>
              <RippleButton 
                className={`${styles.tabBtn} ${activeTab === 'dashboard' ? styles.tabBtnActive : ''}`}
                onClick={() => setActiveTab('dashboard')}
              >
                Dashboard
              </RippleButton>
              <RippleButton 
                className={`${styles.tabBtn} ${activeTab === 'scanner' ? styles.tabBtnActive : ''}`}
                onClick={() => setActiveTab('scanner')}
              >
                Scanner
              </RippleButton>
              <RippleButton 
                className={`${styles.tabBtn} ${activeTab === 'research' ? styles.tabBtnActive : ''}`}
                onClick={() => setActiveTab('research')}
              >
                Research
              </RippleButton>
            </div>

            <div className={`${styles.tabContent} ${activeTab === 'dashboard' ? styles.activeTab : ''}`}>
              <VitalsGrid account={state.account} />
              <PositionsTable positions={state.positions} />
            </div>

            <div className={`${styles.tabContent} ${activeTab === 'scanner' ? styles.activeTab : ''}`}>
              <ScannerTab state={state} />
            </div>

            <div className={`${styles.tabContent} ${activeTab === 'charts' ? styles.activeTab : ''}`}>
              <TradingChart symbol={activeSymbol} trades={state.today_trades} onMarkerClick={setSelectedTrade} />
              <EquityCurve />
            </div>

            <div className={`${styles.tabContent} ${activeTab === 'news' ? styles.activeTab : ''}`}>
              <TradesTable trades={state.today_trades} onTradeClick={setSelectedTrade} />
              <div className={styles.mobileResearchDesk}>
                <ResearchDesk tips={state.research_tips} />
              </div>
            </div>
          </main>
        </div>

        <aside className={styles.sidebar}>
          <ScannerTab state={state} />
          <ResearchDesk tips={state.research_tips} />
        </aside>
      </div>

      <div className={styles.mobileNavWrapper}>
        <BottomNav activeTab={activeTab} setActiveTab={setActiveTab} />
      </div>
    </>
  );
}

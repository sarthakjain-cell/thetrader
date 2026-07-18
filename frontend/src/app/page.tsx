"use client";

import React, { useState, useEffect } from 'react';
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from 'react-resizable-panels';
import { useAlgoStream } from '../hooks/useAlgoStream';
import { CommandPalette } from '../components/CommandPalette';
import { MarketPulse } from '../components/MarketPulse';
import { CategoryScroll } from '../components/CategoryScroll';
import { AIPortfolio } from '../components/AIPortfolio';
import { NewsHub } from '../components/NewsHub';
import { TradingChart } from '../components/TradingChart';
import { KillBanner } from '../components/KillBanner';
import { BottomNav } from '../components/BottomNav';
import { Scanner } from '../components/Scanner';
import { useAlerts } from '../contexts/AlertContext';
import { AlertLog } from '../components/AlertLog';
import { StockInsightsModal } from '../components/StockInsightsModal';
import { ProfileDropdown } from '../components/ProfileDropdown';
import styles from './page.module.css';

export default function Home() {
  const { addAlert } = useAlerts();
  const state = useAlgoStream(process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/stream` : 'http://206.189.129.232:8000/api/stream', addAlert);
  
  const [isMobile, setIsMobile] = useState(false);
  const [activeTab, setActiveTab] = useState<'home' | 'scanner' | 'charts' | 'portfolio' | 'news'>('home');
  const [selectedChartSymbol, setSelectedChartSymbol] = useState<string | null>(null);
  const [selectedInsightSymbol, setSelectedInsightSymbol] = useState<string | null>(null);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 1024);
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const marketSignals = state.market_signals?.map((sig: any) => {
    return {
      symbol: sig.symbol,
      ai_prob: sig.ai_prob || 0.5,
      rsi: sig.rsi || 50,
      macd: sig.adx || 25, 
      trend: sig.signal === 'BUY' ? 'Bullish' : sig.signal === 'SELL' ? 'Bearish' : 'Neutral',
      sentiment: sig.sentiment || 0,
      last_price: sig.last_price || 0,
      volume_spike: sig.volume_spike || 1
    };
  }) || [];

  const activeSymbol = selectedChartSymbol || (state.positions.length > 0 ? state.positions[0].symbol : 'RELIANCE.NS');

  return (
    <>
      <KillBanner isTriggered={state.account?.is_kill_triggered || false} />
      
      <div className={`${styles.terminalContainer} ${isMobile ? styles.isMobileView : ''}`}>
        
        {/* Upstox-style Top Header */}
        <header className={styles.topSection}>
          <div className={styles.commandRow}>
            <div className={styles.logo}>AlgoTrade AI</div>
            
            <div className={styles.searchContainer} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ flex: 1 }}>
                <CommandPalette onSearch={(sym) => setSelectedInsightSymbol(sym)} />
              </div>
              <AlertLog />
              <ProfileDropdown />
            </div>

            <div className={styles.statusBox}>
              <span className={`${styles.statusDot} ${styles[state.status.toLowerCase()] || ''}`} />
              <span className={styles.statusText}>{state.status}</span>
            </div>
          </div>

          {/* Nifty/Sensex Capsules immediately below search */}
          <MarketPulse />
        </header>

        {/* Workspace */}
        <main className={styles.workspace}>
          {isMobile ? (
            <div className={styles.mobileContent}>
              {activeTab === 'home' && (
                <div className={styles.mobileTab}>
                  <div style={{ paddingTop: '16px' }} />
                  <CategoryScroll title="Top AI Buys" signals={marketSignals.slice(0, 3)} onStockClick={setSelectedInsightSymbol} />
                  <CategoryScroll title="Momentum Leaders" signals={marketSignals.slice(3, 6)} onStockClick={setSelectedInsightSymbol} />
                  <CategoryScroll title="Value Picks" signals={marketSignals.slice(0, 2)} onStockClick={setSelectedInsightSymbol} />
                  <div style={{ paddingBottom: '32px' }} />
                </div>
              )}
              {activeTab === 'scanner' && (
                <div className={styles.mobileTab}>
                  <Scanner signals={marketSignals} />
                </div>
              )}
              {activeTab === 'portfolio' && (
                <div className={styles.mobileTab}>
                  <AIPortfolio 
                    positions={state.positions} 
                    account={state.account} 
                    strategies={state.strategies} 
                    onPositionClick={(sym) => { setSelectedChartSymbol(sym); setActiveTab('charts'); }}
                  />
                </div>
              )}
              {activeTab === 'charts' && (
                <div className={styles.mobileTab}>
                  <div className={styles.chartWrapper}>
                    <TradingChart symbol={activeSymbol} trades={state.today_trades} onMarkerClick={() => {}} />
                  </div>
                </div>
              )}
              {activeTab === 'news' && (
                <div className={styles.mobileTab}>
                  <NewsHub />
                </div>
              )}
            </div>
          ) : (
            <PanelGroup direction="horizontal">
              <Panel defaultSize={25} minSize={20} maxSize={40} className={styles.panel}>
                <div className={styles.panelContent}>
                  <CategoryScroll title="Top AI Buys" signals={marketSignals} onStockClick={setSelectedInsightSymbol} />
                  <AIPortfolio 
                    positions={state.positions} 
                    account={state.account} 
                    strategies={state.strategies}
                    onPositionClick={(sym) => setSelectedChartSymbol(sym)}
                  />
                </div>
              </Panel>
              <PanelResizeHandle className={styles.resizeHandle} />
              <Panel defaultSize={50} minSize={30} className={styles.panel}>
                <div className={styles.panelContent}>
                  <div className={styles.chartWrapper}>
                    <TradingChart symbol={activeSymbol} trades={state.today_trades} onMarkerClick={() => {}} />
                  </div>
                </div>
              </Panel>
              <PanelResizeHandle className={styles.resizeHandle} />
              <Panel defaultSize={25} minSize={20} maxSize={40} className={styles.panel}>
                <div className={styles.panelContent}>
                  <NewsHub />
                </div>
              </Panel>
            </PanelGroup>
          )}
        </main>
      </div>

      {selectedInsightSymbol && (
        <StockInsightsModal 
          symbol={selectedInsightSymbol} 
          currentPrice={marketSignals.find(s => s.symbol === selectedInsightSymbol)?.last_price || 0}
          trend={marketSignals.find(s => s.symbol === selectedInsightSymbol)?.trend || 'Neutral'}
          onClose={() => setSelectedInsightSymbol(null)} 
        />
      )}

      {isMobile && (
        <BottomNav activeTab={activeTab} setActiveTab={setActiveTab} />
      )}
    </>
  );
}

import React, { useEffect, useRef, useState, useMemo } from 'react';
import { createChart, IChartApi, ISeriesApi, ColorType, CrosshairMode } from 'lightweight-charts';
import { Trade } from '../types';
import styles from './TradingChart.module.css';

interface Props {
  symbol: string;
  trades: Trade[];
  onMarkerClick?: (trade: Trade) => void;
}

export const TradingChart: React.FC<Props> = ({ symbol, trades, onMarkerClick }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!chartContainerRef.current) return;
    
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#8b949e',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.02)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.02)' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          width: 1,
          color: 'rgba(255, 255, 255, 0.1)',
          style: 3,
        },
        horzLine: {
          width: 1,
          color: 'rgba(255, 255, 255, 0.1)',
          style: 3,
        },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: 'rgba(255, 255, 255, 0.05)',
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.05)',
      },
      watermark: {
        visible: true,
        fontSize: 120,
        horzAlign: 'center',
        vertAlign: 'center',
        color: 'rgba(255, 255, 255, 0.03)',
        text: symbol || 'ALGO-AI',
      },
      height: chartContainerRef.current.clientHeight || 400,
    });
    
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#00f5a0', downColor: '#ff0076', borderVisible: false,
      wickUpColor: '#00f5a0', wickDownColor: '#ff0076',
    });
    
    chartRef.current = chart;
    seriesRef.current = candlestickSeries;
    
    const resizeObserver = new ResizeObserver(entries => {
      if (entries.length === 0 || entries[0].target !== chartContainerRef.current) { return; }
      const newRect = entries[0].contentRect;
      chart.applyOptions({ height: newRect.height, width: newRect.width });
    });
    
    resizeObserver.observe(chartContainerRef.current);
    
    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, []);

  useEffect(() => {
    if (!symbol || !seriesRef.current) return;
    
    const fetchBars = async () => {
      setLoading(true);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://206.189.129.232:8000';
        const res = await fetch(`${baseUrl}/api/bars/${symbol}`);
        const data = await res.json();
        
        if (data.length === 0) return;

        // Deduplicate and sort
        const uniqueData = Array.from(new Map(data.map((item: any) => [item.time, item])).values());
        uniqueData.sort((a: any, b: any) => a.time - b.time);
        seriesRef.current?.setData(uniqueData as any);
        
        // Generate Markers
        const markers: any[] = [];
        
        // Find closest bar time helper
        const findClosestTime = (targetUnix: number) => {
           let closest = uniqueData[0].time;
           let minDiff = Math.abs(targetUnix - closest);
           for (const d of uniqueData) {
               const diff = Math.abs(targetUnix - d.time);
               if (diff < minDiff) {
                   minDiff = diff;
                   closest = d.time;
               }
           }
           return closest;
        };

        trades.filter(t => t.symbol === symbol).forEach(t => {
          const entryTimeUnix = new Date(t.entry_time).getTime() / 1000;
          markers.push({ 
            time: findClosestTime(entryTimeUnix), 
            position: 'belowBar', 
            color: '#00f5a0', 
            shape: 'arrowUp', 
            text: `EXEC: BUY @ ${t.entry_price}`,
            id: `trade_${t.id}`
          });
          
          if (t.exit_time) {
            const exitTimeUnix = new Date(t.exit_time).getTime() / 1000;
            markers.push({ 
              time: findClosestTime(exitTimeUnix), 
              position: 'aboveBar', 
              color: '#ff0076', 
              shape: 'arrowDown', 
              text: `EXEC: SELL @ ${t.exit_price}`,
              id: `trade_${t.id}`
            });
          }
        });
        
        markers.sort((a,b) => a.time - b.time);
        seriesRef.current?.setMarkers(markers);
        chartRef.current?.timeScale().fitContent();
        
      } catch (err) {
        console.error("Failed to fetch bars", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchBars();
    const interval = setInterval(fetchBars, 30000);
    return () => clearInterval(interval);
  }, [symbol, JSON.stringify(trades)]);

  // Get active trades for this symbol
  const activeSymbolTrades = useMemo(() => {
    return trades.filter(t => t.symbol === symbol).sort((a, b) => new Date(b.entry_time).getTime() - new Date(a.entry_time).getTime());
  }, [trades, symbol]);

  const latestTrade = activeSymbolTrades[0];
  const isHolding = latestTrade && !latestTrade.exit_time;

  return (
    <div className={styles.chartContainer}>
      <div className={styles.chartHeader}>
        <div className={styles.titleGroup}>
          <h3 className={styles.title}>
            {symbol ? `${symbol.replace('.NS', '')}` : 'STANDBY MODE'}
          </h3>
          <div className={styles.liveBadge}>
            <div className={styles.pulseDot} />
            LIVE EXECUTION
          </div>
        </div>
        {loading && <span style={{fontSize: '0.75rem', color: '#8b949e', letterSpacing: '1px'}}>SYNCING TELEMETRY...</span>}
      </div>

      {symbol ? (
        <div className={styles.chartArea}>
          <div ref={chartContainerRef} className={styles.lwChart} />
          
          {/* Glass HUD Overlay */}
          <div className={styles.hudOverlay}>
            <div className={styles.glassCard}>
              <div className={styles.hudTitle}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                AI TELEMETRY
              </div>
              <div className={styles.hudGrid}>
                <div className={styles.hudItem}>
                  <span className={styles.hudLabel}>Strategy Lock</span>
                  <span className={styles.hudValue}>{latestTrade?.strategy_id || 'SCANNING'}</span>
                </div>
                <div className={styles.hudItem}>
                  <span className={styles.hudLabel}>Status</span>
                  <span className={`${styles.hudValue} ${isHolding ? styles.bullish : ''}`}>{isHolding ? 'ACTIVE HOLD' : 'OBSERVING'}</span>
                </div>
                {isHolding && (
                  <>
                    <div className={styles.hudItem}>
                      <span className={styles.hudLabel}>Entry</span>
                      <span className={styles.hudValue}>₹{latestTrade.entry_price.toFixed(2)}</span>
                    </div>
                    <div className={styles.hudItem}>
                      <span className={styles.hudLabel}>Qty</span>
                      <span className={styles.hudValue}>{latestTrade.qty}</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Trade Log Overlay */}
          {activeSymbolTrades.length > 0 && (
            <div className={styles.executionPanel}>
              <div className={styles.tradeLog}>
                {activeSymbolTrades.slice(0, 2).map(t => (
                  <div key={t.id} className={`${styles.glassCard} ${styles.tradeEntry} ${t.exit_time ? styles.sell : ''}`}>
                    <div className={styles.tradeHeader}>
                      <span className={styles.tradeType}>{t.exit_time ? 'CLOSED POSITION' : 'OPEN POSITION'}</span>
                      <span className={styles.tradePrice}>
                        {t.exit_time ? `PnL: ₹${(t.pnl || 0).toFixed(2)}` : `Buy: ₹${t.entry_price}`}
                      </span>
                    </div>
                    <div className={styles.tradeReason}>
                      <strong>{t.strategy_id}</strong>: {t.reason}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className={styles.emptyState}>
          <div className={styles.radarSpinner} />
          <span>AWAITING TARGET SELECTION</span>
        </div>
      )}
    </div>
  );
};

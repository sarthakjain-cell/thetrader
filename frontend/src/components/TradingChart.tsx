import React, { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, ColorType } from 'lightweight-charts';
import { Trade } from '../types';

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
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
      height: 400,
    });
    
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#10b981', downColor: '#ef4444', borderVisible: false,
      wickUpColor: '#10b981', wickDownColor: '#ef4444',
    });
    
    chartRef.current = chart;
    seriesRef.current = candlestickSeries;
    
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  useEffect(() => {
    if (!symbol || !seriesRef.current) return;
    
    const fetchBars = async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/bars/${symbol}`);
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
            color: '#10b981', 
            shape: 'arrowUp', 
            text: `Buy @ ${t.entry_price}`,
            id: `trade_${t.id}`
          });
          
          if (t.exit_time) {
            const exitTimeUnix = new Date(t.exit_time).getTime() / 1000;
            markers.push({ 
              time: findClosestTime(exitTimeUnix), 
              position: 'aboveBar', 
              color: '#ef4444', 
              shape: 'arrowDown', 
              text: `Sell @ ${t.exit_price}`,
              id: `trade_${t.id}`
            });
          }
        });
        
        markers.sort((a,b) => a.time - b.time);
        seriesRef.current?.setMarkers(markers);
        chartRef.current?.timeScale().fitContent();
        
        // Add click handler for markers (Lightweight charts fires click on series)
        chartRef.current?.subscribeClick((param) => {
          if (!param.point || !param.seriesData || !onMarkerClick) return;
          // Actually, lightweight charts doesn't natively expose marker clicks well.
          // We can approximate by checking if the clicked time matches a trade.
          const time = param.time;
          if (time) {
             const matchedTrade = trades.find(t => {
                if (t.symbol !== symbol) return false;
                const entryUnix = new Date(t.entry_time).getTime() / 1000;
                const exitUnix = t.exit_time ? new Date(t.exit_time).getTime() / 1000 : 0;
                return Math.abs(entryUnix - (time as number)) < 300 || Math.abs(exitUnix - (time as number)) < 300;
             });
             if (matchedTrade) onMarkerClick(matchedTrade);
          }
        });
        
      } catch (err) {
        console.error("Failed to fetch bars", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchBars();
    const interval = setInterval(fetchBars, 30000);
    return () => clearInterval(interval);
  }, [symbol, trades]);

  return (
    <div className="glass-panel" style={{ marginBottom: 'var(--space-6)' }}>
      <div className="flex-between" style={{ padding: 'var(--space-4)', borderBottom: '1px solid var(--panel-border)' }}>
        <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 700 }}>Live Chart: {symbol || 'Select a symbol'}</h3>
        {loading && <span style={{fontSize: 'var(--text-xs)', color: 'var(--text-muted)'}}>Loading...</span>}
      </div>
      {symbol ? (
        <div ref={chartContainerRef} style={{ width: '100%' }} />
      ) : (
        <div style={{ padding: 'var(--space-6)', textAlign: 'center', color: 'var(--text-muted)' }}>
          Please select an active position to view chart
        </div>
      )}
    </div>
  );
};

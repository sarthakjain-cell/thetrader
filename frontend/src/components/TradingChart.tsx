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
        textColor: '#8b949e', // Upstox secondary text
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.03)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.03)' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: 'rgba(255, 255, 255, 0.05)',
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.05)',
      },
      // Give initial height, but we will auto-resize
      height: chartContainerRef.current.clientHeight || 400,
    });
    
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#00c897', downColor: '#e63946', borderVisible: false, // Upstox colors
      wickUpColor: '#00c897', wickDownColor: '#e63946',
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
            color: '#00c897', 
            shape: 'arrowUp', 
            text: `Buy @ ${t.entry_price}`,
            id: `trade_${t.id}`
          });
          
          if (t.exit_time) {
            const exitTimeUnix = new Date(t.exit_time).getTime() / 1000;
            markers.push({ 
              time: findClosestTime(exitTimeUnix), 
              position: 'aboveBar', 
              color: '#e63946', 
              shape: 'arrowDown', 
              text: `Sell @ ${t.exit_price}`,
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
  }, [symbol, trades]);

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: '#12151c' }}>
      <div style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#ffffff', margin: 0 }}>{symbol || 'Select a symbol'}</h3>
        {loading && <span style={{fontSize: '0.8rem', color: '#8b949e'}}>Loading data...</span>}
      </div>
      {symbol ? (
        <div ref={chartContainerRef} style={{ flex: 1, width: '100%' }} />
      ) : (
        <div style={{ padding: '24px', textAlign: 'center', color: '#8b949e' }}>
          Please select an active position to view chart
        </div>
      )}
    </div>
  );
};

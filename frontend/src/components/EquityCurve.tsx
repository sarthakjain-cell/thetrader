import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { useAlgoStream } from '../hooks/useAlgoStream';
import GlassPanel from './GlassPanel';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export const EquityCurve: React.FC = () => {
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    const fetchEquity = async () => {
      try {
        const res = await fetch('http://206.189.129.232:8000/api/equity_history');
        const history = await res.json();
        setData(history);
      } catch (err) {
        console.error("Failed to fetch equity history", err);
      }
    };
    fetchEquity();
    const interval = setInterval(fetchEquity, 60000); // 1 min
    return () => clearInterval(interval);
  }, []);

  if (data.length === 0) {
    return (
      <GlassPanel style={{ padding: 'var(--space-6)', textAlign: 'center', color: 'var(--text-muted)' }}>
        No historical equity data yet.
      </GlassPanel>
    );
  }

  const labels = data.map(d => d.time);
  const equityData = data.map(d => d.equity);
  const drawdownData = data.map(d => d.peak > 0 ? ((d.peak - d.equity) / d.peak) * -100 : 0);

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Equity (₹)',
        data: equityData,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        yAxisID: 'y',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Drawdown (%)',
        data: drawdownData,
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.2)',
        yAxisID: 'y1',
        fill: true,
        tension: 0.1,
      }
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#94a3b8' }
      },
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#94a3b8' }
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        grid: { drawOnChartArea: false },
        ticks: { color: '#ef4444' },
        max: 0,
        min: -15, // Scale drawdown axis to 15% drop
      },
    },
    plugins: {
      legend: { labels: { color: '#f8fafc' } }
    }
  };

  return (
    <GlassPanel style={{ marginBottom: 'var(--space-6)', padding: 'var(--space-4)' }}>
      <h3 style={{ marginBottom: 'var(--space-4)' }}>Equity Curve</h3>
      <div style={{ height: '300px' }}>
        <Line data={chartData} options={options} />
      </div>
    </GlassPanel>
  );
};

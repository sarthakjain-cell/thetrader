import React, { useEffect, useState } from 'react';
import styles from './AIPortfolio.module.css';
import { StrategyPerformance } from '../types';
import { motion } from 'framer-motion';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler
);

interface Position {
  symbol: string;
  qty: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  strategy_id?: string;
}

interface AIPortfolioProps {
  positions: Position[];
  account: any;
  strategies?: StrategyPerformance[];
  onPositionClick?: (symbol: string) => void;
}

export const AIPortfolio: React.FC<AIPortfolioProps> = ({ positions, account, strategies = [], onPositionClick }) => {
  const [equityData, setEquityData] = useState<{ time: string; equity: number }[]>([]);
  const totalPnl = positions.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0);
  const isPositive = totalPnl >= 0;

  useEffect(() => {
    const fetchEquity = async () => {
      try {
        const url = process.env.NEXT_PUBLIC_API_URL 
          ? `${process.env.NEXT_PUBLIC_API_URL}/api/equity_history`
          : 'http://206.189.129.232:8000/api/equity_history';
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          setEquityData(data);
        }
      } catch (e) {
        console.error("Failed to fetch equity history", e);
      }
    };
    fetchEquity();
  }, []);

  const mdd = account?.current_drawdown ? (account.current_drawdown * 100).toFixed(2) : "0.00";
  const totalTrades = strategies.reduce((sum, s) => sum + s.total_trades, 0);
  const totalWins = strategies.reduce((sum, s) => sum + (s.total_trades * s.win_rate), 0);
  const avgWinRate = totalTrades > 0 ? ((totalWins / totalTrades) * 100).toFixed(1) : "0.0";
  const avgProfitFactor = strategies.length > 0 ? 
    (strategies.reduce((sum, s) => sum + s.profit_factor, 0) / strategies.length).toFixed(2) : "0.00";

  let chartLabels = equityData.map(d => d.time.split(' ')[0]);
  let chartValues = equityData.map(d => d.equity);
  
  if (chartValues.length === 0 && account?.equity) {
    chartLabels = ['Start', 'Live'];
    chartValues = [100000, account.equity];
  } else if (account?.equity && chartValues.length > 0) {
    chartLabels.push('Live');
    chartValues.push(account.equity);
  }

  const chartData = {
    labels: chartLabels,
    datasets: [
      {
        label: 'Account Equity (₹)',
        data: chartValues,
        fill: true,
        borderColor: isPositive ? 'rgba(0, 255, 135, 1)' : 'rgba(255, 51, 102, 1)',
        backgroundColor: (context: any) => {
          const ctx = context.chart.ctx;
          const gradient = ctx.createLinearGradient(0, 0, 0, 200);
          if (isPositive) {
            gradient.addColorStop(0, 'rgba(0, 255, 135, 0.4)');
            gradient.addColorStop(1, 'rgba(0, 255, 135, 0.0)');
          } else {
            gradient.addColorStop(0, 'rgba(255, 51, 102, 0.4)');
            gradient.addColorStop(1, 'rgba(255, 51, 102, 0.0)');
          }
          return gradient;
        },
        tension: 0.4,
        pointRadius: 0,
        pointHitRadius: 15,
        borderWidth: 2,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(20, 20, 25, 0.9)',
        titleColor: 'rgba(255, 255, 255, 0.5)',
        bodyColor: '#FFFFFF',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 12,
        boxPadding: 4,
        usePointStyle: true,
      },
    },
    scales: {
      x: { display: false },
      y: { 
        display: false,
        min: chartValues.length > 0 ? Math.min(...chartValues) * 0.99 : 0,
        max: chartValues.length > 0 ? Math.max(...chartValues) * 1.01 : 100,
      },
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false,
    },
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };
  
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className={styles.portfolioContainer}>
      <div className={styles.header}>
        <div className={styles.title}>Multi-Strategy AI Matrix</div>
        <div className={styles.totalPnl}>
          <span className={styles.pnlLabel}>Live Float Returns</span>
          <span className={`${styles.pnlValue} ${isPositive ? styles.positive : styles.negative}`}>
            {isPositive ? '+' : ''}₹{totalPnl.toFixed(2)}
          </span>
        </div>
      </div>

      <div className={styles.sectionTitle} style={{ marginBottom: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <span>Account Equity Curve</span>
        <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)', fontWeight: 'normal', letterSpacing: '0px' }}>
          Visualizes total portfolio balance over time, reflecting realized profits and live paper trading drawdowns.
        </span>
      </div>

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className={styles.chartContainer}
      >
        {chartValues.length > 0 ? (
          <Line data={chartData} options={chartOptions} />
        ) : (
          <div className={styles.emptyChart}>Processing Equity Curve...</div>
        )}
      </motion.div>

      <motion.div 
        variants={containerVariants} initial="hidden" animate="show"
        className={styles.riskMetricsRow}
      >
        <motion.div variants={itemVariants} className={styles.riskCard}>
          <span className={styles.riskLabel}>Max Drawdown</span>
          <span className={styles.riskValue}>{mdd}%</span>
        </motion.div>
        <motion.div variants={itemVariants} className={styles.riskCard}>
          <span className={styles.riskLabel}>Agg. Win Rate</span>
          <span className={styles.riskValue}>{avgWinRate}%</span>
        </motion.div>
        <motion.div variants={itemVariants} className={styles.riskCard}>
          <span className={styles.riskLabel}>Profit Factor</span>
          <span className={styles.riskValue}>{avgProfitFactor}</span>
        </motion.div>
      </motion.div>

      {/* Strategies Leaderboard */}
      <div className={styles.sectionTitle}>Active AI Engines ({strategies.length})</div>
      <motion.div variants={containerVariants} initial="hidden" animate="show" className={styles.strategyList}>
        {strategies.length === 0 ? (
          <motion.div variants={itemVariants} className={styles.emptyState}>
            <div className={styles.boxIcon}>⚙️</div>
            <div className={styles.emptyTitle}>Booting AI Engines...</div>
            <div className={styles.emptyDesc}>The genetic algorithm is synthesizing strategies for today's market conditions.</div>
          </motion.div>
        ) : (
          strategies.map((strat) => (
            <motion.div variants={itemVariants} key={strat.strategy_id} className={styles.strategyCard}>
              <div className={styles.stratHeader}>
                <div className={styles.stratName}>
                  <span className={styles.activeDot}></span>
                  {strat.name}
                </div>
                <div className={`${styles.stratPnl} ${strat.net_pnl >= 0 ? styles.positive : styles.negative}`}>
                  {strat.net_pnl >= 0 ? '+' : ''}₹{strat.net_pnl.toFixed(2)}
                </div>
              </div>
              <div className={styles.stratStats}>
                <div className={styles.statBox}>
                  <div className={styles.statVal}>{strat.total_trades}</div>
                  <div className={styles.statLabel}>Trades</div>
                </div>
                <div className={styles.statBox}>
                  <div className={styles.statVal}>{(strat.win_rate * 100).toFixed(1)}%</div>
                  <div className={styles.statLabel}>Win Rate</div>
                </div>
                <div className={styles.statBox}>
                  <div className={styles.statVal}>{strat.profit_factor.toFixed(2)}</div>
                  <div className={styles.statLabel}>Profit Factor</div>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </motion.div>

      <div className={styles.sectionTitle}>Live Paper Positions</div>
      <motion.div variants={containerVariants} initial="hidden" animate="show" className={styles.listContainer}>
        {positions.length === 0 ? (
          <motion.div variants={itemVariants} className={styles.emptyState}>
            <div className={styles.boxIcon}>🔭</div>
            <div className={styles.emptyTitle}>Scanning Market...</div>
            <div className={styles.emptyDesc}>The AI is waiting for the perfect entry criteria across all active strategies.</div>
          </motion.div>
        ) : (
          positions.map(p => {
            const currentPrice = p.current_price || p.entry_price;
            const uPnl = p.unrealized_pnl || 0;
            const pnlPositive = uPnl >= 0;
            const pnlColorClass = pnlPositive ? styles.positive : styles.negative;
            const pnlArrow = pnlPositive ? '↑' : '↓';

            return (
              <motion.div 
                variants={itemVariants} 
                key={p.symbol} 
                className={styles.row}
                onClick={() => onPositionClick && onPositionClick(p.symbol)}
                style={{ cursor: onPositionClick ? 'pointer' : 'default' }}
              >
                <div className={styles.leftCol}>
                  <div className={styles.symbol}>{p.symbol.split('.')[0]}</div>
                  <div className={styles.qtyInfo}>
                    {p.qty} Qty • Avg ₹{p.entry_price.toFixed(2)}
                    {p.strategy_id && <span className={styles.stratTag}>{p.strategy_id}</span>}
                  </div>
                </div>
                <div className={styles.rightCol}>
                  <div className={styles.ltp}>₹{currentPrice.toFixed(2)}</div>
                  <div className={`${styles.change} ${pnlColorClass}`}>
                    {pnlArrow} ₹{Math.abs(uPnl).toFixed(2)}
                  </div>
                </div>
              </motion.div>
            );
          })
        )}
      </motion.div>
    </div>
  );
};

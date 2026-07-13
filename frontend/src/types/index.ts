export interface AccountInfo {
  equity: number;
  open_positions_value: number;
  current_drawdown: number;
  is_kill_triggered: boolean;
  max_drawdown_limit: number;
}

export interface Position {
  symbol: string;
  entry_price: number;
  current_price: number;
  quantity: number;
  pnl: number;
  unrealized_pnl: number;
}

export interface Trade {
  symbol: string;
  entry_time: string;
  exit_time: string;
  entry_price: number;
  exit_price: number;
  pnl: number;
  notes?: string;
}

export interface ResearchTip {
  symbol: string;
  confidence: 'High' | 'Medium' | 'Low';
  rationale: string;
  score: number;
}

export interface MarketSignal {
  symbol: string;
  last_price: number;
  regime: string;
  signal: 'BUY' | 'SELL' | 'HOLD' | 'VETO';
  rsi: number;
  volume_spike: number;
  adx: number;
  sentiment: number;
  confidence: 'High' | 'Medium' | 'Low';
  ai_prob?: number;
}

export interface AfterHoursLog {
  id: number;
  timestamp: string;
  symbol: string;
  analysis_type: string;
  finding: string;
  confidence: string;
}

export interface PreMarketIntelligence {
  symbol: string;
  date: string;
  support: number;
  resistance: number;
  pattern: string;
  sentiment_trend: string;
  proximity_52w: string;
}

export type ConnectionStatus = 'IDLE' | 'CONNECTING' | 'CONNECTED' | 'RECONNECTING' | 'CLOSED' | 'ERROR';

export interface StrategyPerformance {
  strategy_id: string;
  name: string;
  description: string;
  is_active: number;
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  net_pnl: number;
  max_drawdown: number;
}

export interface DashboardState {
  status: ConnectionStatus;
  market_status: 'OPEN' | 'CLOSED';
  account: AccountInfo | null;
  positions: Position[];
  today_trades: Trade[];
  research_tips: ResearchTip[];
  market_signals: MarketSignal[];
  after_hours_research: AfterHoursLog[];
  pre_market_intelligence: PreMarketIntelligence[];
  strategies: StrategyPerformance[];
  last_updated: number | null; // Timestamp
}

export type StreamAction = 
  | { type: 'CONNECTING' }
  | { type: 'CONNECTED' }
  | { type: 'DISCONNECTED' }
  | { type: 'ERROR', payload: string }
  | { type: 'UPDATE_DATA', payload: any };

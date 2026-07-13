import { useEffect, useReducer, useRef } from 'react';
import { DashboardState, StreamAction } from '../types';

const initialState: DashboardState = {
  status: 'IDLE',
  market_status: 'OPEN',
  account: null,
  positions: [],
  today_trades: [],
  research_tips: [],
  market_signals: [],
  after_hours_research: [],
  pre_market_intelligence: [],
  strategies: [],
  last_updated: null,
};

function streamReducer(state: DashboardState, action: StreamAction): DashboardState {
  switch (action.type) {
    case 'CONNECTING':
      return { ...state, status: 'CONNECTING' };
    case 'CONNECTED':
      return { ...state, status: 'CONNECTED' };
    case 'DISCONNECTED':
      return { ...state, status: state.status === 'CONNECTED' ? 'RECONNECTING' : 'CLOSED' };
    case 'ERROR':
      return { ...state, status: 'ERROR' };
    case 'UPDATE_DATA': {
      const data = action.payload;
      const newState = {
        ...state,
        status: 'CONNECTED' as const,
        market_status: data.market_status || 'OPEN',
        account: data.account ? {
          equity: data.account.equity || 0,
          open_positions_value: 0,
          current_drawdown: data.account.mdd || 0,
          is_kill_triggered: Boolean(data.account.is_halted),
          max_drawdown_limit: 0.1,
        } : null,
        positions: data.positions || [],
        today_trades: data.trades || [],
        research_tips: data.research_tips || [],
        market_signals: data.market_signals || [],
        
        // Append new research items, but if we get a huge dump (e.g. reload), just take it.
        after_hours_research: data.after_hours_research 
          ? [...state.after_hours_research, ...data.after_hours_research].slice(-50) // keep last 50
          : state.after_hours_research,
          
        pre_market_intelligence: data.pre_market_intelligence || state.pre_market_intelligence,
        strategies: data.strategies || [],
        last_updated: Date.now(),
      };
      
      // Persist state
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('algoDashboardState', JSON.stringify(newState));
      }
      return newState;
    }
    default:
      return state;
  }
}

export function useAlgoStream(url: string, addAlert?: (alert: any) => void) {
  const [state, dispatch] = useReducer(streamReducer, initialState, (initial) => {
    // Hydrate from sessionStorage on load
    if (typeof window !== 'undefined') {
      const cached = sessionStorage.getItem('algoDashboardState');
      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          // Set status back to idle/connecting so it doesn't falsely show connected
          return { ...parsed, status: 'CONNECTING' };
        } catch (e) {}
      }
    }
    return initial;
  });

  useEffect(() => {
    let pollingInterval: NodeJS.Timeout;
    let isMounted = true;

    let lastAhId = 0;

    const poll = async () => {
      try {
        // We use fetch instead of EventSource because Android WebView / Capacitor
        // often has native limitations or bugs with long-lived streaming connections.
        // Fetch is robust and we already know it works (via the equity_history endpoint).
        const pollUrl = url.replace('/stream', `/poll?last_ah_id=${lastAhId}`);
        const response = await fetch(pollUrl);
        if (!response.ok) throw new Error('Network response was not ok');
        
        const data = await response.json();
        
        if (isMounted) {
          dispatch({ type: 'UPDATE_DATA', payload: data });
          if (data.after_hours_research && data.after_hours_research.length > 0) {
            lastAhId = data.after_hours_research[data.after_hours_research.length - 1].id;
          }
          if (data.alerts && addAlert) {
            data.alerts.forEach((alert: any) => addAlert(alert));
          }
        }
      } catch (err) {
        if (isMounted) {
          console.error("Polling failed!", err);
          dispatch({ type: 'DISCONNECTED' });
        }
      }
    };

    dispatch({ type: 'CONNECTING' });
    
    // Initial fetch
    poll();
    
    // Poll every 2 seconds
    pollingInterval = setInterval(poll, 2000);

    return () => {
      isMounted = false;
      clearInterval(pollingInterval);
    };
  }, [url]);

  return state;
}

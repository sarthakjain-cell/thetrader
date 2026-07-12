import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'algo.trade.terminal',
  appName: 'AlgoTrade',
  webDir: 'out',
  backgroundColor: '#0b0e14',
  server: {
    androidScheme: 'http',
    cleartext: true
  }
};

export default config;

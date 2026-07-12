export const NIFTY_SECTORS: Record<string, string> = {
  "RELIANCE.NS": "Energy", "ONGC.NS": "Energy", "POWERGRID.NS": "Energy", "NTPC.NS": "Energy", "COALINDIA.NS": "Energy", "BPCL.NS": "Energy",
  "HDFCBANK.NS": "Finance", "ICICIBANK.NS": "Finance", "KOTAKBANK.NS": "Finance", "AXISBANK.NS": "Finance", "SBIN.NS": "Finance", "BAJFINANCE.NS": "Finance", "BAJAJFINSV.NS": "Finance", "INDUSINDBK.NS": "Finance", "HDFCLIFE.NS": "Finance", "SBILIFE.NS": "Finance",
  "TCS.NS": "Tech", "INFY.NS": "Tech", "HCLTECH.NS": "Tech", "WIPRO.NS": "Tech", "TECHM.NS": "Tech", "LTIM.NS": "Tech",
  "ITC.NS": "FMCG", "HINDUNILVR.NS": "FMCG", "NESTLEIND.NS": "FMCG", "TATACONSUM.NS": "FMCG", "BRITANNIA.NS": "FMCG",
  "TATAMOTORS.NS": "Auto", "M&M.NS": "Auto", "MARUTI.NS": "Auto", "BAJAJ-AUTO.NS": "Auto", "EICHERMOT.NS": "Auto", "HEROMOTOCO.NS": "Auto",
  "TATASTEEL.NS": "Metals", "JSWSTEEL.NS": "Metals", "HINDALCO.NS": "Metals",
  "SUNPHARMA.NS": "Pharma", "DRREDDY.NS": "Pharma", "CIPLA.NS": "Pharma", "DIVISLAB.NS": "Pharma", "APOLLOHOSP.NS": "Pharma",
  "LT.NS": "Infra", "ULTRACEMCO.NS": "Infra", "GRASIM.NS": "Infra", "ADANIENT.NS": "Infra", "ADANIPORTS.NS": "Infra",
  "ASIANPAINT.NS": "Consumer", "TITAN.NS": "Consumer",
  "BHARTIARTL.NS": "Telecom"
};

export function getSector(symbol: string): string {
  return NIFTY_SECTORS[symbol] || "Other";
}

export function translateTrend(raw: string): string {
  if (raw === "Bullish") return "AI detects strong upward momentum.";
  if (raw === "Bearish") return "Price action is weak; AI expects further drop.";
  return "Trend is Stable: AI is waiting for a clear breakout direction.";
}

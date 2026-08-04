import pandas as pd

SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS",
    "BHARTIARTL.NS", "ITC.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "TITAN.NS", "HCLTECH.NS", "TATASTEEL.NS", "NTPC.NS", "TATAMOTORS.NS",
    "WIPRO.NS", "ONGC.NS", "POWERGRID.NS", "ULTRACEMCO.NS", "TECHM.NS",
    "M&M.NS", "BAJAJFINSV.NS", "NESTLEIND.NS", "JSWSTEEL.NS", "GRASIM.NS",
    "INDUSINDBK.NS", "CIPLA.NS", "ADANIENT.NS", "ADANIPORTS.NS", "DRREDDY.NS",
    "TATACHEM.NS", "DIVISLAB.NS", "BAJAJ-AUTO.NS", "BRITANNIA.NS", "APOLLOHOSP.NS",
    "EICHERMOT.NS", "COALINDIA.NS", "TATACONSUM.NS", "SHREECEM.NS", "HEROMOTOCO.NS",
    "BPCL.NS", "UPL.NS", "SBILIFE.NS", "HINDALCO.NS"
]

base_symbols = [s.replace(".NS", "") for s in SYMBOLS]

url = "https://images.dhan.co/api-data/api-scrip-master.csv"
try:
    df = pd.read_csv(url, low_memory=False)
    
    # Filter for NSE Equity
    df = df[(df['SEM_EXM_EXCH_ID'] == 'NSE') & (df['SEM_INSTRUMENT_NAME'] == 'EQUITY')]
    
    mapping = {}
    for s in base_symbols:
        match = df[df['SEM_TRADING_SYMBOL'] == s + "-EQ"]
        if match.empty:
            match = df[df['SEM_TRADING_SYMBOL'] == s]
        if match.empty:
            match = df[df['SEM_CUSTOM_SYMBOL'] == s]
            
        if not match.empty:
            mapping[s + ".NS"] = str(match.iloc[0]['SEM_SMST_SECURITY_ID'])
        else:
            print(f"NOT FOUND: {s}")
            
    print("MAPPING = {")
    for k, v in mapping.items():
        print(f'    "{k}": "{v}",')
    print("}")
except Exception as e:
    print(e)

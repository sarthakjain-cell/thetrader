import pandas as pd
df = pd.DataFrame({'Symbol': ['A', 'A', 'B', 'B'], 'Close': [1,2,3,4]})
res = df.groupby('Symbol', group_keys=False).apply(lambda g: g.assign(EMA=g['Close']*2))
print("group_keys=False:", res.columns.tolist())
res2 = df.groupby('Symbol').apply(lambda g: g.assign(EMA=g['Close']*2)).reset_index(drop=True)
print("reset_index(drop=True):", res2.columns.tolist())

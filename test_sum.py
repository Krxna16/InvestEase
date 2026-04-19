import pandas as pd
df = pd.DataFrame(index=pd.date_range("2023-01-01", periods=3))
res = df.sum(axis=1)
print(type(res.index))
print(res)

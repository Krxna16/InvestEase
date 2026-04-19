import pandas as pd
s = pd.Series(dtype=float)
print(type(s.index))
try:
    s.resample('M').prod()
    print("Resampled successfully")
except Exception as e:
    print(f"Error: {e}")

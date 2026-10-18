import sys 
import pandas as pd



df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
df.to_parquet("output.parquet", engine="pyarrow", index=False)
print(df.head())
import pandas as pd

basefile = '4hour.csv'
suppfile = '1min.csv'

df = pd.read_csv(basefile)
print(df)
# Initially fill the offline store with historic data
import pandas as pd
from sqlalchemy import create_engine

df = pd.read_csv('./data/BTCUSD_5.csv', header = None, names = ["unix", "open", "high", "low", "close", "volume", "trades"])
df["unix"] = df["unix"].astype('datetime64[s]')
df["timestamp"] = df["unix"]
df["timestamp_created"] = df["unix"]
df["symbol"] = "BTC/USD"
df.drop(["unix", "volume", "trades"], inplace=True, axis=1)


engine = create_engine('postgresql://feast:feast@offline-store-postgresql.feast.svc.cluster.local:5432/feast')
df.to_sql('crypto_source', engine, index=False)
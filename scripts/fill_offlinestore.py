# Initially fill the offline store with historic data
import pandas as pd
from sqlalchemy import create_engine

df = pd.read_csv('./data/BTC-2021min.csv')
df["unix"] = df["unix"].astype('datetime64[s]')
df["date"] = df["date"].astype('datetime64[s]')
df["timestamp"] = df["unix"]
df["timestamp_created"] = df["unix"]
df.drop(["unix", "date", "Volume BTC", "Volume USD"], inplace=True, axis=1)


engine = create_engine('postgresql://feast:feast@offline-store-postgresql.feast.svc.cluster.local:5432/feast')
df.to_sql('crypto_source', engine, index=False)
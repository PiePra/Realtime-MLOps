from pygments import highlight
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine

st.markdown("# Feature Store")
st.sidebar.markdown("# Feature Store")

features=[
    "crypto_stats:open",
    "crypto_stats:high",
    "crypto_stats:low",
    "crypto_stats:close",
]

st.markdown("Values in feature store as of " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

headers = {"Content-type": "application/json", "Accept": "application/json"}
params = {'features': features, 'entities': {"symbol": ["BTC/USD", "ETH/USD"]},
            'full_feature_names': False}
json_params = json.dumps(params)

r = requests.post("http://feast-feature-server.feast.svc.cluster.local:80/get-online-features/", data=json_params, headers=headers)
r = r.json()
symbol = r["results"][0]["values"]
open= r["results"][1]["values"]
low= r["results"][2]["values"]
close= r["results"][3]["values"]
high = r["results"][4]["values"]
columns = r["metadata"]["feature_names"]
st.markdown("## Online Store")
st.markdown("Currently served feature values")
online = pd.DataFrame(list(zip(symbol, open, low, close, high)), columns=columns)
st.dataframe(online)

st.markdown("## Offline Store")
st.markdown("20 most recent values in offline store")
offline = pd.read_sql("select symbol, open, low, close, high, timestamp from crypto_source order by timestamp desc limit 20;", 
    con = create_engine('postgresql://feast:feast@offline-store-postgresql.feast.svc.cluster.local:5432/feast'))
st.dataframe(offline)
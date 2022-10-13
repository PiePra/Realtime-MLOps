import streamlit as st
import pandas as pd
import ast
import subprocess
import plotly.express as px
from sqlalchemy import create_engine

st.markdown("# Stream Aggregation")
st.sidebar.markdown("# Stream Aggregation")


def run_command(args):
    """Run command, transfer stdout/stderr back into Streamlit and manage error"""
    #st.info(f"Running '{' '.join(args)}'")
    result = subprocess.run(args, capture_output=True, text=True)
    try:
        result.check_returncode()
    except subprocess.CalledProcessError as e:
        raise e
    return result.stdout


events = run_command("/usr/bin/kafkacat -b streaming-system-kafka-0.kafka.svc.cluster.local:9094 -t knative-broker-default-crypto -C -e"
                        .split(" "))
events = events.split("\n")
events_json = []
for event in events[:-1]:
    events_json.append(ast.literal_eval(event))
df = pd.DataFrame(events_json)
df["timestamp"] = df["timestamp"].astype('datetime64[s]')
btc = df[df["symbol"] == "BTC/USD"]
btc.sort_values(by="timestamp", inplace=True)

st.plotly_chart(px.line(btc.iloc[-20:], x="timestamp", y="price", title='Price BTC/USD 1 min') )
st.markdown("# Stream aggregation")
st.markdown("Windows of 5 minutes are aggregated to get open, high, low, close data every 5 minutes")
col1, col2 = st.columns(2)
with col1:
    st.dataframe(btc.iloc[::-1][:10])
with col2:
    aggregated = pd.read_sql("select * from crypto_source where symbol = 'BTC/USD' order by timestamp desc limit 2;", 
        con = create_engine('postgresql://feast:feast@offline-store-postgresql.feast.svc.cluster.local:5432/feast'))
    st.dataframe(aggregated.drop("timestamp_created", axis=1))
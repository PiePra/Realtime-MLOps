import streamlit as st
import pandas as pd
import ast
import subprocess
import plotly.express as px

st.markdown("# Bitcoin")
st.sidebar.markdown("# Bitcoin")


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

st.plotly_chart(px.line(btc, x="timestamp", y="price", title='Price BTC/USD 1 min') )
st.dataframe(btc.iloc[::-1][:10])


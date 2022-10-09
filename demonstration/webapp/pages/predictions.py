import streamlit as st
import subprocess
import pandas as pd
import ast
import numpy as np

def run_command(args):
    """Run command, transfer stdout/stderr back into Streamlit and manage error"""
    result = subprocess.run(args, capture_output=True, text=True)
    try:
        result.check_returncode()
    except subprocess.CalledProcessError as e:
        raise e
    return result.stdout

st.markdown("# Predictions")
st.sidebar.markdown("# Predictions")

events = run_command("/usr/bin/kafkacat -b streaming-system-kafka-0.kafka.svc.cluster.local:9094 -t knative-broker-default-crypto-prediction -C -e"
                        .split(" "))
events = events.split("\n")
events_json = []
for event in events[:-1]:
    events_json.append(ast.literal_eval(event.replace("null", "None")))
df = pd.DataFrame(events_json)
df[["timestamp", "timestamp_created"]] = df[["timestamp", "timestamp_created"]].astype("datetime64[s]")
df = df.iloc[::-1]


st.markdown("## Predict")

try:
    response = df[df["type"] == "response"]
    response = response.drop(["low", "high", "open", "close", "parameters"], axis=1)
    response["outputs"] = response["outputs"].apply(lambda s: np.nan if s is np.nan else s[0]["data"][0])
    response.sort_values(by="timestamp_created", inplace=True)
    st.dataframe(response[["symbol", "type", "outputs", "model_name", "model_version", "timestamp_created", "id"]].iloc[::-1].head(4))
except:
    st.error("No response data yet, wait for prediction")

st.markdown("## Ground Truth")
st.markdown("New event of actual Data added every 5 min to evaluate performance in realtime")
try:
    ground_truth = df[df["type"] == "ground_truth"]
    ground_truth.sort_values(by="timestamp_created", inplace=True)
    ground_truth = ground_truth.drop(["timestamp_created", "open", "high", "low", "model_name", "model_version", "id", "parameters", "outputs"],axis=1)
    st.dataframe(ground_truth[ground_truth["symbol"] == 'BTC/USD'].iloc[::-1].head(4))
except:
    st.error("No ground truth data yet")


import streamlit as st
import subprocess
from cloudevents.http import CloudEvent, to_structured
from datetime import datetime
import requests
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
st.markdown("We demonstrate online Inference on a Kafka Topic. Features are loaded using the online Store")
st.sidebar.markdown("# Predictions")

attributes = {
    "type": "cluster.local.predict_btc",
    "source": "https://cluster.local/dashboard",
}

events = run_command("/usr/bin/kafkacat -b streaming-system-kafka-0.kafka.svc.cluster.local:9094 -t knative-broker-default-crypto-prediction -C -e"
                        .split(" "))
events = events.split("\n")
events_json = []
for event in events[:-1]:
    events_json.append(ast.literal_eval(event.replace("null", "None")))
df = pd.DataFrame(events_json)
df[["timestamp", "timestamp_created"]] = df[["timestamp", "timestamp_created"]].astype("datetime64[s]")
df = df.iloc[::-1]

def post_event():
    event = CloudEvent(attributes, {"symbol": "BTC/USD", "type": "predict", "timestamp": datetime.now().timestamp()})
    headers, body = to_structured(event)
    requests.post("http://kafka-broker-ingress.knative-eventing.svc.cluster.local/default/crypto-prediction", data=body, headers=headers)

st.markdown("## Predict")
st.button("Create BTC Forecast Event!", help="Generates a CloudEvent to Predict", on_click=post_event)

predict = df[df["type"] == "predict"]
predict = predict.drop([ "low", "high", "open", "close", "timestamp_created", "model_name", 
    "model_version", "id", "parameters", "outputs"], axis=1)
st.dataframe(predict.head(1))

st.markdown("## Response")
st.markdown("The model response event")
response = df[df["type"] == "response"]
response = response.drop(["timestamp_created", "low", "high", "open", "close", "parameters"], axis=1)
response["outputs"] = response["outputs"].apply(lambda s: np.nan if s is np.nan else s[0]["data"][0])
st.dataframe(response[["symbol", "type", "outputs", "model_name", "model_version", "id"]].head(1))

st.markdown("## Ground Truth")
st.markdown("New event of actual Data added every 5 min to evaluate performance in realtime")
ground_truth = df[df["type"] == "ground_truth"]
ground_truth = ground_truth.drop(["timestamp_created", "model_name", "model_version", "id", "parameters", "outputs"],axis=1)
st.dataframe(ground_truth[ground_truth["symbol"] == 'BTC/USD'].head(3))


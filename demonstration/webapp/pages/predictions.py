from sqlalchemy import null
import streamlit as st
import subprocess
from cloudevents.http import CloudEvent, to_structured
from datetime import datetime
import requests
import pandas as pd
import ast

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

attributes = {
    "type": "cluster.local.predict_btc",
    "source": "https://cluster.local/dashboard",
}

if st.button("Create BTC Forecast Event!", help="Generates a CloudEvent to Predict", ):
    event = CloudEvent(attributes, {"symbol": "BTC/USD", "type": "predict", "timestamp": datetime.now().timestamp()})
    headers, body = to_structured(event)
    requests.post("http://kafka-broker-ingress.knative-eventing.svc.cluster.local/default/crypto-prediction", data=body, headers=headers)

events = run_command("/usr/bin/kafkacat -b streaming-system-kafka-0.kafka.svc.cluster.local:9094 -t knative-broker-default-crypto-prediction -C -e"
                        .split(" "))
events = events.split("\n")
events_json = []
for event in events[:-1]:
    events_json.append(ast.literal_eval(event.replace("null", "None")))
df = pd.DataFrame(events_json)
df = df.drop(["parameters", "low", "open", "high", "id", "model_version"], axis=1)
df[["timestamp", "timestamp_created"]] = df[["timestamp", "timestamp_created"]].astype("datetime64[s]")
btc = df[df["symbol"] == "BTC/USD"]
st.dataframe(btc.iloc[::-1][:6])


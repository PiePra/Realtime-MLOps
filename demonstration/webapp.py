import streamlit as st
import pandas as pd
from cloudevents.http import CloudEvent
from cloudevents.conversion import to_structured
import requests


attributes = {
    "type": "cluster.local.predict_btc",
    "source": "https://cluster.local/dashboard",
}


def btc_button_callback():
    event = CloudEvent(attributes, {"symbol": "BTC/USD", "action": "predict"})
    headers, body = to_structured(event)
    requests.post("http://kafka-broker-ingress.knative-eventing.svc.cluster.local/default/crypto-prediction", data=body, headers=headers)
    st.json(body.decode(),  expanded=True)


st.button("Create BTC Forecast Event!", help="Generates a CloudEvent to Predict", on_click=btc_button_callback )


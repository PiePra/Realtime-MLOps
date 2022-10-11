import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, mean_absolute_error, r2_score
from cloudevents.http import CloudEvent, to_structured
import requests
from datetime import datetime
import plotly.express as px

def metrics_dict(y, y_hat):
    metrics = {
        "RMSE": round(mean_squared_error(y, y_hat, squared=False), 2),
        "MAPE": round(mean_absolute_percentage_error(y, y_hat) * 100, 2),
        "MAE": round(mean_absolute_error(y, y_hat), 2),
        "R2": round(r2_score(y, y_hat), 2),
    }
    return metrics

attributes = {
    "type": "cluster.local.model_retrain",
    "source": "https://cluster.local/dashboard",
}

def post_event(mode):
    event = CloudEvent(attributes, {"type": "model_retrain", "mode": mode, "timestamp": datetime.utcnow().timestamp()})
    headers, body = to_structured(event)
    requests.post("http://kafka-broker-ingress.knative-eventing.svc.cluster.local/default/ml-training", data=body, headers=headers)
    st.write("Created event:")
    st.info(body)

st.markdown("# Metrics")
st.sidebar.markdown("# Metrics")
st.markdown("Metrics over last 5 predictions")

try:
    metrics = pd.read_sql("select * from metrics;", 
        con = create_engine('postgresql://feast:feast@offline-store-postgresql.feast.svc.cluster.local:5432/feast'))
    col1, col2, col3, col4 = st.columns(4)
    if len(metrics) > 4:
        metrics_now = metrics.iloc[-5:]
        metrics_past = metrics.iloc[-6:-1]
    elif len(metrics) >=2: 
        metrics_now = metrics
        metrics_past = metrics.iloc[:-1]
    else:
        metrics_now = metrics
        metrics_past = metrics


    now = metrics_dict(metrics_now["y"], metrics_now["y_hat"])
    past = metrics_dict(metrics_past["y"], metrics_past["y_hat"])

    #substract two dicts
    res = {key: round(now[key] - past.get(key, 0), 2)
                        for key in now.keys()}

    col1.metric("RMSE", now["RMSE"], res["RMSE"], delta_color="inverse")
    col2.metric("MAPE", str(now["MAPE"]) + "%" , str(res["MAPE"]) + "%", delta_color="inverse" )
    col3.metric("MAE", now["MAE"], res["MAE"], delta_color="inverse")
    col4.metric("R²",  now["R2"], res["R2"], delta_color="normal" if now["R2"]<0 else "inverse")
    metrics["timestamp"] = metrics["timestamp"].astype('datetime64[s]')
    st.dataframe(metrics.iloc[::-1])
    
except:
    st.error("No metrics data available yet")
st.plotly_chart(px.line(metrics.iloc[-40:], x="timestamp", y="diff", title='Diff over time') )
# st.markdown("## Model retraining")
# col1, col2 = st.columns(2)
# with col1:
#     if st.button("Start stateful training!", help="Generates a CloudEvent to do stateful retraining"):
#         post_event("stateful")

# with col2:
#     if st.button("Start stateless training!", help="Generates a CloudEvent to do full retraining"):
#         post_event("stateless")

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


def post_message():
    r = requests.post("http://el-stateless-fit.default.svc.cluster.local:8080", json={})
    st.write("Created run:")
    st.info(r.json())

st.markdown("# Metrics")
st.sidebar.markdown("# Metrics")
st.markdown("Metrics over last 10 predictions")
col1, col2, col3, col4, col5 = st.columns(5)
try:
    metrics = pd.read_sql("select * from metrics;", 
        con = create_engine('postgresql://feast:feast@offline-store-postgresql.feast.svc.cluster.local:5432/feast'))

    if len(metrics) > 4:
        metrics_now = metrics.iloc[-10:]
        metrics_past = metrics.iloc[-11:-1]
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

    metrics["timestamp"] = metrics["timestamp"].astype('datetime64[s]')
    metrics["delta_y"] = metrics["y"] - metrics["y"].shift(1)
    metrics["delta_y_hat"] = metrics["y_hat"] - metrics["y"].shift(1)
    metrics["trend_y"] = metrics["delta_y"].apply(lambda x: True if x > 0 else False )
    metrics["trend_y_hat"] = metrics["delta_y_hat"].apply(lambda x: True if x > 0 else False )
    metrics["accurate"] = metrics["trend_y"] == metrics["trend_y_hat"]
    try:
        accuracy = metrics["accurate"].iloc[-10:].value_counts(True)[True]
    except:
        accuracy = 0
    try:
        accuracy_past = metrics["accurate"].iloc[-11:-1].value_counts(True)[True]
    except:
        accuracy_past = 0
    col1.metric("RMSE", now["RMSE"], res["RMSE"], delta_color="inverse")
    col2.metric("MAPE", str(now["MAPE"]) + "%" , str(res["MAPE"]) + "%", delta_color="inverse" )
    col3.metric("MAE", now["MAE"], res["MAE"], delta_color="inverse")
    col4.metric("R²",  now["R2"], res["R2"], delta_color="normal" if now["R2"]<0 else "inverse")
    col5.metric("Acc", str(accuracy * 100) + "%", str(round((accuracy - accuracy_past) * 100, 1)) + "%" )
    
except Exception as e:
    st.write(e)
    st.error("No metrics data available yet")

st.plotly_chart(px.line(metrics.iloc[-40:], x="timestamp", y="diff", title='Diff over time') )
st.markdown("## Model retraining")
if st.button("Start stateless training!", help="Triggers a steteless training on last 150 observations"):
    post_message()

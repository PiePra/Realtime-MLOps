import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

st.markdown("# Metrics")
st.sidebar.markdown("# Metrics")

offline = pd.read_sql("select * from metrics limit 20;", 
    con = create_engine('postgresql://feast:feast@offline-store-postgresql.feast.svc.cluster.local:5432/feast'))
st.dataframe(offline)
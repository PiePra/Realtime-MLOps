from datetime import timedelta

from feast import (
    Entity,
    FeatureService,
    FeatureView,
    Field,
    PushSource,
)

from feast.types import Float32, Float64
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import (
    PostgreSQLSource,
)
from feast.on_demand_feature_view import on_demand_feature_view
from ta.momentum import RSIIndicator,StochasticOscillator
import pandas as pd

# Define an entity for the driver. You can think of an entity as a primary key used to
# fetch features.
crypto = Entity(name="crypto", join_keys=["symbol"])

# Read data from parquet files. Parquet is convenient for local development mode. For
# production, you can use your favorite DWH, such as BigQuery. See Feast documentation
# for more info.

crypto_source = PostgreSQLSource(
    name="crypto_source",
    query="SELECT * FROM crypto_source",
    timestamp_field="timestamp",
    created_timestamp_column="timestamp_created"
)


# Our parquet files contain sample data that includes a driver_id column, timestamps and
# three feature column. Here we define a Feature View that will allow us to serve this
# data to our model online.
crypto_fv = FeatureView(
    # The unique name of this feature view. Two feature views in a single
    # project cannot have the same name
    name="crypto_stats",
    entities=[crypto],
    ttl=timedelta(hours=24),
    # The list of features defined below act as a schema to both define features
    # for both materialization of features into a store, and are used as references
    # during retrieval for building a training dataset or serving features
    schema=[
        Field(name="open", dtype=Float32),
        Field(name="high", dtype=Float32),
        Field(name="low", dtype=Float32),
        Field(name="close", dtype=Float32),
    ],
    online=True,
    source=crypto_source,
    # Tags are user defined key/value pairs that are attached to each
    # feature view
    tags={"team": "crypto"},
)


crypto_sv = FeatureService(
    name="crypto_stats", features=[crypto_fv])

# Defines a way to push data (to be available offline, online or both) into Feast.
crypto_push_source = PushSource(
    name="crypto_push_source",
    batch_source=crypto_source,
)


@on_demand_feature_view(sources=[crypto_fv],
    schema=[
        Field(name='ema_9', dtype=Float64),
        Field(name='sma_5', dtype=Float64),
        Field(name='sma_20', dtype=Float64),
        Field(name='macd', dtype=Float64),
        Field(name='rsi', dtype=Float64),
        Field(name='stochastic', dtype=Float64),
   ],
)
def technical_indicators(features_df: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame()
    df['ema_9'] = features_df['close'].ewm(9).mean() # exponential moving average of window 9
    df['sma_5'] = features_df['close'].rolling(5).mean() # moving average of window 5
    df['sma_20'] = features_df['close'].rolling(20).mean() # moving average of window 20
    EMA_12 = pd.Series(features_df['close'].ewm(span=12, min_periods=12).mean())
    EMA_26 = pd.Series(features_df['close'].ewm(span=26, min_periods=26).mean())
    df['macd'] = pd.Series(EMA_12 - EMA_26)    # calculates Moving Average Convergence Divergence
    df['rsi'] = RSIIndicator(features_df['close']).rsi() # calculates Relative Strength Index 
    df['stochastic']=StochasticOscillator(features_df['high'],features_df['low'],features_df['close']).stoch()
    return df
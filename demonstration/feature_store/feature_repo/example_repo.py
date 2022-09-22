from datetime import timedelta

from feast import (
    Entity,
    FeatureService,
    FeatureView,
    Field,
    PushSource,
)
from feast.types import Float32
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import (
    PostgreSQLSource,
)

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

#crypto_source = FileSource(
#    name="crypto_source",
#    path="/home/pierre/Realtime-MLOps/demonstration/apps/feature_store/feature_repo/data/BTC-2021min.parquet",
#    timestamp_field="timestamp",
#    created_timestamp_column="timestamp_created",
#)

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

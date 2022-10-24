import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Tuple

import pandas as pd
import requests
import sqlalchemy
from bytewax.dataflow import Dataflow
from bytewax.execution import run_main
from bytewax.inputs import KafkaInputConfig
from bytewax.outputs import ManualOutputConfig
from bytewax.window import SystemClockConfig, TumblingWindowConfig
from cloudevents.conversion import to_structured
from cloudevents.http import CloudEvent
from feast import FeatureStore
from sqlalchemy import create_engine

#Kafka Input
KAFKA_BOOTSTRAP_SERVERS=["streaming-system-kafka-0.kafka.svc.cluster.local:9094"]
KAFKA_TOPIC="knative-broker-default-crypto"

#Feast Config
FEAST_PATH="./platform/feature-store/feature_store/feature_repo/"
FEAST_FEATURE_VIEW="crypto_stats"
FEAST_SOURCE_TABLE="crypto_source"

#Feast Offline Store
DB_TYPE="postgresql"
PG_USER="feast"
PG_PASS="feast"
PG_HOST="offline-store-postgresql.feast.svc.cluster.local"
PG_PORT="5432"
PG_DB="feast"

#Output Broker Ingress
KAFKA_BROKER_INGRESS="http://kafka-broker-ingress.knative-eventing.svc.cluster.local/default/crypto-prediction"

#CloudEvent Attributes
CE_ATTR_TYPE="cluster.local.aggregated_"
CE_ATTR_SOURCE="https://cluster.local/dataflow"

@dataclass
class OHLC:
    """Class representing output Feature Vector"""
    symbol: str
    open: float
    high: float
    low: float
    close: float
    timestamp_created: datetime
    timestamp: datetime = field(default=datetime.utcnow().timestamp())


def get_message(msg: Tuple[str, Tuple]) -> Tuple[str, Tuple]:
    """Formats msg to use symbol as key and content as tuple"""
    key, val = msg
    key = json.loads(val) 
    msg = key
    yield msg["symbol"], (msg["price"], msg["timestamp"])  

def append_price(prices: list, price: Tuple):
    """Appends price to list of prices"""
    prices.append(price)
    return prices

def get_vals(msg: Tuple[str, Tuple]) -> list:
    """"Get OHLC Data from prices"""
    key, msg = msg
    prices = [item[0] for item in msg]
    timestamps = [item[1] for item in msg]

    output = OHLC(
        symbol=key,
        low=min(prices),
        high=max(prices),
        open=prices[0],
        close=prices[-1],
        timestamp_created=timestamps[-1]
    )
    return output

def get_engine() -> sqlalchemy.engine.Engine:
    """Create DB Connection Engine"""
    return create_engine(f"{DB_TYPE}://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}")

def get_feature_store() -> FeatureStore:
    """Create Feature Store Object"""
    return FeatureStore(FEAST_PATH)

def get_cloudevent(data: OHLC) -> CloudEvent:
    """Create the Cloudevent from attributes and data"""
    attributes = {
        "type": f"{CE_ATTR_TYPE}_",
        "source": CE_ATTR_SOURCE,
    }
    event = data.__dict__
    event["type"]="ground_truth"
    return CloudEvent(attributes, event)

def get_df(data: OHLC) -> pd.DataFrame:
    """Create pandas dataframe to send to feast"""
    item = data.__dict__
    for key in item.keys():
        item[key] = [item[key]]
    df = pd.DataFrame(item)
    df["timestamp"] = df["timestamp"].astype('datetime64[s]')
    df["timestamp_created"] = df["timestamp_created"].astype('datetime64[s]')
    return df

def output_builder(worker_index: int, worker_count: int) -> callable:
    """Build the function to write to feast"""
    engine = get_engine()
    store = get_feature_store()
    def write(item: OHLC):
        df = get_df(item)
        # Write to online store
        store.write_to_online_store(FEAST_FEATURE_VIEW, df)
        # Post Event to Broker Ingress
        event = get_cloudevent(item)
        headers, body = to_structured(event)
        requests.post(KAFKA_BROKER_INGRESS, data=body, headers=headers)
        # Write offline store (directly to sql table as write_to_offline_store not implemented for postgresql yet)
        df.to_sql(FEAST_SOURCE_TABLE, engine, if_exists='append', index=False)
    return write

def run_dataflow() -> None:
    cc = SystemClockConfig()
    #cc = TestingClockConfig(start_at=datetime(2022, 1, 1, 13), item_incr = timedelta(minutes=1))
    wc = TumblingWindowConfig(length=timedelta(minutes=5))
    input_config = KafkaInputConfig(KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC, tail=True, starting_offset="end")
    flow = Dataflow()
    flow.input("input", input_config)
    flow.flat_map(get_message)
    flow.fold_window("session_state_recovery", cc, wc, list, append_price)
    flow.map(get_vals)
    flow.capture(ManualOutputConfig(output_builder))
    run_main(flow)

if __name__ == "__main__":
    run_dataflow()

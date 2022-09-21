import json
from datetime import datetime, timedelta
import logging
import pandas as pd
from sqlalchemy import create_engine
from bytewax.dataflow import Dataflow
from bytewax.execution import run_main
from bytewax.inputs import KafkaInputConfig, TestingInputConfig
from bytewax.outputs import StdOutputConfig, ManualOutputConfig
from bytewax.window import (SystemClockConfig, TumblingWindowConfig, TestingClockConfig)
from feast import FeatureStore
from bytewax.window import ClockConfig

def get_message(msg):
    key, val = msg
    key = json.loads(val) 
    msg = key
    yield ("btc", (msg["price"], msg["timestamp"]))  

def append_price(prices, price):
    prices.append(price)
    return prices

def get_vals(msg):
    key, msg = msg
    prices = [item[0] for item in msg]
    timestamps = [item[1] for item in msg]

    output = pd.DataFrame([{
        "symbol": "BTC/USD",
        "low": min(prices),
        "high": max(prices),
        "open": prices[0],
        "close": prices[-1],
        "timestamp": datetime.now().timestamp(),
        "timestamp_created": timestamps[-1]
    }])
    output["timestamp"] = output["timestamp"].astype('datetime64[s]')
    output["timestamp_created"] = output["timestamp_created"].astype('datetime64[s]')
    return output

def output_builder(worker_index, worker_count):
    store = FeatureStore('.')
    engine = create_engine('postgresql://feast:feast@offline-store-postgresql.feast.svc.cluster.local:5432/feast')
    def write(item):
        store.write_to_online_store("crypto_stats", item, allow_registry_cache = True)
        # Write to offline store for posotgres not implemented in feast 0.25 yet
        #store.write_to_offline_store("crypto_stats", item, allow_registry_cache = True)
        item.to_sql("crypto_source", engine, if_exists='append', index=False)
        logging.info(f"worker {worker_index} created - {item}")
    return write


if __name__ == "__main__":
    cc = TestingClockConfig(start_at=datetime(2022, 1, 1, 13), item_incr = timedelta(minutes=1))
    cc = SystemClockConfig()
    wc = TumblingWindowConfig(length=timedelta(minutes=5))
    input_config = KafkaInputConfig(["streaming-system-kafka-0.kafka.svc.cluster.local:9094"], "knative-broker-default-btc", tail=True, starting_offset="end")
    flow = Dataflow()
    flow.input("input", input_config)
    flow.flat_map(get_message)
    flow.fold_window("session_state_recovery", cc, wc, list, append_price)
    flow.map(get_vals)
    flow.capture(ManualOutputConfig(output_builder))
    run_main(flow)

import json
from datetime import datetime, timedelta
import logging

from bytewax.dataflow import Dataflow
from bytewax.execution import run_main
from bytewax.inputs import KafkaInputConfig, TestingInputConfig
from bytewax.outputs import StdOutputConfig, ManualOutputConfig
from bytewax.window import (SystemClockConfig, TumblingWindowConfig, TestingClockConfig)
from feast import FeatureStore


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

    output = {
        "symbol": "BTC/USD",
        "low": min(prices),
        "high": max(prices),
        "open": prices[0],
        "close": prices[-1],
        "timestamp": datetime.now().timestamp(),
        "timestamp_created": timestamps[-1]
    }
    return output

def output_builder(worker_index, worker_count):
    store = FeatureStore()
    def write(item):
        store.write_to_online_store("crypto_stats", item, allow_registry_cache = True)
        store.write_to_offline_store("crypto_stats", item, allow_registry_cache = True, reorder_columns = True)
        logging.info(f"worker {worker_index} created - {item}")
    return write


if __name__ == "__main__":
    cc = TestingClockConfig(start_at=datetime(2022, 1, 1, 13), item_incr = timedelta(minutes=1))
    wc = TumblingWindowConfig(length=timedelta(minutes=5))

    input_config = KafkaInputConfig(["streaming-system-kafka-0.kafka.svc.cluster.local:9094"], "knative-broker-default-btc", tail=True, starting_offset="beginning")
    flow = Dataflow()
    flow.input("input", input_config)
    flow.flat_map(get_message)
    flow.fold_window("session_state_recovery", cc, wc, list, append_price)
    flow.map(get_vals)
    flow.capture(ManualOutputConfig(output_builder))
    run_main(flow)

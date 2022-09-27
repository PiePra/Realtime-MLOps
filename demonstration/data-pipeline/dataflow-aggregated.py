import json
from datetime import datetime, timedelta
import logging
from bytewax.dataflow import Dataflow
from bytewax.execution import run_main
from bytewax.inputs import KafkaInputConfig
from bytewax.outputs import ManualOutputConfig, StdOutputConfig
from bytewax.window import SystemClockConfig, TumblingWindowConfig, TestingClockConfig
from cloudevents.http import CloudEvent
from cloudevents.conversion import to_structured
import requests
import pandas as pd
from sqlalchemy import create_engine

def get_message(msg):
    key, val = msg
    key = json.loads(val) 
    msg = key
    yield msg["symbol"], (msg["price"], msg["timestamp"])  

def append_price(prices, price):
    prices.append(price)
    return prices

def get_vals(msg):
    key, msg = msg
    prices = [item[0] for item in msg]
    timestamps = [item[1] for item in msg]

    output = {
        "symbol": key,
        "low": min(prices),
        "high": max(prices),
        "open": prices[0],
        "close": prices[-1],
        "timestamp": datetime.now().timestamp(),
        "timestamp_created": timestamps[-1]
    }
    return output

def output_builder(worker_index, worker_count):
    engine = create_engine('postgresql://feast:feast@offline-store-postgresql.feast.svc.cluster.local:5432/feast')
    def write(item):
        attributes = {
            "type": f"cluster.local.aggregated_{item['symbol']}",
            "source": "https://cluster.local/dataflow",
        }
        event = item
        event["type"] = "ground_truth"
        event = CloudEvent(attributes, event)
        headers, body = to_structured(event)
        requests.post("http://kafka-broker-ingress.knative-eventing.svc.cluster.local/default/crypto-prediction", data=body, headers=headers)
        logging.info(f"worker {worker_index} created - {item}")
        push_data = {
            "push_source_name": "crypto_push_source",
            "df": item,
            "to": "online_and_offline",
        }
        requests.post("http://feast-feature-server.feast.svc.cluster.local:80/push", json=push_data)
        logging.info(f"worker {worker_index} pushed to online store - {item['timestamp_created']}")
        # We have to write directly to postgres because write offline store not implemented for postgres yet
        df = pd.DataFrame([item])
        df["timestamp"] = df["timestamp"].astype('datetime64[s]')
        df["timestamp_created"] = df["timestamp_created"].astype('datetime64[s]')
        df.to_sql("crypto_source", engine, if_exists='append', index=False)
        logging.info(f"worker {worker_index} pushed to offlone store - {item['timestamp_created']}")
    return write


if __name__ == "__main__":
    cc = SystemClockConfig()
    #cc = TestingClockConfig(start_at=datetime(2022, 1, 1, 13), item_incr = timedelta(minutes=1))
    wc = TumblingWindowConfig(length=timedelta(minutes=5))
    input_config = KafkaInputConfig(["streaming-system-kafka-0.kafka.svc.cluster.local:9094"], "knative-broker-default-crypto", tail=True, starting_offset="end")
    flow = Dataflow()
    flow.input("input", input_config)
    flow.flat_map(get_message)
    flow.fold_window("session_state_recovery", cc, wc, list, append_price)
    flow.map(get_vals)
    flow.capture(ManualOutputConfig(output_builder))
    run_main(flow)
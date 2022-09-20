from distutils import ccompiler
import json
import operator
from datetime import datetime, timedelta

from bytewax.dataflow import Dataflow
from bytewax.execution import run_main
from bytewax.inputs import KafkaInputConfig, TestingInputConfig
from bytewax.outputs import StdOutputConfig
from bytewax.window import (SystemClockConfig, TumblingWindowConfig, TestingClockConfig)


def get_message(msg):
    key, val = msg
    key = json.loads(val) 
    msg = key
    yield ("btc", msg["price"]) 

def append_price(prices, price):
    prices.append(price)
    return prices

def get_vals(msg):
    key, prices = msg
    return prices[0], prices[-1], max(prices), min(prices)




if __name__ == "__main__":
    cc = TestingClockConfig(start_at=datetime(2022, 1, 1, 13), item_incr = timedelta(minutes=1))
    wc = TumblingWindowConfig(length=timedelta(minutes=5))

    input_config = KafkaInputConfig(["streaming-system-kafka-0.kafka.svc.cluster.local:9094"], "knative-broker-default-btc", tail=True, starting_offset="beginning")
    flow = Dataflow()
    flow.input("input", input_config)
    flow.flat_map(get_message)
    flow.fold_window("session_state_recovery", cc, wc, list, append_price)
    flow.map(get_vals)
    flow.capture(StdOutputConfig())
    run_main(flow)

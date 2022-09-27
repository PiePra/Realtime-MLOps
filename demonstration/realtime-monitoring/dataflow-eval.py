from datetime import timedelta
import logging
from bytewax.dataflow import Dataflow
from bytewax.execution import run_main
from bytewax.inputs import TestingInputConfig
from bytewax.outputs import ManualOutputConfig, StdOutputConfig
from bytewax.window import SystemClockConfig, TumblingWindowConfig, TestingClockConfig

events = [
    {"symbol":"ETH/USD", "type": "ground_truth", "close": 2}, #"low":1298.92,"high":1302.01,"open":1298.92,"close":1301.72,"timestamp":1.663938349891634E9,"timestamp_created":1.663938282346164E9},
    {"symbol":"BTC/USD", "type": "ground_truth", "close": 2}, #"low":18899.25,"high":18962.24,"open":18899.25,"close":18962.24,"timestamp":1.663938349891649E9,"timestamp_created":1.663938282722775E9},
    {"symbol":"BTC/USD", "type": "infer"},
    {"symbol":"BTC/USD", "type": "response", "price": 1, "outputs":[{"name":"predict","shape":[1,1],"datatype":"FP32","parameters":None,"data":[19286.939453125]}]}, #"model_name": "bitcoin-forecast", "model_version": None, "id": "4c525f3b-0f0c-4988-b41c-afa974b99240", "parameters": None, "outputs": [{"name": "predict", "shape": [1, 1], "datatype": "FP32", "parameters": None, "data": [19286.939453125]}]},
    {"symbol":"ETH/USD", "type": "ground_truth", "close": 2}, #"low":1310.02,"high":1311.8,"open":1310.14,"close":1311.8,"timestamp":1.663939033477638E9,"timestamp_created":1.663939011822367E9},
    {"symbol":"BTC/USD", "type": "ground_truth", "close": 2}, #"low":19002.62,"high":19045.29,"open":19002.62,"close":19045.29,"timestamp":1.663939333477632E9,"timestamp_created":1.663939315750054E9},
    {"symbol":"BTC/USD", "type": "infer"},
    {"symbol":"BTC/USD", "type": "response", "price": 1, "outputs":[{"name":"predict","shape":[1,1],"datatype":"FP32","parameters":None,"data":[19286.939453125]}]},     #"model_name":"bitcoin-forecast","model_version":None,"id":"4c525f3b-0f0c-4988-b41c-afa974b99240","parameters":None,]},
    {"symbol":"BTC/USD", "type": "infer"},
    {"symbol":"BTC/USD", "type": "response", "price": 1, "outputs":[{"name":"predict","shape":[1,1],"datatype":"FP32","parameters":None,"data":[19286.939453125]}]}, 
    {"symbol":"BTC/USD", "type": "ground_truth", "close": 2}, #"low":19002.62,"high":19045.29,"open":19002.62,"close":19045.29,"timestamp":1.663939333477632E9,"timestamp_created":1.663939315750054E9},
]


def get_message(msg):
    yield (msg["symbol"], [msg])

def extend_session(session, events):
    session.extend(events)
    return session

def session_complete(session):
    return any(event["type"] == "ground_truth" for event in session)

def get_metric(session):
    key, msg = session
    if len(msg) > 1:
        y = msg[-1]["close"]
        symbol = msg[-1]["symbol"]
        out = {"type": "eval",
        "symbol": symbol,
        "y": [],
        "y_hat": [],
        "diff": [],}
        for line in msg:
            if line["type"] == "response":
                y_hat = line["outputs"][0]["data"][0]
                out["y_hat"].append(y_hat)
                out["y"].append(y)
                diff = y - y_hat
                if diff > 0:
                    out["diff"].append(diff)
                else:
                    out["diff"].append(y_hat)
        return(out) 

if __name__ == "__main__":
    cc = SystemClockConfig()
    #cc = TestingClockConfig(start_at=datetime(2022, 1, 1, 13), item_incr = timedelta(minutes=1))
    wc = TumblingWindowConfig(length=timedelta(minutes=5))
    input_config = TestingInputConfig(events)
    #input_config = KafkaInputConfig(["streaming-system-kafka-0.kafka.svc.cluster.local:9094"], "knative-broker-default-crypto", tail=True, starting_offset="end")
    flow = Dataflow()
    flow.input("input", input_config)
    flow.flat_map(get_message)
    flow.reduce("sessionizer", extend_session, session_complete)
    flow.map(get_metric)
    flow.capture(StdOutputConfig())
    run_main(flow)
from bytewax.dataflow import Dataflow
from bytewax.execution import run_main
from bytewax.inputs import KafkaInputConfig
from bytewax.outputs import ManualOutputConfig, StdOutputConfig
import pandas as pd
from sqlalchemy import create_engine
import json
from datetime import datetime

def get_message(msg):
    key, val = msg
    val = json.loads(val) 
    yield (val["symbol"], [val])

def extend_session(session, events):
    session.extend(events)
    return session

def session_complete(session):
    return any(event["type"] == "ground_truth" for event in session)

def get_metric(session):
    key, msg = session
    out = []
    if len(msg) > 1:
        y = msg[-1]["close"]
        symbol = msg[-1]["symbol"]
        for line in msg:
            if line["type"] == "response":
                y_hat = line["outputs"][0]["data"][0]
                diff = y - y_hat
                if diff < 0:
                    diff = diff * -1
                temp = {"type": "eval",
                "symbol": symbol,
                "y": y,
                "y_hat": y_hat,
                "diff": diff,
                "model_name": line["model_name"],
                "model_version": line["model_version"],
                "timestamp": datetime.now().timestamp()
                }
                out.append(temp)
    return(out)

def output(worker_index, worker_count):
    engine = create_engine('postgresql://feast:feast@offline-store-postgresql.feast.svc.cluster.local:5432/feast')
    def write(item):
        df = pd.DataFrame([item])
        df.to_sql("metrics", engine, if_exists='append', index=False)

    return write

if __name__ == "__main__":
    input_config = KafkaInputConfig(["streaming-system-kafka-0.kafka.svc.cluster.local:9094"], "knative-broker-default-crypto-prediction", tail=True, starting_offset="end")
    flow = Dataflow()
    flow.input("input", input_config)
    flow.flat_map(get_message)
    flow.reduce("sessionizer", extend_session, session_complete)
    flow.map(get_metric)
    flow.flat_map(lambda s: s)
    flow.capture(ManualOutputConfig(output))
    run_main(flow)
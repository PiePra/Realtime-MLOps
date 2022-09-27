from bytewax.dataflow import Dataflow
from bytewax.inputs import TestingInputConfig
from bytewax.outputs import StdOutputConfig
from bytewax.execution import run_main



inp = [
    {"user": "a", "type": "login"},
    {"user": "a", "type": "post"},
    {"user": "b", "type": "login"},
    {"user": "b", "type": "logout"},
    {"user": "a", "type": "logout"},
]


def user_as_key(event):
    return event["user"], [event]

def extend_session(session, events):
    session.extend(events)
    return session

def session_complete(session):
    return any(event["type"] == "logout" for event in session)


flow = Dataflow()
flow.input("inp", TestingInputConfig(inp))
flow.map(user_as_key)
flow.reduce("sessionizer", extend_session, session_complete)
flow.capture(StdOutputConfig())
run_main(flow)
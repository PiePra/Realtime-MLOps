import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict

import requests
from cloudevents.conversion import to_structured
from cloudevents.http import CloudEvent

#API Config
API_URL="https://api.binance.com/api/v3/ticker/price"
API_QUERY="symbol"

#CloudEvent Attributes
CE_ATTR_TYPE="cluster.local.crypto_price"
CE_ATTR_SOURCE="https://cluster.local/crypto_price"

#Knative Attributes
KNATIVE_BROKER_INGRESS="http://kafka-broker-ingress.knative-eventing.svc.cluster.local/default/crypto"

def get_cloudevent(data: Dict) -> CloudEvent:
    """Create a CloudEvent from a dict"""
    attributes = {
        "type": CE_ATTR_TYPE,
        "source": CE_ATTR_SOURCE,}
    return CloudEvent(attributes, data)

def post_event(event: CloudEvent) -> None:
    """Post a CloudEvent to the Broker Ingress"""
    headers, body = to_structured(event)
    requests.post(KNATIVE_BROKER_INGRESS, data=body, headers=headers)

def format_ticker(ticker: str) -> str:
    """Format Ticker according to Binance API"""
    return ticker.replace("/","") + "T"

def get_ticker(ticker: str) -> None:
    """Query API to get price data"""
    formatted_ticker = format_ticker(ticker)
    r = requests.get(f'{API_URL}?{API_QUERY}={formatted_ticker}')
    if r.status_code != 200:
        return
    price = float(r.json()['price'])
    price_data = {"price": price, "timestamp": datetime.utcnow().timestamp(), "symbol": ticker}
    event = get_cloudevent(price_data)
    post_event(event)

def run() -> None:
    while True:
        get_ticker("ETH/USD")
        get_ticker("BTC/USD")
        time.sleep(60)

if __name__ == "__main__":
    run()

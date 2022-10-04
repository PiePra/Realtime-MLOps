import requests
from cloudevents.http import CloudEvent
from cloudevents.conversion import to_structured
from datetime import datetime
import time
import logging

attributes = {
    "type": "cluster.local.crypto_price",
    "source": "https://cluster.local/crypto_price",
}

def get_ticker(ticker):
    try:
        
        r = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={ticker.replace("/", "") + "T"}')
        data = {"price": float(r.json()['price']), "timestamp": datetime.now().timestamp(), "symbol": ticker}
        try:
            event = CloudEvent(attributes, data)
            headers, body = to_structured(event)
            requests.post("http://kafka-broker-ingress.knative-eventing.svc.cluster.local/default/crypto", data=body, headers=headers)
            logging.info(f"created {event}")
        except:
            logging.error("broker not reachable")
    except:
        logging.error("api not reachable")

if __name__ == "__main__":
    while True:
        get_ticker("ETH/USD")
        get_ticker("BTC/USD")
        time.sleep(60)
import requests
from cloudevents.http import CloudEvent
from cloudevents.conversion import to_structured
from flask import Flask
from datetime import datetime

app = Flask(__name__)
attributes = {
    "type": "cluster.local.crypto_price",
    "source": "https://cluster.local/crypto_price",
}

@app.route("/btc")
def get_btc():
    r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
    data = {"price": float(r.json()['price']), "timestamp": datetime.now().timestamp(), "symbol": "BTC/USD"}
    post_event(data)
    return "success"

@app.route("/eth")
def get_eth():
    r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT')
    data = {"price": float(r.json()['price']), "timestamp": datetime.now().timestamp(), "symbol": "ETH/USD"}
    post_event(data)
    return "success"

def post_event(data):
    event = CloudEvent(attributes, data)
    headers, body = to_structured(event)
    requests.post("http://kafka-broker-ingress.knative-eventing.svc.cluster.local/default/crypto", data=body, headers=headers)

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=5000)

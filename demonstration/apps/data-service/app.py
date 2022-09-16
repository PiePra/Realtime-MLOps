import requests
from cloudevents.http import CloudEvent
from cloudevents.conversion import to_structured
from flask import Flask
from datetime import datetime

app = Flask(__name__)

@app.route("/btc")
def get_btc():
    attributes = {
    "type": "com.example.sampletype1",
    "source": "https://example.com/event-producer",
    }
    r = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
    data = {"price": float(r.json()['price']), "timestamp": datetime.now().timestamp()}
    event = CloudEvent(attributes, data)
    headers, body = to_structured(event)
    requests.post("http://kafka-broker-ingress.knative-eventing.svc.cluster.local/default/btc", data=body, headers=headers)
    return "success"


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=5000)

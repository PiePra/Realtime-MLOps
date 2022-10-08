from flask import Flask
import requests
app = Flask(__name__)


@app.route('/')
def trigger():
    r = requests.post("http://el-stateful-fit.default.svc.cluster.local:8080", json={"action": "stateful"}) 
    return "success"

if __name__=="__main__":
    app.run(host='0.0.0.0', port=5000)
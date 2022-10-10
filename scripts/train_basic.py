import os
import pandas as pd
import numpy as np
import mlflow
import logging
from mlflow.models.signature import infer_signature
import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.ERROR)

#read and prepare dataframe
df = pd.read_csv('data/BTCUSD_5.csv', header = None, names = ["unix", "open", "high", "low", "close", "volume", "trades"])
df['unix'] = pd.to_datetime(df['unix'], unit='s')
df = df.set_index(pd.DatetimeIndex(df['unix']))
df = df.drop(df[['volume', 'trades', 'unix']], axis=1)
df.sort_values(by='unix', inplace=True)

#get y
df['y'] = df['close'].shift(-1)
df = df[:-1]
#df = df.resample('5Min').asfreq().dropna()

#get eth
df_eth = pd.read_csv('data/ETHUSD_5.csv', header = None, names = ["unix", "open", "high", "low", "close", "volume", "trades"])
df_eth['unix'] = pd.to_datetime(df_eth['unix'], unit='s')
df_eth = df_eth.set_index(pd.DatetimeIndex(df_eth['unix']))
df_eth = df_eth.drop(df_eth[['volume', 'trades', 'unix']], axis=1)
df_eth.sort_values(by='unix', inplace=True)

#join
df = df.join(df_eth, on='unix', how='inner', lsuffix='_btc', rsuffix='_eth')

#get timestamp of first and last observation
first = df.index[0].timestamp()
last = df.index[-1].timestamp()

#prepare model data
random_state = 42
train_size = 0.8
X = df[['open_btc', 'high_btc', 'low_btc', 'close_btc', 'open_eth', 'high_eth', 'low_eth', 'close_eth']]
y = df['y']
X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=train_size, random_state=random_state)

#set mlflow parameters
os.environ["AWS_ACCESS_KEY_ID"] = "mlflow"
os.environ["AWS_SECRET_ACCESS_KEY"] = "mlflow123"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = f"http://mlflow-minio.mlflow.svc.cluster.local:9000/"
model_artifact_name = "model"

mlflow.set_tracking_uri("http://mlflow.mlflow.svc.cluster.local")
mlflow.set_experiment("bitcoin")

np.random.seed(random_state)

logger = logging.getLogger(__name__)

def eval_metrics(actual, pred):
    rmse = np.sqrt(mean_squared_error(actual, pred))
    mae = mean_absolute_error(actual, pred)
    r2 = r2_score(actual, pred)
    return rmse, mae, r2

with mlflow.start_run():
    mlflow.xgboost.autolog()
    
    best_parameters = {'gamma': 0.001,
          'learning_rate': 0.05,
          'max_depth': 8,
          'n_estimators': 200,
          'random_state': 42}

    model = xgb.XGBRegressor(**best_parameters, objective='reg:squarederror')
    model.fit(X_train, y_train, eval_set=eval_set, verbose=False)

    # Evaluate the best model with testing data.
    y_hat = model.predict(X_test)
    (rmse, mae, r2) = eval_metrics(y_test, y_hat)
    mlflow.log_param("data_from", first)
    mlflow.log_param("data_to", last)
    mlflow.log_param("feature_view", "crypto_stats")
    mlflow.log_param("framework", "xgboost")
    mlflow.log_param("random_state", random_state)
    mlflow.log_metric("rmse", rmse)
    mlflow.log_metric("r2", r2)
    mlflow.log_metric("mae", mae)
    
    model_signature = infer_signature(X_train, y_train)
    info = mlflow.xgboost.log_model(model, model_artifact_name, registered_model_name="BitcoinForecast-xgb", signature=model_signature)
    
    uri = mlflow.get_artifact_uri()


storage_uri = f"{uri}/{model_artifact_name}"

template = f"""
apiVersion: "serving.kserve.io/v1beta1"
kind: "InferenceService"
metadata:
  name: "bitcoin-forecast"
  namespace: default
  labels:
    networking.knative.dev/visibility: cluster-local
spec:
  predictor:
    serviceAccountName: sa-s3
    model:
      modelFormat:
        name: mlflow
      protocolVersion: v2
      storageUri: {storage_uri}
  transformer:
    logger: 
      mode: response
      url: http://kafka-broker-ingress.knative-eventing.svc.cluster.local/default/crypto-prediction
    containers:
    - image: piepra/feast-transformer:1.8
      name: btc-transfomer
      command:
      - "python"
      - "app/app.py"
      args:
      - --feast_serving_url
      - feast-feature-server.feast.svc.cluster.local:80
      - --entity_ids
      - "BTC/USD"
      - --feature_refs
      - "crypto_stats:open"
      - "crypto_stats:high"
      - "crypto_stats:low"
      - "crypto_stats:close"
      - --protocol
      - v2
"""

with open('demonstration/feast-kserve-transform/deployment/isvc.yaml', 'w+') as f:
    f.writelines(template)
    logging.info("wrote to demonstration/feast-kserve-transform/deployment/isvc.yaml")
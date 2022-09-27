import os
import pandas as pd
import numpy as np
import mlflow
import logging
from mlflow.models.signature import infer_signature
import tensorflow as tf
from tensorflow.keras.layers import Dense
from tensorflow.keras.models import Sequential
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.ERROR)

#read and prepare dataframe
df = pd.read_csv('data/BTC-2021min.csv')
df['unix'] = pd.to_datetime(df['unix'], unit='s')
df = df.set_index(pd.DatetimeIndex(df['unix']))
df = df.drop(df[['symbol', 'Volume BTC', 'Volume USD', 'date', 'unix']], axis=1)
df.sort_values(by='unix', inplace=True)

#resample to 5 mins
df['y'] = df['close'].shift(-1)
df = df[:-1]
df = df.resample('5Min').asfreq().dropna()

#get timestamp of first and last observation
first = df.index[0].timestamp()
last = df.index[-1].timestamp()

#prepare model data
random_state = 42
train_size = 0.8
X = df[['open', 'high', 'low', 'close']]
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
tf.random.set_seed(random_state) 

logger = logging.getLogger(__name__)

def eval_metrics(actual, pred):
    rmse = np.sqrt(mean_squared_error(actual, pred))
    mae = mean_absolute_error(actual, pred)
    r2 = r2_score(actual, pred)
    return rmse, mae, r2

with mlflow.start_run():
    mlflow.tensorflow.autolog()
    
    model = Sequential()
    model.add(Dense(32, input_shape=(X_train.shape[-1],), activation="relu", name="hidden_layer"))
    model.add(Dense(16))
    model.add(Dense(1))
    model.compile(loss="mse", optimizer="adam")
    
    model.fit(X_train, y_train, epochs=5, batch_size=100, validation_split=.2)
            
    # Evaluate the best model with testing data.
    y_hat = model.predict(X_test)
    (rmse, mae, r2) = eval_metrics(y_test, y_hat)
    mlflow.log_param("data_from", first)
    mlflow.log_param("data_to", last)
    mlflow.log_param("feature_view", "crypto_stats")
    mlflow.log_param("framework", "tensorflow")
    mlflow.log_param("version", tf.__version__)
    mlflow.log_param("random_state", random_state)
    mlflow.log_metric("rmse", rmse)
    mlflow.log_metric("r2", r2)
    mlflow.log_metric("mae", mae)
    lr = res = {"lr_" + str(key): val for key, val in model.optimizer.get_config().items()}
    mlflow.log_params(lr)
    
    model_signature = infer_signature(X_train, y_train)
    info = mlflow.keras.log_model(model, model_artifact_name, registered_model_name="BitcoinForecast", signature=model_signature)
    
    uri = mlflow.get_artifact_uri()


storage_uri = f"{uri}/{model_artifact_name}"

template_basic = f"""
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
"""

with open('demonstration/basic-model/deployment/isvc.yaml', 'w+') as f:
    f.writelines(template_basic)
    logging.error("Wrote file demonstration/basic-model/deployment/isvc.yaml")

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
    logger: 
      mode: response
      url: http://kafka-broker-ingress.knative-eventing.svc.cluster.local/default/crypto-prediction
    model:
      modelFormat:
        name: mlflow
      protocolVersion: v2
      storageUri: {storage_uri}
  transformer:
    containers:
    - image: piepra/feast-transformer:1.2
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
    logging.error("demonstration/feast-kserve-transform/deployment/isvc.yaml")
import argparse
import pandas as pd
from datetime import datetime
from feast import FeatureStore

parser = argparse.ArgumentParser(description='Load offline features.')
parser.add_argument('--feature_service', help='The name of the feature service.', type=str, required = True)
parser.add_argument('--entity_name', help='Name of the entity.', type=str, required = True)
parser.add_argument('--entity_ids', help='List of entity ids', type=str, nargs="+", required = True)
parser.add_argument('--from_time', help='Name of the entity.', type=float, required = True)
parser.add_argument('--to_time', help='Get features since this time.', type=float, default=datetime.utcnow().timestamp())
parser.add_argument('--frequency', help=' The frequency interval.', type=str, default = "5min")
args = parser.parse_args()

FEATURE_SERVICE = args.feature_service
ENTITY = args.entity_name
ENTITY_IDs = args.entity_ids
FROM = args.from_time
TO = args.to_time
FREQUENCY= args.frequency

ENTITY = "symbol"
ENTITY_IDs = ["BTC/USD", "ETH/USD"]
FROM = 1656633000.0
TO = datetime.utcnow()
FREQUENCY="5min"
FEATURE_SERVICE = "crypto_stats"

entity_dfs = []
for entity_id in ENTITY_IDs:
    entity_df = pd.DataFrame.from_dict(
        {
            ENTITY: entity_id,
            "event_timestamp": [item for item in pd.date_range(datetime.fromtimestamp(FROM), datetime.utcnow(), freq=FREQUENCY)]
        }
    )
    entity_dfs.append(entity_df)
    
feature_store = FeatureStore('demonstration/feature_store/feature_repo')  # Initialize the feature store
feature_service = feature_store.get_feature_service(FEATURE_SERVICE)

training_dfs = []
for entity_df in entity_dfs:
    training_df = feature_store.get_historical_features(features=feature_service, entity_df=entity_df).to_df()
    training_df = training_df.set_index(pd.DatetimeIndex(training_df['event_timestamp']))
    training_dfs.append(training_df)
    
for i in range(1, len(training_dfs)):
    df = training_dfs[0].join(training_dfs[i], lsuffix="_"+ENTITY_IDs[0][:3].lower(), rsuffix="_"+ENTITY_IDs[i][:3].lower())
    
df = df.dropna()
first = df.index[0].timestamp()
last = df.index[-1].timestamp()

df['y'] = df['close_btc'].shift(-1)
df = df.iloc[:-1]

keys = [x for x in df.columns if "symbol" not in x and "timestamp" not in x]
df = df[keys].drop_duplicates()
df.to_csv('features.csv')
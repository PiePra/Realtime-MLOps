import argparse
import kserve

from crypto_transformer import CryptoTransformer

DEFAULT_MODEL_NAME = "mlflow-crypto-forecast"
DEFAULT_FEAST_URL = "feature-store-feature-server.feast.svc.cluster.local:6566"
DEFAULT_PROTOCOL = "v2"

parser = argparse.ArgumentParser(parents=[kserve.model_server.parser])
parser.add_argument(
    "--predictor_host",
    help="The URL for the model predict function", required=True
)
parser.add_argument(
    "--protocol", default=DEFAULT_PROTOCOL,
    help="The protocol for the predictor"
)
parser.add_argument(
    "--model_name", default=DEFAULT_MODEL_NAME,
    help='The name that the model is served under.')
parser.add_argument(
    "--feast_serving_url",
    type=str,
    help="The url of the Feast feature server.", required=True)
parser.add_argument(
    "--entity_ids",
    type=str, nargs="+",
    help="A list of entity ids to use as keys in the feature store.",
    required=True)
parser.add_argument(
    "--feature_refs",
    type=str, nargs="+",
    help="A list of features to retrieve from the feature store.",
    required=True)


args, _ = parser.parse_known_args()

if __name__ == "__main__":
    transformer = CryptoTransformer(
        name=args.model_name,
        predictor_host=args.predictor_host,
        protocol=args.protocol,
        feast_serving_url=args.feast_serving_url,
        entity_ids=args.entity_ids,
        feature_refs=args.feature_refs)
    server = kserve.ModelServer()
    server.start(models=[transformer])
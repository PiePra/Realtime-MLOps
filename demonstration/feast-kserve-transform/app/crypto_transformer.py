#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import List, Dict
import logging
import kserve
import requests
import json
import numpy as np
#from tritonclient.grpc import service_pb2 as pb
#from tritonclient.grpc import InferResult

logging.basicConfig(level=kserve.constants.KSERVE_LOGLEVEL)


class CryptoTransformer(kserve.Model):
    """ A class object for the data handling activities of crypto forecast
    Task and returns a KServe compatible response.
    Args:
        kserve (class object): The Model class from the KServe
        module is passed here.
    """
    def __init__(self, name: str,
                 predictor_host: str,
                 protocol: str,
                 feast_serving_url: str,
                 entity_ids: List[str],
                 feature_refs: List[str]):
        """Initialize the model name, predictor host, Feast serving URL,
           entity IDs, and feature references
        Args:
            name (str): Name of the model.
            predictor_host (str): The host in which the predictor runs.
            protocol (str): The protocol in which the predictor runs.
            feast_serving_url (str): The Feast feature server URL, in the form
            of <host_name:port>
            entity_ids (List[str]): The entity IDs for which to retrieve
            features from the Feast feature store
            feature_refs (List[str]): The feature references for the
            features to be retrieved
        """
        super().__init__(name)
        self.predictor_host = predictor_host
        self.protocol = protocol
        self.feast_serving_url = feast_serving_url
        self.entity_ids = entity_ids
        self.feature_refs = feature_refs
        self.feature_refs_key = [feature_refs[i].replace(":", "__") for i in range(len(feature_refs))]
        logging.info("Model name = %s", name)
        logging.info("Protocol = %s", protocol)
        logging.info("Predictor host = %s", predictor_host)
        logging.info("Feast serving URL = %s", feast_serving_url)
        logging.info("Entity ids = %s", entity_ids)
        logging.info("Feature refs = %s", feature_refs)

        self.timeout = 100


    def buildPredictRequest(self, inputs, features) -> Dict:
        """Build the predict request for all entities and return it as a dict.
        Args:
            inputs (Dict): entity ids from http request
            features (Dict): entity features extracted from the feature store
        Returns:
            Dict: Returns the entity ids with features
        """
        entity_name = "symbol"
        inputs = []
        i = 0
        for line in features['metadata']['feature_names']:
            if line != entity_name:
                value = features['results'][i]["values"]
                entry ={"name": line, "shape": [1], "datatype": "FP64", "data": value}
                inputs.append(entry)
            i = i + 1
            
        result =  {
            "parameters": {
                "content_type": "pd"
            },
            "inputs": inputs
        }

        return result

    def preprocess(self, inputs: Dict) -> Dict:
        """Pre-process activity of the crypto forefacst data.
        Args:
            inputs (Dict): http request
        Returns:
            Dict: Returns the request input after ingesting online features
        """
        headers = {"Content-type": "application/json", "Accept": "application/json"}
        params = {'features': self.feature_refs, 'entities': {"symbol": self.entity_ids},
                  'full_feature_names': True}
        json_params = json.dumps(params)
        r = requests.post("http://" + self.feast_serving_url + "/get-online-features/", data=json_params, headers=headers)
        logging.info("The online feature rest request status is %s", r.status_code)
        features = r.json()
        logging.error(f"input: {input}")
        logging.error(f"features: {features}")
        outputs = self.buildPredictRequest(inputs, features)
        logging.error(f"outputs: {outputs}")

        logging.info("The input for model predict is %s", outputs)

        return outputs

    def postprocess(self, inputs: Dict) -> Dict:
        """Post process function of the driver ranking output data. Here we
        simply pass the raw rankings through. Convert gRPC response if needed.
        Args:
            inputs (Dict): The inputs
        Returns:
            Dict: If a post process functionality is specified, it could convert
            raw rankings into a different list.
        """
        logging.info("The output from model predict is %s", inputs)
        # if self.protocol == "grpc-v2":
        #     response = InferResult(inputs)
        #     return response.get_response(as_json=True)
        return 
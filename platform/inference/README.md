# Model Serving

Deploy the model serving environment including istio, knative-serving, cert-manager, kserve, prometheus.
`kubectl kustomize platform/inference/ | kubectl create -f -`

wait for all resources to be ready
`watch kubectl get pods -A`

# Test Model Serving
Apply an inferencesverice
`kubectl apply -f demonstration/apps/basic-model/deployment`
Wait till it becomes ready (takes some minutes)
`watch kubectl get isvc`

check the url 
`http://mlflow-v2-wine-classifier2-predictor-default.default.svc.cluster.local/v2`

test the model
```bash
curl -v -H "bitcoin-forecast.default.svc.cluster.local" -H "Content-Type: application/json" -d @demonstration/apps/basic-model/payload.json \
 http://bitcoin-forecast.default.svc.cluster.local/v2/models/bitcoin-forecast/infer 
```

description of v2 api-docs
https://kserve.github.io/website/modelserving/inference_api/

check prometheus
`http://prometheus.prometheus.svc.cluster.local`

head to status -> targets
the demo Endpoint should show state as up
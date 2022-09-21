# Model Serving

Deploy the model serving environment including istio, knative-serving, cert-manager, kserve, prometheus.
`kubectl kustomize platform/model-serving/ | kubectl create -f -`

wait for all resources to be ready
`watch kubectl get pods -A`

# Test Model Serving
Apply an inferencesverice
`kubectl apply -f platform/model-serving/kserve/test.yaml`
Wait till it becomes ready
`watch kubectl get isvc`

check the url 
`http://mlflow-v2-wine-classifier2-predictor-default.default.svc.cluster.local/v2`

(might have to telepresence quit / telepresence connect)

check prometheus
`http://prometheus.prometheus.svc.cluster.local`

head to status -> targets
the demo Endpoint should show state as up
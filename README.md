# Realtime-MLOps: A combination of open-source technologies to operate machine learning in realtime.

Realtime MLOps combines selected open-source tools to operate machine learning models with a focus on realtime ml.
This setup enables and demonstrates online inferencing, realtime monitoring and continual learning with automated statefull retrainings while also providing a matured Kubernetes-native MLOps platform. 

The platform is divided in 4 modules to enable different areas of realtime MLOps. 

Kubernetes is used in conjunction with Github and ArgoCD to provide an Infrastructure-as-Code enabled way of managing the platform.
Strimzi Kafka Operator and KNative Eventing are used to provide and abstract streaming capabilities in a Kubernetes-native way.
To orchestrate modular ml pipelines tekton is used along with mlflow to store experiment metadata and model artifacts. Tekton enables event triggered pipeline runs.
Inferencing is done by using KServe and Prometheus to allow model serving, model updating and model monitoring. 
Feast is used as a feature store to orchestrate and serve features at low latency. 

# Platform Setup
Installation is provided in the form of kustomization and yaml manifests. The setup is developed and tested on Kubernetes v1.23.
A kind configuration is provided to enable a local installation. 
```bash
kind create cluster --name realtime-mlops --config kind/kind.yaml
```
Depending on the system there might be the necessity to increase inotify instances:
```bash
sudo sysctl fs.inotify.max_user_watches=524288
sudo sysctl fs.inotify.max_user_instances=512
```

Generate and create platform manifests on Kubuernetes using kustomize.
```bash
kubectl kustomize ./platform | kubectl create -f -
```
Wait for all resources to be ready.
```bash
watch kubectl get pods -A
```

# Platform Access
Telepresence provides a convinient way to access internal Kubernetes services externally. Install Telepresence according to the installation docs or by using:
```bash
sudo curl -fL https://app.getambassador.io/download/tel2/linux/amd64/latest/telepresence -o /usr/local/bin/telepresence
sudo chmod a+x /usr/local/bin/telepresence
```
then run
```
telepresence helm install
telepresence connect
```

Web interfaces then are available at:
- argocd: https://argocd-server.argocd.svc.cluster.local
- prometheus: http://prometheus.prometheus.svc.cluster.local/
- grafana: http://grafana.prometheus.svc.cluster.local:3000/
- tekton: http://tekton-dashboard.tekton-pipelines.svc.cluster.local:9097
- mlflow: http://mlflow.mlflow.svc.cluster.local/
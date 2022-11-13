# Realtime-MLOps: A framework of open-source technologies to design real-time ml systems.

Realtime MLOps provides a cloud-native approach to design machine learning systems enabling the use of real-time.
This setup enables and demonstrates real-time feature engineering, online inferencing, real-time monitoring and continual learning as a a matured Kubernetes-native MLOps platform. 

- [Realtime-MLOps: A framework of open-source technologies to design real-time ml systems.](#realtime-mlops-a-framework-of-open-source-technologies-to-design-real-time-ml-systems)
- [Summary](#summary)
- [Quickstart](#quickstart)
- [Access](#access)
- [Demonstration](#demonstration)
  - [Real-time Feature Engineering](#real-time-feature-engineering)
  - [Online Inferencing](#online-inferencing)
  - [Continual Learning](#continual-learning)
  - [Real-time Monitoring](#real-time-monitoring)

# Summary

The platform is divided in five modules to enable different areas of real-time MLOps. 

Kubernetes is used in conjunction with Github to provide an Infrastructure-as-Code enabled way of managing the platform.
Strimzi Kafka Operator and KNative Eventing are used to provide and abstract streaming capabilities in a Kubernetes-native way.
To orchestrate modular ml pipelines tekton is used along with mlflow to store experiment metadata and model artifacts. Tekton enables event triggered pipeline runs.
Inferencing is done by using KServe and Prometheus to allow model serving, model updating and model monitoring. 
Feast is used as a feature store to orchestrate and serve features at low latency. 

# Quickstart
Download the repistory and create conda environment
`make env`
and activate
`conda activate realtime-mlops`

Simply use `make install` to install all components and run the demonstration examples.

# Access
Telepresence provides a convinient way to access internal Kubernetes services externally. 

Web interfaces then are available at:
- prometheus: http://prometheus.prometheus.svc.cluster.local/
- tekton: http://tekton-dashboard.tekton-pipelines.svc.cluster.local:9097
- mlflow: http://mlflow.mlflow.svc.cluster.local/
- minio: http://mlflow-minio.mlflow.svc.cluster.local:9000/
- demo-app: http://webapp.default.svc.cluster.local/

If the setup did run successfully but the web UIs are not available it may help to quit and connect telepresence client again.
```
telepresence quit
telepresence connect
```

# Demonstration
Check out the demonstraion for a real-time ml use-case.

## Real-time Feature Engineering
see demonstration/realtime-feature-engineering/README.md

## Online Inferencing
see demonstration/online-inferencing/README.md

## Continual Learning
see demonstration/continual-learning/README.md

## Real-time Monitoring
see demonstration/realtime-monitoring/README.md
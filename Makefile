env:
	echo "---- Creating Conda Env ----" 
	conda env create -f platform/infra/conda/environment.yaml

delete-env:
	echo "---- Deleting Conda Env ----" 
	conda env delete --name realtime-mlops

delete:
	echo "---- Deleting Kind Cluster ----" 
	kind delete cluster --name realtime-mlops

cluster:
	echo "---- Installing Kind Cluster ----" 
	sudo sysctl fs.inotify.max_user_watches=524288
	sudo sysctl fs.inotify.max_user_instances=512	
	kind create cluster --name realtime-mlops --config platform/infra/kind/kind.yaml
	kubectl wait deployment -n kube-system coredns --for condition=Available=True --timeout=180s

connect: 
	echo "---- Installing Telepresence ----" 
	telepresence helm install
	telepresence connect

feature-store:
	echo "---- Installing Feature Store ----" 
	kubectl kustomize --enable-helm platform/feature-store/ | kubectl apply -n feast -f -
	kubectl rollout status -n feast --watch --timeout=180s statefulsets/online-store-redis-master
	kubectl rollout status -n feast --watch --timeout=180s statefulsets/offline-store-postgresql
	kubectl wait deployment -n feast feature-store-feast-feature-server --for condition=Available=True --timeout=180s
	echo "---- Loading Data into offline Store ----" 
	python scripts/fill_offlinestore.py
	echo "---- Creating Feature Store tables ----" 
	(cd platform/feature-store/feature_store/feature_repo ;feast apply)
	kubectl rollout restart deployment/feature-store-feast-feature-server -n feast


streaming-system:
	echo "---- Installing Streaming System ----" 
	kubectl kustomize platform/streaming-system/ | kubectl create -f -
	kubectl wait deployment -n strimzi strimzi-cluster-operator --for condition=Available=True --timeout=180s
	kubectl wait pods -n kafka -l strimzi.io/name=streaming-system-zookeeper --for condition=Ready --timeout=180s
	sleep 5s
	kubectl wait pods -n kafka -l strimzi.io/name=streaming-system-kafka --for condition=Ready --timeout=180s
	sleep 5s
	kubectl wait deployment -n kafka streaming-system-entity-operator --for condition=Available=True --timeout=180s
	kubectl apply -f demonstration/stream-processing/data-service/deployment
	kubectl wait deployment data-service --for condition=Available=True --timeout=180s
	kubectl apply -f demonstration/stream-processing/data-pipeline/deployment

training:
	echo "---- Installing Training Components ----" 
	kubectl kustomize --enable-helm platform/training | kubectl create -f - 
	kubectl rollout status -n mlflow --watch --timeout=180s statefulsets/postgres-postgresql
	kubectl wait deployment -n mlflow mlflow-minio --for condition=Available=True --timeout=180s
	kubectl wait deployment -n mlflow mlflow --for condition=Available=True --timeout=180s
	echo "---- Train a basic model ----" 
	python scripts/train_basic.py

inference:
	echo "---- Installing Inference Components ----" 
	kubectl kustomize platform/inference/ | kubectl create -f -
	kubectl wait deployment -n kserve kserve-controller-manager --for condition=Available=True --timeout=300s
	kubectl apply -f demonstration/online-inference/deployment
	sleep 5
	kubectl apply -f demonstration/realtime-monitoring/deployment
	sleep 5
	kubectl wait deployment bitcoin-forecast-predictor-default-00001-deployment --for condition=Available=True --timeout=600s

online-learning:
	echo "---- Installing ML Pipeline Components ----" 
	kubectl apply -f demonstration/continual-learning/trigger/deployment
	kubectl apply -f demonstration/continual-learning/tasks
	kubectl apply -f demonstration/continual-learning/pipelines
	kubectl apply -f demonstration/continual-learning/eventlistener
	
install:
	make cluster connect feature-store streaming-system training inference online-learning

# Install the training syste

`kubectl kustomize --enable-helm platform/training | kubectl create -f - `

wait for all resources to be ready

`watch kubectl get pods -A`

# Train a model to mlflow

install dependencies
`pip install boto3 pandas tensorflow mlflow sklearn matplotlib`

run the basic_model.ipynb at demonstration/apps/basic-model

# Check out Model at MLFlow

`http://mlflow.mlflow.svc.cluster.local/`




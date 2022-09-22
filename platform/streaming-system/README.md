# Streaming System

Deploy the streaming system environment including strimzi, knative-eventing and create a kafka cluster
`kubectl kustomize platform/streaming-system/ | kubectl create -f -`

wait for all resources (inlcuding kafkacluster in namespace kafka) to be ready
`watch kubectl get pods -A`

# Test Streaming System
create a python service and a knative-broker to start ingesting events into the broker
`kubectl apply -f demonstration/data-service/deployment`

inspect incoming events (new events every minute). Start a bash in the kafka container.
`kubectl exec -it -n kafka streaming-system-kafka-0 -- bash`
list available topics
`./bin/kafka-topics.sh --bootstrap-server localhost:9092 --list`
and read the relevant topic for incoming cloudevents
`./bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --from-beginning --topic knative-broker-default-crypto --property print.headers=true`
and exit
`exit`

# Apply Streaming Data Pipeline

Create the bytewax deployment
`kubectl apply -f demonstration/data-pipeline/deployment/bytewax.yaml`



# Check database
inspect new database entries populated to offline store coming in after 5 minutes:
Login to postgres (password: feast)
`psql -U feast -h offline-store-postgresql.feast.svc.cluster.local -d feast`
Check tables
`\dt+`
Check offline source
`select * from crypto_source order by timestamp desc limit 5;`
Quit
`\q`
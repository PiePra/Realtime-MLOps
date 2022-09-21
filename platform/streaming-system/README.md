# Streaming System

Deploy the streaming system environment including strimzi, knative-eventing and create a kafka cluster
`kubectl kustomize platform/model-serving/ | kubectl create -f -`

wait for all resources to be ready
`watch kubectl get pods -A`

# Test Streaming System
We create a rest service, knative-broker and a cronjob to start ingesting events into the broker
`kubectl apply -f demonstration/apps/data-service/deployment`

inspect incoming events. Start a bash in the kafka container.
`kubectl exec -it -n kafka streaming-system-kafka-0 -- bash`
list available topics
`./bin/kafka-topics.sh --bootstrap-server localhost:9092 --list`
and read the relevant topic for incoming cloudevents
`./bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --from-beginning --topic knative-broker-default-crypto --property print.headers=true`

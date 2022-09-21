# Feature Store

Deploy the Feast Feature Store
`kubectl kustomize --enable-helm platform/feast/ | kubectl apply -n feast -f -`



# Populate the offline Store
Install dependencies 
`pip install jupyterlab pandas feast feast[redis] feast[postgres]`

Start jupyter lab in a terminal
`jupyter lab`

Open the Helper Notebook
`demonstration/apps/feature_store/helper.ipynb`

Run the "CSV to SQL" to create table at offline store

# Populate feast infrastructure

install feast and dependencies


cd to feature_repo
`cd demonstration/apps/feature_store/feature_repo`
run feast apply
`feast apply`

# Check Database
Login to postgres (password: feast)
`psql -U feast -h offline-store-postgresql.feast.svc.cluster.local -d feast`
Check tables
`\dt+`
Check offline source
`select * from crypto_source order by timestamp desc limit 5;`
Quit
`\q`


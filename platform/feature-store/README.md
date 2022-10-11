# Feature Store

Deploy the Feast Feature Store
`kubectl kustomize --enable-helm platform/feast/ | kubectl apply -n feast -f -`

# Populate the offline Store
Start jupyter lab in a terminal
`jupyter lab`

Open the Helper Notebook
`demonstration/feature_store/helper.ipynb`

Run the "CSV to SQL" to create table at offline store

# Populate feast infrastructure

cd to feature_repo
`cd demonstration/feature_store/feature_repo`
run feast apply
`feast apply`
go back to main directory
`cd ../../../`


# Check database
Login to postgres (password: feast)
`psql -U feast -h offline-store-postgresql.feast.svc.cluster.local -d feast`
Check tables
`\dt+`
Check offline source
`select * from crypto_source order by timestamp desc limit 5;`
Quit
`\q`

# Populate the online store

Run the "Read and Write online Features" in the notebook. 
# Docker container

Run
```
sudo docker-compose build
sudo docker-compose up
```

For rebuilding use
```
sudo docker-compose down
sudo docker-compose build
sudo docker-compose up
```


Afterwards run
```
gh webhook forward --events=push,pull_request --repo=alleonhardt/algo-learn --url="http://localhost:8000" --secret="your-secret-token"
```
to forward the webhooks to the created service or use the github web interface to directly add the webhook.

Now the builds should be available at `http://localhost:1409`.

# Bot for testing message sending with export metrics to Prometheus

## Build
```bash
docker build -t <image_name> .
```

## Run 
```bash
docker run -t -p 8080:8080 <image_name>
```

## Environment variables

Set them in Dockerfile:

`BOT_ENDPOINT` - endpoint for watching

`BOT_TOKEN` - token for bot

`USERNAME` - username for auth in bitbucket

`PASSWORD` - password for auth in bitbucket

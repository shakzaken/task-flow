# CDK Project

## Prerequisites

- Python `3.13`
- AWS CLI configured with credentials
- Node.js and `npm`

## Required local files

Create the local config file from the example:

```bash
cp cdk/.env.cdk.example cdk/.env.cdk
```

Then fill in the required values before deploy.

## Install dependencies

Python dependencies with `uv`:

```bash
cd cdk
UV_CACHE_DIR=../.uv-cache uv sync
```

Node dependency for the local CDK CLI:

```bash
cd cdk
npm install
```

## Run synth

Use a local `HOME` so the JSII cache stays inside the repo:

```bash
cd cdk
HOME=$PWD/.home ./node_modules/.bin/cdk synth
```

## Notes

- `.env.cdk` is local-only and ignored by git.
- The first version uses `.env.cdk` for both normal config and secrets.
- ECR repositories must already exist before deployment:
  - `task-flow-api`
  - `task-flow-worker`

## Create ECR repositories

If the repositories do not exist yet:

```bash
aws ecr create-repository --repository-name task-flow-api
aws ecr create-repository --repository-name task-flow-worker
```

Authenticate Docker to ECR:

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

## Build and push images

Choose one immutable tag, for example a git SHA:

```bash
export IMAGE_TAG=<git-sha>
export AWS_ACCOUNT_ID=<account-id>
export AWS_REGION=us-east-1
```

Build the API image:

```bash
docker build -f api-service/Dockerfile -t task-flow-api:$IMAGE_TAG .
docker tag task-flow-api:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/task-flow-api:$IMAGE_TAG
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/task-flow-api:$IMAGE_TAG
```

Build the worker image:

```bash
docker build -f worker-service/Dockerfile -t task-flow-worker:$IMAGE_TAG .
docker tag task-flow-worker:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/task-flow-worker:$IMAGE_TAG
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/task-flow-worker:$IMAGE_TAG
```

Then set these values in `cdk/.env.cdk`:

- `AWS_ACCOUNT=$AWS_ACCOUNT_ID`
- `AWS_REGION=$AWS_REGION`
- `API_IMAGE_TAG=$IMAGE_TAG`
- `WORKER_IMAGE_TAG=$IMAGE_TAG`

## Deploy

Bootstrap the environment once if needed:

```bash
cd cdk
UV_CACHE_DIR=../.uv-cache uv sync
HOME=$PWD/.home ./node_modules/.bin/cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION
```

Deploy:

```bash
cd cdk
UV_CACHE_DIR=../.uv-cache uv sync
HOME=$PWD/.home ./node_modules/.bin/cdk deploy
```

Useful outputs after deploy:

- ALB DNS name
- S3 bucket name
- ECS cluster name
- ECS service names
- Cloud Map namespace

## Destroy

```bash
cd cdk
HOME=$PWD/.home ./node_modules/.bin/cdk destroy
```

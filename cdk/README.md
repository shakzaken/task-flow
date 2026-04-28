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

Use the shared script from the repo root:

```bash
./scripts/cdk_synth.sh
```

## Notes

- `.env.cdk` is local-only and ignored by git.
- The first version uses `.env.cdk` for both normal config and secrets.
- ECR repositories must already exist before deployment:
  - `task-flow-api`
  - `task-flow-worker`
- `api-service` runs Alembic migrations on startup before serving traffic, so the AWS stack does not use a separate migration task.

## Create ECR repositories

If the repositories do not exist yet:

```bash
aws ecr create-repository --repository-name task-flow-api
aws ecr create-repository --repository-name task-flow-worker
```

Authenticate Docker to ECR:

```bash
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.eu-west-1.amazonaws.com
```

## Build and push images

Use the shared script from the repo root:

```bash
./scripts/push_images_to_ecr.sh
```

By default it:

- uses your AWS CLI credentials from `aws configure`
- resolves the AWS account ID automatically
- uses your configured AWS region
- builds and pushes both images:
  - `task-flow-api`
  - `task-flow-worker`
- tags both images as `latest`

If needed, you can override the defaults:

```bash
AWS_REGION=eu-west-1 IMAGE_TAG=latest ./scripts/push_images_to_ecr.sh
```

Then set these values in `cdk/.env.cdk`:

- `AWS_ACCOUNT=<your-account-id>`
- `AWS_REGION=eu-west-1`
- `API_IMAGE_TAG=latest`
- `WORKER_IMAGE_TAG=latest`

## Deploy

Bootstrap the environment once if needed:

```bash
cd cdk
UV_CACHE_DIR=../.uv-cache uv sync
HOME=$PWD/.home ./node_modules/.bin/cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION
```

Deploy with the shared script:

```bash
./scripts/cdk_deploy.sh
```

Useful outputs after deploy:

- ALB DNS name
- S3 bucket name
- ECS cluster name
- ECS service names
- Cloud Map namespace

## Destroy

```bash
./scripts/cdk_destroy.sh
```

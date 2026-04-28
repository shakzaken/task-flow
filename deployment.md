# Deployment Guide

## Purpose

This guide explains how to run Task Flow locally and how to deploy it to AWS.

## Local Development

Task Flow supports two local workflows:

1. Full Docker workflow
2. Non-Docker workflow

### Option 1: Full Docker Workflow

This is the easiest way to run the full application locally.

#### Prerequisites

- Docker Desktop or Docker Engine
- AWS credentials are not required for local Docker

#### Start the stack

From the repository root, run:

```bash
docker compose up --build
```

This starts:

- `api-service`
- `worker-service`
- PostgreSQL
- Redis
- RabbitMQ
- MinIO

#### Local endpoints

- App UI and API: `http://localhost:8000`
- RabbitMQ management: `http://localhost:15672`
- MinIO console: `http://localhost:9001`

### Option 2: Non-Docker Workflow

This workflow runs the services directly on your machine while keeping the project structure the same.

#### Prerequisites

- Python 3.13
- `uv`
- Node.js and npm
- Docker for local infrastructure only, or locally installed PostgreSQL, Redis, RabbitMQ, and MinIO

#### API service

```bash
cd api-service
UV_CACHE_DIR=../.uv-cache uv sync --dev
.venv/bin/uvicorn app.main:app --reload --port 8000
```

`api-service` runs Alembic migrations automatically on startup.

#### Worker service

```bash
cd worker-service
UV_CACHE_DIR=../.uv-cache uv sync --dev
.venv/bin/uvicorn app.main:app --reload --port 8001
```

#### Frontend service

If you want the frontend as a standalone development server:

```bash
cd frontend-service
npm install
npm run dev
```

In this mode, the frontend talks to `api-service` on port `8000`.

If you want the frontend to be served by `api-service`, build it first:

```bash
./scripts/build_frontend_for_api.sh
```

Then open:

```text
http://localhost:8000
```

## AWS Deployment

The AWS deployment uses the CDK project in [cdk](/Users/yakir/projects/claude/task-flow/cdk).

### Prerequisites

- AWS account
- AWS CLI configured locally with `aws configure`
- Docker
- ECR repositories created manually:
  - `task-flow-api`
  - `task-flow-worker`

### Configure the CDK project

Create:

```text
cdk/.env.cdk
```

You can start from:

```text
cdk/.env.cdk.example
```

Fill in the required values before deployment.

### Bootstrap CDK

Run once per AWS account and region:

```bash
cd cdk
./node_modules/.bin/cdk bootstrap aws://<aws-account-id>/<aws-region>
```

### Build and push images

From the repository root:

```bash
./scripts/push_images_to_ecr.sh
```

This script:

- reads your AWS credentials from the local AWS CLI configuration
- builds `linux/amd64` images
- pushes both application images to ECR

### Validate the stack

```bash
./scripts/cdk_synth.sh
```

### Deploy the stack

```bash
./scripts/cdk_deploy.sh
```

### Destroy the stack

```bash
./scripts/cdk_destroy.sh
```

The destroy script performs ECS cleanup first so stack deletion is more reliable when capacity providers are involved.

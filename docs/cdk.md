# AWS CDK Plan

## Goal

Create one AWS CDK project in Python that deploys the app to AWS with a cost-first ECS on EC2 architecture.

This document reflects the current decisions:

- one CDK app
- one stack: `TaskFlowStack`
- one ECS cluster
- one EC2 Auto Scaling Group with `5` `t3.small` instances
- ECS on EC2 launch type
- soft placement, not strict dedicated-instance placement
- `api-service` is the only public entrypoint
- `worker-service`, `postgres`, `redis`, and `rabbitmq` run as ECS services on EC2
- frontend is served by `api-service`
- AWS uses `S3`, not MinIO
- CDK creates the S3 bucket
- ECR repositories are created manually, outside CDK
- CDK reads deployment config from a local ignored `.env.cdk` file
- first version uses HTTP only, no Route53, ACM, or CloudFront

## Target Architecture

### Public traffic

- Browser -> ALB -> `api-service`
- `api-service` serves:
  - frontend static files
  - backend API routes
  - artifact download routes

### Internal traffic

- `api-service` -> `postgres`
- `api-service` -> `redis`
- `api-service` -> `rabbitmq`
- `api-service` -> `S3`
- `worker-service` -> `postgres`
- `worker-service` -> `rabbitmq`
- `worker-service` -> `S3`
- `worker-service` -> external APIs such as Resend and OpenRouter

### ECS services

- `api-service`
- `worker-service`
- `postgres`
- `redis`
- `rabbitmq`

### AWS resources

- `1` VPC
- public subnets for the ALB
- public workload subnets for ECS EC2 instances
- `1` ECS cluster
- `1` Auto Scaling Group with `5 x t3.small`
- `1` internet-facing ALB
- `1` S3 bucket for uploads and outputs
- security groups
- CloudWatch log groups
- IAM roles and instance profile for ECS and S3 access

## Placement Strategy

We are using **soft placement**.

That means:

- the cluster has `5` EC2 instances
- ECS is allowed to place tasks wherever capacity exists
- we size and configure services so the intended layout is roughly one primary service per instance
- we do not add hard placement rules that pin one specific service to one specific machine

Why this choice:

- simpler CDK
- easier recovery if an instance dies
- more flexible than strict placement
- still close to the desired low-cost layout

## Service Layout Assumption

The intended runtime shape is:

1. `api-service`
2. `worker-service`
3. `postgres`
4. `redis`
5. `rabbitmq`

This is an intended capacity model, not a strict scheduler rule.

## Image Strategy

CDK will not create ECR repositories.

Manual ECR repositories:

- `task-flow-api`
- `task-flow-worker`

Image tagging recommendation:

- deploy with immutable git SHA tags
- optionally also push `latest` for convenience

For AWS deployment:

- `api-service` uses image from `task-flow-api`
- `worker-service` uses image from `task-flow-worker`
- `postgres`, `redis`, and `rabbitmq` can use public upstream images unless we later decide to mirror them into ECR

## Configuration Strategy

### Local CDK config file

CDK reads deployment values from:

- `.env.cdk`

This file must be:

- local only
- added to `.gitignore`
- not committed

We should also keep:

- `.env.cdk.example`

with placeholder values and documentation comments.

### What goes into `.env.cdk`

Non-secret config examples:

- AWS region
- stack name override if needed
- ECR image tags
- container ports
- database name
- database user
- S3 bucket name
- OpenRouter model
- worker concurrency

Secret config examples:

- `POSTGRES_PASSWORD`
- `RESEND_API_KEY`
- `OPENROUTER_API_KEY`
- `RABBITMQ_DEFAULT_USER`
- `RABBITMQ_DEFAULT_PASS`

### Important note

For this first version, `.env.cdk` is acceptable and simple.

Later, we may want to move real secrets into:

- AWS Secrets Manager
- or SSM Parameter Store

But that is not required for the first CDK version.

## CDK Project Structure

Recommended structure:

```text
cdk/
  app.py
  cdk.json
  requirements.txt
  .env.cdk.example
  config_loader.py
  task_flow_stack.py
  cdk_constructs/
    network.py
    storage.py
    observability.py
    cluster.py
    discovery.py
    load_balancer.py
    services.py
```

We are using one stack, but helper constructs are still useful for keeping the code readable.

## What `TaskFlowStack` Should Create

### 1. VPC and networking

- VPC across at least 2 Availability Zones
- public subnets for ALB
- public workload subnets for ECS EC2 instances
- internet gateway
- route tables

We should avoid NAT Gateway for now to keep costs low.

For the first low-cost version, the practical choice is:

- ALB in public subnets
- ECS EC2 instances in public workload subnets with controlled security groups
- `api-service` exposed only through the ALB
- `worker-service`, `postgres`, `redis`, and `rabbitmq` kept internal by security-group exposure

This is not the most production-hardened design, but it is simpler and cheaper than introducing NAT Gateways.

### 2. Security groups

At minimum:

- ALB security group
- ECS instance security group

Allowed traffic:

- internet -> ALB on `80`
- ALB -> `api-service`
- ECS internal traffic for:
  - `postgres`
  - `redis`
  - `rabbitmq`
- outbound internet for:
  - S3 access
  - package/service APIs such as Resend and OpenRouter

### 3. ECS cluster and EC2 capacity

- ECS cluster
- Auto Scaling Group with:
  - desired capacity `5`
  - min capacity `5`
  - max capacity `5`
  - instance type `t3.small`
- ECS-optimized AMI
- capacity provider attached to the cluster
- IAM instance role/profile for ECS EC2 instances

The EC2 instance role should include what is needed for:

- ECS agent
- CloudWatch logs
- S3 object access for app containers if accessed through instance role or task role

### 4. S3 bucket

One private S3 bucket for:

- `uploads/tmp/...`
- `uploads/tasks/...`
- `outputs/...`

Recommended settings:

- private bucket
- block public access
- versioning optional
- lifecycle rules optional for later

Bucket name can come from `.env.cdk`, or CDK can generate one and expose it as an output. Since the app expects env-driven config, using `.env.cdk` for the bucket name is fine.

### 5. CloudWatch log groups

Create log groups for:

- `api-service`
- `worker-service`
- `postgres`
- `redis`
- `rabbitmq`

Recommended:

- explicit retention period
- predictable names

### 6. Application Load Balancer

- internet-facing ALB
- HTTP listener on port `80`
- target group for `api-service`
- health check path:
  - `/health`

The ALB only routes to `api-service`.

No public route is needed for:

- `worker-service`
- `postgres`
- `redis`
- `rabbitmq`

### 7. ECS task definitions and services

#### `api-service`

- ECS service
- desired count `1`
- registered in ALB target group
- environment from `.env.cdk`
- image from `task-flow-api:<tag>`

Needs:

- S3 bucket env vars
- Postgres connection env vars
- Redis connection env vars
- RabbitMQ connection env vars

#### `worker-service`

- ECS service
- desired count `1`
- no public ingress
- image from `task-flow-worker:<tag>`

Needs:

- S3 bucket env vars
- Postgres connection env vars
- RabbitMQ connection env vars
- Resend/OpenRouter env vars
- worker temp directory env var

#### `postgres`

- ECS service
- desired count `1`
- internal only

We need to decide storage handling in implementation:

- cheapest path: ephemeral container storage
- better path: attach EBS-backed persistence

For the first version, document clearly whether data is disposable or persistent.

#### `redis`

- ECS service
- desired count `1`
- internal only

Can likely be treated as disposable in the first version.

#### `rabbitmq`

- ECS service
- desired count `1`
- internal only

Also needs credentials from `.env.cdk`.

## Service Discovery / Internal Addressing

The app needs stable internal hostnames for:

- `postgres`
- `redis`
- `rabbitmq`

Recommended first approach:

- use ECS service discovery with AWS Cloud Map
- or use fixed internal DNS/service naming supported by ECS networking choices

This should be kept simple and explicit in implementation.

## Environment Variable Plan

### `api-service`

Expected categories:

- app port
- database config
- Redis config
- RabbitMQ config
- S3 config
- rate limiting config

### `worker-service`

Expected categories:

- app port
- database config
- RabbitMQ config
- S3 config
- worker runtime config
- email config
- OpenRouter config

### Example values CDK should set

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `REDIS_URL`
- `RABBITMQ_URL`
- `S3_REGION`
- `S3_BUCKET`
- `AWS_REGION`
- `RESEND_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `WORKER_WORK_ROOT`

## Docker / Build Expectations

CDK will assume Docker images already exist in ECR.

Before deployment:

1. build `api-service` image
2. build `worker-service` image
3. push `task-flow-api:<tag>`
4. push `task-flow-worker:<tag>`
5. set the image tags in `.env.cdk`
6. run `cdk deploy`

## Recommended Implementation Order

1. Create `cdk/` CDK project in Python.
2. Add `.env.cdk.example` and config loader.
3. Build `TaskFlowStack` skeleton.
4. Add VPC, security groups, ALB.
5. Add ECS cluster and ASG.
6. Add S3 bucket.
7. Add CloudWatch log groups.
8. Add ECS task definitions and services.
9. Add internal connectivity for Postgres, Redis, RabbitMQ.
10. Add stack outputs:
   - ALB DNS name
   - bucket name
   - cluster name
11. Deploy to a test AWS account.
12. Validate:
   - UI loads
   - API works
   - uploads work
   - worker processes tasks
   - artifacts download from S3-backed flow

## Risks and Tradeoffs

### Cost-first tradeoffs

This design is intentionally low cost, but it has tradeoffs:

- Postgres on ECS is not as reliable as RDS
- Redis on ECS is not as reliable as ElastiCache
- RabbitMQ on ECS is more operationally fragile than a managed service
- ECS EC2 in public subnets is simpler and cheaper, but less ideal than private subnets plus NAT

### Operational tradeoffs

- `.env.cdk` is simple, but not the strongest secret-management model
- one stack is easier now, but may get large later
- soft placement is simpler, but not perfectly predictable

## Future Improvements

Later improvements could include:

- move secrets to Secrets Manager
- move Postgres to RDS
- move Redis to ElastiCache
- keep RabbitMQ or reevaluate queue architecture
- serve frontend from S3 and optionally CloudFront
- move ECS EC2 instances to private subnets with NAT or VPC endpoints
- add HTTPS with ACM and Route53
- split one stack into multiple stacks if needed

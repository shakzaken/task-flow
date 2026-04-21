# AWS CDK Plan

## Goal

Create an AWS CDK project in Python that deploys this application to AWS with a low-cost ECS on EC2 architecture.

This plan follows the current decisions:

- Use AWS CDK in Python
- Use ECS with the EC2 launch type
- Use 5 EC2 instances
- Use S3 for file/object storage
- Do not use CloudFront
- Keep PostgreSQL, Redis, and RabbitMQ on ECS tasks instead of managed AWS database/cache/message services
- Use one primary service per EC2 instance
- Create and push ECR images manually outside CDK
- Initially serve the frontend through `api-service`
- Keep both local filesystem storage and S3 storage supported
- Use environment variables for secrets in ECS task definitions
- Keep RabbitMQ as RabbitMQ

## Planned AWS Architecture

### Compute

- 1 ECS cluster
- 1 Auto Scaling Group with 5 EC2 instances
- 1 capacity provider connected to the ECS cluster
- ECS tasks scheduled onto those 5 instances

### Application services

- `api-service`
  - ECS service
  - Internet-facing through an ALB
  - Initially also serves the built frontend assets
- `worker-service`
  - ECS service
  - No public ingress
- `postgres`
  - ECS service or ECS task with persistent EBS-backed storage strategy
- `redis`
  - ECS service
- `rabbitmq`
  - ECS service

### Frontend delivery decision

Initial plan:

- do not run `frontend-service` as a separate public runtime service in AWS
- build the frontend statically
- package the built frontend with `api-service` and serve it from the API container

Later option:

- move frontend hosting to S3
- optionally add CloudFront later if needed

### Storage

- S3 bucket for uploaded files and generated artifacts
- EBS volumes for stateful container workloads that need persistence:
  - PostgreSQL
  - RabbitMQ
  - potentially Redis if persistence is enabled

### Networking

- 1 VPC
- public subnets for ALB
- private subnets for ECS instances if possible
- security groups for:
  - ALB
  - ECS instances
  - internal service-to-service traffic

### Access path

- Browser -> ALB -> `api-service` for both frontend assets and API routes
- `api-service` -> RabbitMQ
- `worker-service` -> RabbitMQ
- `api-service` / `worker-service` -> PostgreSQL
- `api-service` / `worker-service` -> Redis
- `api-service` / `worker-service` -> S3

## CDK Project Structure

Planned CDK app layout:

```text
infrastructure/
  app.py
  cdk.json
  requirements.txt
  stacks/
    network_stack.py
    storage_stack.py
    cluster_stack.py
    service_stack.py
    observability_stack.py
  constructs/
    ecs_service.py
    ecs_stateful_service.py
    security.py
    task_definition_factory.py
```

## Stack Plan

### 1. `NetworkStack`

Creates:

- VPC
- subnets
- internet gateway / route tables
- security groups
- ALB

Responsibilities:

- expose HTTP entry points
- isolate internal services
- define allowed ports:
  - frontend
  - api
  - postgres
  - redis
  - rabbitmq

### 2. `StorageStack`

Creates:

- S3 bucket for app uploads and outputs
- optional bucket policies
- optional lifecycle rules

Responsibilities:

- hold uploaded files
- hold generated files such as resized images, merged PDFs, and summarized PDFs

### 3. `ClusterStack`

Creates:

- ECS cluster
- Auto Scaling Group with 5 EC2 instances
- ECS capacity provider
- instance profile / IAM role
- ECS-optimized AMI selection

Responsibilities:

- provide the 5 EC2 instances used by all ECS services
- install ECS agent through the standard ECS-optimized AMI path

Initial assumption:

- Use `t3.small` for all 5 ECS EC2 instances

### 4. `ServiceStack`

Creates task definitions and ECS services for:

- `api-service`
- `worker-service`
- `postgres`
- `redis`
- `rabbitmq`

Responsibilities:

- environment variables
- task roles
- log groups
- port mappings
- service discovery or internal DNS usage
- ALB target groups for API and frontend asset delivery through `api-service`

### 5. `ObservabilityStack`

Creates:

- CloudWatch log groups
- alarms for instance health
- alarms for ALB target health
- optional CPU and memory alarms

## ECS Placement Plan

Target layout with 5 EC2 instances:

1. Instance 1: `api-service`
2. Instance 2: `worker-service`
3. Instance 3: `postgres`
4. Instance 4: `redis`
5. Instance 5: `rabbitmq`

This is the simplest mental model and matches the current 5-instance requirement while keeping one primary service per instance.

Alternative later optimization:

- pack multiple services onto fewer instances and keep spare capacity
- but the initial CDK plan should assume one primary service per instance

## Container Image Strategy

The CDK project should expect Docker images for:

- `api-service`
- `worker-service`
- `postgres`
- `redis`
- `rabbitmq`

Planned image source:

- ECR repositories created manually outside CDK
- images built and pushed manually or by CI/CD outside CDK

CDK responsibility:

- reference existing ECR repository names and tags
- deploy ECS services using those images

## Configuration and Secrets

Use:

- ECS task environment variables for both non-secret config and secrets

Secrets to manage:

- PostgreSQL credentials
- Redis password if enabled
- RabbitMQ credentials
- `RESEND_API_KEY`
- `OPENROUTER_API_KEY`

Non-secret config:

- ports
- bucket names
- service URLs
- `EMAIL_PROVIDER_MODE`
- `OPENROUTER_MODEL`
- `REDIS_URL`

Important note:

- this is simple and matches the current preference
- it is less secure than using Secrets Manager or SSM Parameter Store
- CDK should keep secret values configurable per environment and never hardcode them in source control

Current decision:

- all environment variables will be configured in CDK before deployment

## Persistence Strategy

### PostgreSQL

Needs durable storage.

Plan:

- mount persistent storage to the Postgres container
- if staying on ECS EC2, this is the riskiest stateful component

Important note:

- ECS on EC2 is not ideal for self-hosted PostgreSQL
- this plan accepts that tradeoff to minimize AWS managed-service cost

### Redis

Plan:

- start with non-critical persistence assumptions
- can run without strong durability if used for cache/rate limiting

### RabbitMQ

Plan:

- enable persistence if task durability matters
- mount storage if message durability is required

## Frontend Serving Plan

Because the initial AWS deployment will serve the frontend through `api-service`, the application needs an app-level adjustment before or alongside CDK work.

Planned changes:

1. build the React frontend during image creation
2. copy the frontend build output into the `api-service` image
3. update `api-service` to serve static frontend assets
4. keep API routes working under a predictable prefix such as `/api` if needed
5. make client-side routing fall back to `index.html`

This keeps the first AWS deployment simpler and avoids a separate frontend runtime service.

Later migration path:

- move static frontend hosting to S3
- optionally add CloudFront later
- keep `api-service` as API-only if desired

## Storage Migration Plan: Local Filesystem And S3

We also need a clear plan for migrating storage from the current local filesystem model to S3 without breaking local development.

### Goal

Support two storage modes:

1. local filesystem mode for local development
2. S3-backed mode for AWS deployment

### Design approach

Use the existing storage abstraction and extend it so the app can switch based on configuration.

Planned model:

- `STORAGE_MODE=local`
  - existing local file behavior
  - used in local development
- `STORAGE_MODE=s3`
  - uploads and generated artifacts stored in S3
  - used in AWS

### API-service changes

The API service should support both implementations through the same interface:

- store temporary uploads
- attach uploads to task scope
- generate artifact references
- download artifact content

Likely implementation:

- keep current local storage service
- add an S3 storage service
- choose implementation based on settings

### Worker-service changes

The worker currently expects filesystem access for inputs and outputs.

For S3 mode, the worker will need a local working directory plus S3 transfer steps:

1. download task input objects from S3 to local temp disk
2. process files locally
3. upload outputs back to S3
4. save S3-backed artifact references in task results

This means the worker storage abstraction also needs a dual implementation or a hybrid local-workdir plus remote-storage model.

### Recommended migration strategy

Phase 1:

- keep local mode unchanged
- add S3 mode behind the same interface
- make AWS use only S3 mode

Phase 2:

- verify all file-producing tasks work with S3:
  - resize image
  - merge PDFs
  - summarize PDF

Phase 3:

- optionally remove assumptions in handlers that inputs are always on the shared local filesystem

### CDK implications

The CDK project should provision:

- S3 bucket
- IAM permissions for `api-service` and `worker-service`
- environment variables required for S3 mode

The CDK project should not assume local shared disk for cross-service file passing in AWS.

## Load Balancer Plan

Use one ALB that routes all application traffic to `api-service` initially.

Within `api-service`:

- API routes should remain under explicit API paths
- frontend assets and SPA fallback should be served by the same container

Later, if the frontend moves to S3, the routing model can be simplified again.

## IAM Plan

### ECS instance role

Needs permissions for:

- ECS cluster registration
- CloudWatch logs
- pulling images from ECR

### Task roles

`api-service` task role:

- S3 read/write

`worker-service` task role:

- S3 read/write

## Deployment Order

Recommended deployment flow:

1. Adjust `api-service` to serve frontend assets
2. Extend storage abstraction to support both local and S3 modes
3. Deploy network stack
4. Deploy storage stack
5. Deploy cluster stack
6. Build and push container images
7. Deploy service stack
8. Deploy observability stack

## Open Questions To Resolve During CDK Implementation

These are the main decisions still worth confirming:

No open questions remain at the planning level for the initial CDK document.

## Recommendation

For the first CDK version:

- keep the project modular
- model the 5-instance layout explicitly
- use one ECS cluster with 5 EC2 instances
- use `t3.small` for all 5 instances
- use one ALB
- use S3 for artifacts
- keep local mode working alongside S3 mode
- serve the frontend through `api-service` first
- use ECS environment variables for secrets initially
- document clearly that self-hosting PostgreSQL/Redis/RabbitMQ on ECS is cost-focused, not reliability-focused

## Suggested Next Step

After this document is approved, the next implementation step should be:

- scaffold `infrastructure/` as a Python CDK app
- create `NetworkStack`, `StorageStack`, and `ClusterStack` first
- then add the ECS services one by one

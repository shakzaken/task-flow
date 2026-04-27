# AWS CDK Tasks

## Purpose

This document breaks the CDK plan into implementation tasks and subtasks.

The goal is to make the work sequential, testable, and easy to track while building the first AWS deployment for this project.

## Phase 1: Prepare the CDK project

### Task 1. Create the CDK project skeleton

- [x] Create `cdk/` directory.
- [x] Initialize an AWS CDK project in Python.
- [x] Add `app.py`.
- [x] Add `cdk.json`.
- [x] Add `requirements.txt`.
- [x] Add a stack module for `TaskFlowStack`.
- [x] Confirm `cdk synth` works with an empty stack.

### Task 2. Add local CDK config files

- [x] Create `cdk/.env.cdk.example`.
- [x] Add `cdk/.env.cdk` to `.gitignore`.
- [x] Define all required config keys in `.env.cdk.example`.
- [x] Decide which config keys are required and which can have defaults.
- [x] Add a small config loader module for `.env.cdk`.
- [x] Validate config at synth/deploy time with clear error messages.

### Task 3. Document CDK prerequisites

- [x] List required tools:
  - AWS CLI
  - CDK CLI
  - Python version
- [x] Document AWS credentials requirement.
- [x] Document manual ECR requirement.
- [x] Document required `.env.cdk` values before deploy.

## Phase 2: Networking and shared AWS resources

### Task 4. Create the VPC

- [x] Add VPC resource to `TaskFlowStack`.
- [x] Create public subnets for the ALB.
- [x] Create ECS instance subnets for the first version without NAT.
- [x] Add internet gateway and routing.
- [x] Output important VPC values if useful.

### Task 5. Finalize subnet strategy

- [x] Confirm we do not use NAT.
- [x] Confirm ALB runs in public subnets.
- [x] Confirm ECS EC2 instances need outbound internet access.
- [x] Confirm the first version uses ECS EC2 instances in public subnets.
- [x] Treat internal services as private by security-group exposure, not by direct internet access.

### Task 6. Create security groups

- [x] Create one public security group for the ALB.
- [x] Create one private security group for ECS instances and ECS services.
- [x] Allow inbound HTTP from internet to ALB on port `80`.
- [x] Allow the ALB to reach `api-service`.
- [x] Allow ECS internal service-to-service traffic.
- [x] Do not allow direct inbound internet access to ECS services.
- [x] Keep `api-service` public only through the ALB.
- [x] Keep `worker-service`, `postgres`, `redis`, and `rabbitmq` private.

### Task 7. Create the S3 bucket

- [x] Add the application S3 bucket.
- [x] Make the bucket private.
- [x] Block public access.
- [x] Do not enable versioning.
- [x] Do not add lifecycle rules for now.
- [x] Add bucket name to stack outputs if useful.

### Task 8. Create CloudWatch log groups

- [x] Create a log group for `api-service`.
- [x] Create a log group for `worker-service`.
- [x] Create a log group for `postgres`.
- [x] Create a log group for `redis`.
- [x] Create a log group for `rabbitmq`.
- [x] Set explicit retention periods.

## Phase 3: ECS cluster and EC2 capacity

### Task 9. Create the ECS cluster

- [x] Add ECS cluster resource.
- [x] Name the cluster clearly.
- [x] Confirm the cluster can accept EC2 capacity.

### Task 10. Create the EC2 Auto Scaling Group

- [x] Add one Auto Scaling Group.
- [x] Set desired capacity to `5`.
- [x] Set min capacity to `5`.
- [x] Set max capacity to `5`.
- [x] Use `t3.small`.
- [x] Use ECS-optimized AMI.
- [x] Attach instance profile and IAM role.

### Task 11. Attach ECS capacity provider

- [x] Add ECS capacity provider backed by the Auto Scaling Group.
- [x] Attach the capacity provider to the ECS cluster.
- [x] Confirm ECS services can use it by default.

### Task 12. Add IAM roles and permissions

- [x] Add EC2 instance role for ECS instances.
- [x] Add permissions needed for ECS agent operation.
- [x] Add permissions for CloudWatch logs.
- [x] Decide whether app containers should use task roles for S3 instead of the instance role.
- [x] Add S3 permissions at the chosen role boundary.
- [x] Add task roles for `api-service` and `worker-service` if needed.

## Phase 4: Load balancing and public entrypoint

### Task 13. Create the ALB

- [x] Add one internet-facing Application Load Balancer.
- [x] Add listener on port `80`.
- [x] Add target group for `api-service`.
- [x] Configure health check path `/health`.
- [x] Output the ALB DNS name.

### Task 14. Wire the ALB to `api-service`

- [x] Confirm container port mapping for `api-service`.
- [x] Register the ECS service in the ALB target group.
- [x] Confirm health checks match the real API route.
- [x] Make sure `api-service` is public only through the ALB.
- [x] Confirm the container and EC2 instances are not directly exposed.

## Phase 5: Stateful and stateless ECS services

### Task 15. Define the `api-service` task definition

- [x] Reference image from `task-flow-api`.
- [x] Read image tag from `.env.cdk`.
- [x] Set CPU and memory values.
- [x] Add port mapping.
- [x] Add environment variables.
- [x] Add S3 config.
- [x] Add DB config.
- [x] Add Redis config.
- [x] Add RabbitMQ config.
- [x] Add CloudWatch logs config.

### Task 16. Define the `worker-service` task definition

- [x] Reference image from `task-flow-worker`.
- [x] Read image tag from `.env.cdk`.
- [x] Set CPU and memory values.
- [x] Add environment variables.
- [x] Add S3 config.
- [x] Add DB config.
- [x] Add RabbitMQ config.
- [x] Add Resend config.
- [x] Add OpenRouter config.
- [x] Add worker temp directory config.
- [x] Add CloudWatch logs config.

### Task 17. Define the `postgres` task definition

- [x] Select container image.
- [x] Set container port.
- [x] Set environment variables.
- [x] Add CloudWatch logs config.
- [x] Decide whether storage is ephemeral for the first version or persistent from day one.
- [x] If persistent, choose the storage mechanism.

### Task 18. Define the `redis` task definition

- [x] Select container image.
- [x] Set container port.
- [x] Add CloudWatch logs config.
- [x] Decide whether persistence is needed in the first version.

### Task 19. Define the `rabbitmq` task definition

- [x] Select container image.
- [x] Set container port.
- [x] Add management port only if needed internally.
- [x] Set credentials from `.env.cdk`.
- [x] Add CloudWatch logs config.
- [x] Decide whether persistence is needed in the first version.

### Task 20. Create ECS services for all containers

- [x] Create ECS service for `api-service`.
- [x] Create ECS service for `worker-service`.
- [x] Create ECS service for `postgres`.
- [x] Create ECS service for `redis`.
- [x] Create ECS service for `rabbitmq`.
- [x] Set desired counts.
- [x] Confirm internal reachability between services.
- [x] Confirm only `api-service` is reachable through the ALB.
- [x] Confirm the rest are internal only.

## Phase 6: Internal connectivity and configuration

### Task 21. Implement service discovery with Cloud Map

- [x] Add ECS service discovery with Cloud Map.
- [x] Create a namespace for internal services.
- [x] Register `postgres` in Cloud Map.
- [x] Register `redis` in Cloud Map.
- [x] Register `rabbitmq` in Cloud Map.
- [x] Decide whether `api-service` and `worker-service` also need Cloud Map registration.

### Task 22. Wire internal hostnames

- [x] Provide stable Cloud Map hostnames for `postgres`.
- [x] Provide stable Cloud Map hostnames for `redis`.
- [x] Provide stable Cloud Map hostnames for `rabbitmq`.
- [x] Map those hostnames into `api-service` env vars.
- [x] Map those hostnames into `worker-service` env vars.

### Task 23. Implement `.env.cdk` mapping

- [x] Read `.env.cdk` values in CDK.
- [x] Map config into ECS task definitions.
- [x] Separate app config from infrastructure config logically.
- [x] Validate that missing required values fail fast.

### Task 24. Decide secret handling for first version

- [x] Confirm `.env.cdk` is acceptable for first deploy.
- [x] Keep `.env.cdk` ignored by git.
- [x] Keep `.env.cdk.example` committed.
- [x] Mark which values are sensitive.
- [x] Document future migration path to Secrets Manager.

## Phase 7: Deployment flow and manual image process

### Task 25. Document manual ECR setup

- [x] Document creating `task-flow-api`.
- [x] Document creating `task-flow-worker`.
- [x] Document authenticating Docker to ECR.

### Task 26. Document image build and push flow

- [x] Build `api-service` image.
- [x] Build `worker-service` image.
- [x] Tag both images.
- [x] Push both images to ECR.
- [x] Set the image tags in `.env.cdk`.

### Task 27. Add deploy instructions

- [x] Document Python dependency install for CDK.
- [x] Document `cdk synth`.
- [x] Document `cdk deploy`.
- [x] Document how to destroy the stack.
- [x] Document what outputs to expect after deploy.

## Phase 8: Validation and testing

### Task 28. Validate infrastructure synthesis

- [x] Run `cdk synth`.
- [x] Review the generated template.
- [x] Confirm all major resources are present.
- [x] Confirm there are no missing config values.

Note:
- Tasks 29 to 31 require a real AWS account, bootstrapped CDK environment, and pushed ECR images.

### Task 29. Deploy to AWS and validate stack health

- [ ] Run `cdk deploy`.
- [ ] Confirm ECS cluster is created.
- [ ] Confirm all `5` EC2 instances join the cluster.
- [ ] Confirm all ECS services become stable.
- [ ] Confirm ALB target becomes healthy.

### Task 30. Validate application behavior in AWS

- [ ] Open the ALB DNS name in a browser.
- [ ] Confirm frontend loads.
- [ ] Confirm API health route works.
- [ ] Confirm file upload works.
- [ ] Confirm task creation works.
- [ ] Confirm worker consumes jobs.
- [ ] Confirm artifact download works.

### Task 31. Validate object storage behavior

- [ ] Confirm uploads land in S3.
- [ ] Confirm outputs land in S3.
- [ ] Confirm artifact downloads still work through `api-service`.
- [ ] Confirm no MinIO-specific behavior remains in AWS config.

## Phase 9: Follow-up hardening

### Task 32. Review cost and cleanup

- [ ] Confirm no unnecessary resources were created.
- [ ] Review ALB, EC2, EBS, S3, and CloudWatch cost drivers.
- [ ] Decide whether any service can be downsized further.

### Task 33. Review reliability tradeoffs

- [ ] Reassess Postgres on ECS.
- [ ] Reassess Redis on ECS.
- [ ] Reassess RabbitMQ on ECS.
- [ ] Decide what should later move to managed AWS services.

### Task 34. Plan future security improvements

- [ ] Move secrets from `.env.cdk` to Secrets Manager.
- [ ] Add HTTPS with ACM.
- [ ] Add Route53 if a custom domain is introduced.
- [ ] Consider moving ECS EC2 instances to private subnets later.

## First recommended execution order

If we want the shortest path to the first deployment, we should do the work in this order:

- [ ] Task 1
- [ ] Task 2
- [ ] Task 4
- [ ] Task 5
- [ ] Task 6
- [ ] Task 7
- [ ] Task 9
- [ ] Task 10
- [ ] Task 11
- [ ] Task 13
- [ ] Task 15
- [ ] Task 16
- [ ] Task 17
- [ ] Task 18
- [ ] Task 19
- [ ] Task 20
- [ ] Task 21
- [ ] Task 22
- [ ] Task 23
- [x] Task 28
- [ ] Task 29
- [ ] Task 30
- [ ] Task 31

## Notes

- Keep the first version simple.
- Prefer deployability over perfect infrastructure design.
- Write down every AWS compromise clearly so we can improve it later without confusion.

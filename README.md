# Task Flow

## Overview

Task Flow gives users a simple place to submit file-based jobs and get back a finished result without waiting for the work to happen in the browser. A user can upload documents or images, choose an operation, and later return to see the task status and download the generated output. The overall experience is centered on turning common document workflows into queued background tasks that are easy to run through a web interface.

Under the hood, the application uses a React UI, an API service, and a worker service. The API stores task state in PostgreSQL, publishes work to RabbitMQ, and saves files in object storage, while the worker consumes queued tasks and performs operations such as image resize, PDF merge, PDF summary generation, and email sending. For local development the project runs with Docker, MinIO, PostgreSQL, Redis, and RabbitMQ, and for AWS deployment it uses the CDK project in this repository.

## Technologies

- Python 3.13
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- RabbitMQ
- Redis
- S3-compatible object storage via MinIO locally and Amazon S3 in AWS
- React
- TypeScript
- Vite
- Docker and Docker Compose
- AWS CDK
- Amazon ECS on EC2

## Services

### frontend-service

`frontend-service` is the React application for the user interface. It lets users upload files, create tasks, check task progress, and download generated artifacts. In local non-Docker development it can run as its own Vite app, and in the integrated deployment flow its built static files are served by `api-service`.

### api-service

`api-service` is the main backend entrypoint of the system. It exposes the HTTP API, validates requests, manages task creation and lookup, publishes jobs to RabbitMQ, serves generated artifacts, applies rate limiting, and runs Alembic migrations on startup so the database schema is ready before the app begins serving traffic.

### worker-service

`worker-service` is the background execution layer. It consumes queued tasks from RabbitMQ, downloads the required input files from object storage, performs the actual processing work, uploads the output artifacts, updates task state, and integrates with external providers such as Resend for email and OpenRouter for PDF summarization.

### cdk

`cdk` contains the AWS infrastructure definition for the project. Its role is to provision the cloud environment needed to run the application on AWS, including networking, ECS capacity, the load balancer, Cloud Map service discovery, log groups, IAM roles, and the S3 bucket used by the application in production.

## Running And Deployment

For local setup and AWS deployment steps, see [deployment.md](/Users/yakir/projects/claude/task-flow/deployment.md).

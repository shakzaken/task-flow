#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

API_REPOSITORY="${API_REPOSITORY:-task-flow-api}"
WORKER_REPOSITORY="${WORKER_REPOSITORY:-task-flow-worker}"
AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region 2>/dev/null || true)}}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text 2>/dev/null || true)}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DOCKER_PLATFORM="${DOCKER_PLATFORM:-linux/amd64}"

if [[ -z "$AWS_REGION" ]]; then
  echo "AWS region is not set. Export AWS_REGION or AWS_DEFAULT_REGION, or configure one with aws configure." >&2
  exit 1
fi

if [[ -z "$AWS_ACCOUNT_ID" ]]; then
  echo "AWS account ID could not be resolved. Make sure aws configure is set up and aws sts get-caller-identity works." >&2
  exit 1
fi

ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
API_LOCAL_IMAGE="${API_REPOSITORY}:${IMAGE_TAG}"
WORKER_LOCAL_IMAGE="${WORKER_REPOSITORY}:${IMAGE_TAG}"
API_REMOTE_IMAGE="${ECR_REGISTRY}/${API_REPOSITORY}:${IMAGE_TAG}"
WORKER_REMOTE_IMAGE="${ECR_REGISTRY}/${WORKER_REPOSITORY}:${IMAGE_TAG}"

echo "Using AWS account: ${AWS_ACCOUNT_ID}"
echo "Using AWS region:  ${AWS_REGION}"
echo "Using image tag:   ${IMAGE_TAG}"
echo "Using platform:    ${DOCKER_PLATFORM}"

echo "Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"

echo "Building API image..."
docker build \
  --platform "$DOCKER_PLATFORM" \
  -f "$REPO_ROOT/api-service/Dockerfile" \
  -t "$API_LOCAL_IMAGE" \
  "$REPO_ROOT"

echo "Tagging and pushing API image..."
docker tag "$API_LOCAL_IMAGE" "$API_REMOTE_IMAGE"
docker push "$API_REMOTE_IMAGE"

echo "Building worker image..."
docker build \
  --platform "$DOCKER_PLATFORM" \
  -f "$REPO_ROOT/worker-service/Dockerfile" \
  -t "$WORKER_LOCAL_IMAGE" \
  "$REPO_ROOT"

echo "Tagging and pushing worker image..."
docker tag "$WORKER_LOCAL_IMAGE" "$WORKER_REMOTE_IMAGE"
docker push "$WORKER_REMOTE_IMAGE"

cat <<EOF

Pushed images successfully.

API image:
  $API_REMOTE_IMAGE

Worker image:
  $WORKER_REMOTE_IMAGE

Use this tag in cdk/.env.cdk:
  API_IMAGE_TAG=$IMAGE_TAG
  WORKER_IMAGE_TAG=$IMAGE_TAG
EOF

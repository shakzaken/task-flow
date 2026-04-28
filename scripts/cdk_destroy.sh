#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CDK_DIR="$REPO_ROOT/cdk"
ENV_FILE="$CDK_DIR/.env.cdk"
ORIGINAL_HOME="${HOME:-}"
AWS_SHARED_CREDENTIALS_FILE="${AWS_SHARED_CREDENTIALS_FILE:-$ORIGINAL_HOME/.aws/credentials}"
AWS_CONFIG_FILE="${AWS_CONFIG_FILE:-$ORIGINAL_HOME/.aws/config}"
export AWS_SHARED_CREDENTIALS_FILE
export AWS_CONFIG_FILE
export HOME="$CDK_DIR/.home"

load_env_file() {
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue

    local key="${line%%=*}"
    local value="${line#*=}"

    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"

    export "$key=$value"
  done < "$ENV_FILE"
}

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE. Create it from cdk/.env.cdk.example before running this script." >&2
  exit 1
fi

if [[ ! -x "$CDK_DIR/.venv/bin/python" ]]; then
  echo "Missing CDK virtual environment at $CDK_DIR/.venv. Run 'cd cdk && UV_CACHE_DIR=../.uv-cache uv sync' first." >&2
  exit 1
fi

if [[ ! -x "$CDK_DIR/node_modules/.bin/cdk" ]]; then
  echo "Missing local CDK CLI at $CDK_DIR/node_modules/.bin/cdk. Run 'cd cdk && npm install' first." >&2
  exit 1
fi

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "AWS credentials are not available. Make sure aws configure is set up and aws sts get-caller-identity works." >&2
  exit 1
fi

load_env_file

STACK_NAME="${STACK_NAME:-TaskFlowStack}"
AWS_REGION="${AWS_REGION:-eu-west-1}"
CLUSTER_NAME="${APP_NAME}-cluster"
mkdir -p "$HOME"

cleanup_ecs_capacity_provider_usage() {
  local cluster_status
  cluster_status="$(aws ecs describe-clusters \
    --clusters "$CLUSTER_NAME" \
    --region "$AWS_REGION" \
    --query 'clusters[0].status' \
    --output text 2>/dev/null || true)"

  if [[ -z "$cluster_status" || "$cluster_status" == "None" || "$cluster_status" == "MISSING" || "$cluster_status" == "INACTIVE" ]]; then
    return 0
  fi

  local services_output
  services_output="$(aws ecs list-services \
    --cluster "$CLUSTER_NAME" \
    --region "$AWS_REGION" \
    --query 'serviceArns' \
    --output text 2>/dev/null || true)"

  if [[ -n "$services_output" && "$services_output" != "None" ]]; then
    echo "Deleting ECS services from cluster: $CLUSTER_NAME"
    read -r -a services <<<"$services_output"
    for service_arn in "${services[@]}"; do
      aws ecs delete-service \
        --cluster "$CLUSTER_NAME" \
        --service "$service_arn" \
        --force \
        --region "$AWS_REGION" \
        >/dev/null
    done

    aws ecs wait services-inactive \
      --cluster "$CLUSTER_NAME" \
      --services "${services[@]}" \
      --region "$AWS_REGION"
  fi

  local capacity_providers
  capacity_providers="$(aws ecs describe-clusters \
    --clusters "$CLUSTER_NAME" \
    --region "$AWS_REGION" \
    --query 'clusters[0].capacityProviders' \
    --output text 2>/dev/null || true)"

  if [[ -n "$capacity_providers" && "$capacity_providers" != "None" ]]; then
    echo "Clearing ECS capacity provider associations from cluster: $CLUSTER_NAME"
    aws ecs put-cluster-capacity-providers \
      --cluster "$CLUSTER_NAME" \
      --capacity-providers "[]" \
      --default-capacity-provider-strategy "[]" \
      --region "$AWS_REGION" \
      >/dev/null
  fi
}

cleanup_ecs_capacity_provider_usage

cd "$CDK_DIR"

echo "Destroying stack: $STACK_NAME"
./node_modules/.bin/cdk destroy "$STACK_NAME" --force

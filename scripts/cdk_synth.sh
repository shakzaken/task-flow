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

load_env_file

STACK_NAME="${STACK_NAME:-TaskFlowStack}"
OUTPUT_DIR="$CDK_DIR/cdk.out"
TEMPLATE_FILE="$OUTPUT_DIR/${STACK_NAME}.template.json"
MAX_TEMPLATE_BODY_BYTES=51200

mkdir -p "$OUTPUT_DIR"
mkdir -p "$HOME"

cd "$CDK_DIR"

echo "Synthesizing CloudFormation template for stack: $STACK_NAME"
./node_modules/.bin/cdk synth "$STACK_NAME" --json --output "$OUTPUT_DIR" > "$TEMPLATE_FILE"

echo "Checking generated JSON template..."
python3 -m json.tool "$TEMPLATE_FILE" >/dev/null

TEMPLATE_SIZE_BYTES="$(wc -c < "$TEMPLATE_FILE" | tr -d ' ')"

if [[ "$TEMPLATE_SIZE_BYTES" -le "$MAX_TEMPLATE_BODY_BYTES" ]]; then
  if aws sts get-caller-identity >/dev/null 2>&1; then
    echo "Validating template with AWS CloudFormation..."
    aws cloudformation validate-template --template-body "file://$TEMPLATE_FILE" >/dev/null
    VALIDATION_MESSAGE="AWS CloudFormation inline validation passed."
  else
    VALIDATION_MESSAGE="Skipped AWS ValidateTemplate because AWS credentials are not available in this shell."
  fi
else
  VALIDATION_MESSAGE="Skipped AWS ValidateTemplate because the synthesized template is ${TEMPLATE_SIZE_BYTES} bytes, and CloudFormation inline validation only accepts up to ${MAX_TEMPLATE_BODY_BYTES} bytes."
fi

cat <<EOF

CloudFormation template generated and validated successfully.

Template file:
  $TEMPLATE_FILE

$VALIDATION_MESSAGE
EOF

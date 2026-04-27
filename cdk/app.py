from __future__ import annotations

import aws_cdk as cdk

from config_loader import load_app_config
from task_flow_stack import TaskFlowStack


app = cdk.App()
config = load_app_config()

stack_env = cdk.Environment(
    account=config.aws_account,
    region=config.aws_region,
)

TaskFlowStack(
    app,
    config.stack_name,
    config=config,
    env=stack_env,
)

app.synth()

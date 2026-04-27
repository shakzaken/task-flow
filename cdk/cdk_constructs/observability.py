from __future__ import annotations

from dataclasses import dataclass

from aws_cdk import RemovalPolicy
from aws_cdk import aws_logs as logs
from constructs import Construct

from config_loader import AppConfig


@dataclass(frozen=True)
class ObservabilityResources:
    api_log_group: logs.LogGroup
    worker_log_group: logs.LogGroup
    postgres_log_group: logs.LogGroup
    redis_log_group: logs.LogGroup
    rabbitmq_log_group: logs.LogGroup


class ObservabilityConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, config: AppConfig) -> None:
        super().__init__(scope, construct_id)

        api_log_group = logs.LogGroup(
            self,
            "ApiServiceLogGroup",
            log_group_name=f"/{config.app_name}/api-service",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )
        worker_log_group = logs.LogGroup(
            self,
            "WorkerServiceLogGroup",
            log_group_name=f"/{config.app_name}/worker-service",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )
        postgres_log_group = logs.LogGroup(
            self,
            "PostgresLogGroup",
            log_group_name=f"/{config.app_name}/postgres",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )
        redis_log_group = logs.LogGroup(
            self,
            "RedisLogGroup",
            log_group_name=f"/{config.app_name}/redis",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )
        rabbitmq_log_group = logs.LogGroup(
            self,
            "RabbitMqLogGroup",
            log_group_name=f"/{config.app_name}/rabbitmq",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.resources = ObservabilityResources(
            api_log_group=api_log_group,
            worker_log_group=worker_log_group,
            postgres_log_group=postgres_log_group,
            redis_log_group=redis_log_group,
            rabbitmq_log_group=rabbitmq_log_group,
        )

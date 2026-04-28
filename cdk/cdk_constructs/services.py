from __future__ import annotations

from dataclasses import dataclass

from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from constructs import Construct

from cdk_constructs.cluster import ClusterResources
from cdk_constructs.discovery import DiscoveryResources
from cdk_constructs.load_balancer import LoadBalancerResources
from cdk_constructs.network import NetworkResources
from cdk_constructs.observability import ObservabilityResources
from cdk_constructs.storage import StorageResources
from config_loader import AppConfig


@dataclass(frozen=True)
class ServiceResources:
    api_service: ecs.Ec2Service
    worker_service: ecs.Ec2Service
    postgres_service: ecs.Ec2Service
    redis_service: ecs.Ec2Service
    rabbitmq_service: ecs.Ec2Service


class ServicesConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: AppConfig,
        network: NetworkResources,
        storage: StorageResources,
        observability: ObservabilityResources,
        cluster_resources: ClusterResources,
        discovery: DiscoveryResources,
        load_balancer: LoadBalancerResources,
    ) -> None:
        super().__init__(scope, construct_id)

        api_repository = ecr.Repository.from_repository_name(
            self,
            "ApiRepository",
            repository_name=config.api_image_repository,
        )
        worker_repository = ecr.Repository.from_repository_name(
            self,
            "WorkerRepository",
            repository_name=config.worker_image_repository,
        )

        api_task_definition = ecs.Ec2TaskDefinition(
            self,
            "ApiTaskDefinition",
            network_mode=ecs.NetworkMode.AWS_VPC,
            task_role=cluster_resources.api_task_role,
            execution_role=cluster_resources.task_execution_role,
        )
        api_container = api_task_definition.add_container(
            "ApiContainer",
            image=ecs.ContainerImage.from_ecr_repository(api_repository, tag=config.api_image_tag),
            cpu=256,
            memory_reservation_mib=512,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="api-service",
                log_group=observability.api_log_group,
            ),
            environment={
                "APP_ENVIRONMENT": "production",
                "CORS_ALLOWED_ORIGINS": config.cors_allowed_origins,
                "API_PORT": str(config.api_port),
                "POSTGRES_HOST": discovery.postgres_hostname,
                "POSTGRES_PORT": str(config.postgres_port),
                "POSTGRES_DB": config.postgres_db,
                "POSTGRES_USER": config.postgres_user,
                "POSTGRES_PASSWORD": config.postgres_password,
                "RABBITMQ_URL": (
                    f"amqp://{config.rabbitmq_default_user}:{config.rabbitmq_default_pass}"
                    f"@{discovery.rabbitmq_hostname}:{config.rabbitmq_port}/{config.rabbitmq_vhost}"
                ),
                "REDIS_URL": f"redis://{discovery.redis_hostname}:{config.redis_port}/0",
                "S3_REGION": config.aws_region,
                "S3_BUCKET": storage.artifacts_bucket.bucket_name,
                "S3_USE_SSL": "true",
                "S3_FORCE_PATH_STYLE": "false",
                "S3_AUTO_CREATE_BUCKET": "false",
            },
        )
        api_container.add_port_mappings(ecs.PortMapping(container_port=config.api_port))

        worker_task_definition = ecs.Ec2TaskDefinition(
            self,
            "WorkerTaskDefinition",
            network_mode=ecs.NetworkMode.AWS_VPC,
            task_role=cluster_resources.worker_task_role,
            execution_role=cluster_resources.task_execution_role,
        )
        worker_container = worker_task_definition.add_container(
            "WorkerContainer",
            image=ecs.ContainerImage.from_ecr_repository(worker_repository, tag=config.worker_image_tag),
            cpu=512,
            memory_reservation_mib=768,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="worker-service",
                log_group=observability.worker_log_group,
            ),
            environment={
                "WORKER_PORT": str(config.worker_port),
                "POSTGRES_HOST": discovery.postgres_hostname,
                "POSTGRES_PORT": str(config.postgres_port),
                "POSTGRES_DB": config.postgres_db,
                "POSTGRES_USER": config.postgres_user,
                "POSTGRES_PASSWORD": config.postgres_password,
                "RABBITMQ_URL": (
                    f"amqp://{config.rabbitmq_default_user}:{config.rabbitmq_default_pass}"
                    f"@{discovery.rabbitmq_hostname}:{config.rabbitmq_port}/{config.rabbitmq_vhost}"
                ),
                "WORKER_CONSUMER_QUEUE": config.rabbitmq_queue,
                "WORKER_MAX_CONCURRENCY": str(config.worker_max_concurrency),
                "RABBITMQ_PREFETCH_COUNT": str(config.rabbitmq_prefetch_count),
                "DB_POOL_SIZE": str(config.db_pool_size),
                "DB_MAX_OVERFLOW": str(config.db_max_overflow),
                "EMAIL_PROVIDER_MODE": config.email_provider_mode,
                "RESEND_API_KEY": config.resend_api_key,
                "RESEND_FROM_EMAIL": config.resend_from_email,
                "RESEND_FROM_NAME": config.resend_from_name,
                "S3_REGION": config.aws_region,
                "S3_BUCKET": storage.artifacts_bucket.bucket_name,
                "S3_USE_SSL": "true",
                "S3_FORCE_PATH_STYLE": "false",
                "S3_AUTO_CREATE_BUCKET": "false",
                "OUTPUT_STORAGE_PATH": config.output_storage_path,
                "WORKER_WORK_ROOT": config.worker_work_root,
                "OPENROUTER_API_KEY": config.openrouter_api_key,
                "OPENROUTER_MODEL": config.openrouter_model,
            },
        )
        worker_container.add_port_mappings(ecs.PortMapping(container_port=config.worker_port))

        postgres_task_definition = ecs.Ec2TaskDefinition(
            self,
            "PostgresTaskDefinition",
            network_mode=ecs.NetworkMode.AWS_VPC,
            execution_role=cluster_resources.task_execution_role,
        )
        postgres_container = postgres_task_definition.add_container(
            "PostgresContainer",
            image=ecs.ContainerImage.from_registry("postgres:16-alpine"),
            cpu=256,
            memory_reservation_mib=512,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="postgres",
                log_group=observability.postgres_log_group,
            ),
            environment={
                "POSTGRES_DB": config.postgres_db,
                "POSTGRES_USER": config.postgres_user,
                "POSTGRES_PASSWORD": config.postgres_password,
            },
        )
        postgres_container.add_port_mappings(ecs.PortMapping(container_port=config.postgres_port))

        redis_task_definition = ecs.Ec2TaskDefinition(
            self,
            "RedisTaskDefinition",
            network_mode=ecs.NetworkMode.AWS_VPC,
            execution_role=cluster_resources.task_execution_role,
        )
        redis_container = redis_task_definition.add_container(
            "RedisContainer",
            image=ecs.ContainerImage.from_registry("redis:7-alpine"),
            cpu=128,
            memory_reservation_mib=256,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="redis",
                log_group=observability.redis_log_group,
            ),
        )
        redis_container.add_port_mappings(ecs.PortMapping(container_port=config.redis_port))

        rabbitmq_task_definition = ecs.Ec2TaskDefinition(
            self,
            "RabbitMqTaskDefinition",
            network_mode=ecs.NetworkMode.AWS_VPC,
            execution_role=cluster_resources.task_execution_role,
        )
        rabbitmq_container = rabbitmq_task_definition.add_container(
            "RabbitMqContainer",
            image=ecs.ContainerImage.from_registry("rabbitmq:3.13-management-alpine"),
            cpu=256,
            memory_reservation_mib=512,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="rabbitmq",
                log_group=observability.rabbitmq_log_group,
            ),
            environment={
                "RABBITMQ_DEFAULT_USER": config.rabbitmq_default_user,
                "RABBITMQ_DEFAULT_PASS": config.rabbitmq_default_pass,
            },
        )
        rabbitmq_container.add_port_mappings(ecs.PortMapping(container_port=config.rabbitmq_port))
        rabbitmq_container.add_port_mappings(ecs.PortMapping(container_port=15672))

        api_service = ecs.Ec2Service(
            self,
            "ApiService",
            cluster=cluster_resources.cluster,
            task_definition=api_task_definition,
            desired_count=1,
            cloud_map_options=ecs.CloudMapOptions(
                cloud_map_namespace=discovery.namespace,
                name="api-service",
            ),
            security_groups=[network.ecs_security_group],
            vpc_subnets=ec2.SubnetSelection(subnet_group_name="PrivateWorkloads"),
        )

        worker_service = ecs.Ec2Service(
            self,
            "WorkerService",
            cluster=cluster_resources.cluster,
            task_definition=worker_task_definition,
            desired_count=1,
            cloud_map_options=ecs.CloudMapOptions(
                cloud_map_namespace=discovery.namespace,
                name="worker-service",
            ),
            security_groups=[network.ecs_security_group],
            vpc_subnets=ec2.SubnetSelection(subnet_group_name="PrivateWorkloads"),
        )

        postgres_service = ecs.Ec2Service(
            self,
            "PostgresService",
            cluster=cluster_resources.cluster,
            task_definition=postgres_task_definition,
            desired_count=1,
            cloud_map_options=ecs.CloudMapOptions(
                cloud_map_namespace=discovery.namespace,
                name="postgres",
            ),
            security_groups=[network.ecs_security_group],
            vpc_subnets=ec2.SubnetSelection(subnet_group_name="PrivateWorkloads"),
        )

        redis_service = ecs.Ec2Service(
            self,
            "RedisService",
            cluster=cluster_resources.cluster,
            task_definition=redis_task_definition,
            desired_count=1,
            cloud_map_options=ecs.CloudMapOptions(
                cloud_map_namespace=discovery.namespace,
                name="redis",
            ),
            security_groups=[network.ecs_security_group],
            vpc_subnets=ec2.SubnetSelection(subnet_group_name="PrivateWorkloads"),
        )

        rabbitmq_service = ecs.Ec2Service(
            self,
            "RabbitMqService",
            cluster=cluster_resources.cluster,
            task_definition=rabbitmq_task_definition,
            desired_count=1,
            cloud_map_options=ecs.CloudMapOptions(
                cloud_map_namespace=discovery.namespace,
                name="rabbitmq",
            ),
            security_groups=[network.ecs_security_group],
            vpc_subnets=ec2.SubnetSelection(subnet_group_name="PrivateWorkloads"),
        )

        load_balancer.http_listener.add_targets(
            "ApiTargets",
            port=config.api_port,
            health_check=elbv2.HealthCheck(path="/health"),
            targets=[
                api_service.load_balancer_target(
                    container_name="ApiContainer",
                    container_port=config.api_port,
                )
            ],
        )

        self.resources = ServiceResources(
            api_service=api_service,
            worker_service=worker_service,
            postgres_service=postgres_service,
            redis_service=redis_service,
            rabbitmq_service=rabbitmq_service,
        )

from __future__ import annotations

from aws_cdk import CfnOutput, Stack
from constructs import Construct

from cdk_constructs.cluster import ClusterConstruct
from cdk_constructs.discovery import DiscoveryConstruct
from cdk_constructs.load_balancer import LoadBalancerConstruct
from cdk_constructs.network import NetworkConstruct
from cdk_constructs.observability import ObservabilityConstruct
from cdk_constructs.services import ServicesConstruct
from cdk_constructs.storage import StorageConstruct
from config_loader import AppConfig


class TaskFlowStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, config: AppConfig, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        network_construct = NetworkConstruct(self, "Network", config=config)
        network = network_construct.resources

        storage_construct = StorageConstruct(self, "Storage", config=config)
        storage = storage_construct.resources

        observability_construct = ObservabilityConstruct(self, "Observability", config=config)
        observability = observability_construct.resources

        cluster_construct = ClusterConstruct(
            self,
            "ClusterResources",
            config=config,
            network=network,
            storage=storage,
        )
        cluster_resources = cluster_construct.resources

        discovery_construct = DiscoveryConstruct(
            self,
            "Discovery",
            config=config,
            cluster=cluster_resources.cluster,
        )
        discovery = discovery_construct.resources

        load_balancer_construct = LoadBalancerConstruct(
            self,
            "LoadBalancer",
            network=network,
        )
        load_balancer = load_balancer_construct.resources

        services_construct = ServicesConstruct(
            self,
            "Services",
            config=config,
            network=network,
            storage=storage,
            observability=observability,
            cluster_resources=cluster_resources,
            discovery=discovery,
            load_balancer=load_balancer,
        )
        services = services_construct.resources

        CfnOutput(self, "AppName", value=config.app_name)
        CfnOutput(self, "ApiImageRepository", value=config.api_image_repository)
        CfnOutput(self, "WorkerImageRepository", value=config.worker_image_repository)
        CfnOutput(self, "ArtifactsBucketName", value=storage.artifacts_bucket.bucket_name)
        CfnOutput(self, "VpcId", value=network.vpc.vpc_id)
        CfnOutput(self, "ClusterName", value=cluster_resources.cluster.cluster_name)
        CfnOutput(self, "AsgName", value=cluster_resources.auto_scaling_group.auto_scaling_group_name)
        CfnOutput(self, "AlbSecurityGroupId", value=network.alb_security_group.security_group_id)
        CfnOutput(self, "EcsSecurityGroupId", value=network.ecs_security_group.security_group_id)
        CfnOutput(self, "AlbDnsName", value=load_balancer.load_balancer.load_balancer_dns_name)
        CfnOutput(self, "CloudMapNamespace", value=discovery.namespace.namespace_name)
        CfnOutput(self, "ApiServiceLogGroupName", value=observability.api_log_group.log_group_name)
        CfnOutput(self, "ApiTaskRoleArn", value=cluster_resources.api_task_role.role_arn)
        CfnOutput(self, "WorkerTaskRoleArn", value=cluster_resources.worker_task_role.role_arn)
        CfnOutput(self, "ApiServiceName", value=services.api_service.service_name)
        CfnOutput(self, "WorkerServiceName", value=services.worker_service.service_name)
        CfnOutput(self, "PostgresServiceName", value=services.postgres_service.service_name)
        CfnOutput(self, "RedisServiceName", value=services.redis_service.service_name)
        CfnOutput(self, "RabbitMqServiceName", value=services.rabbitmq_service.service_name)

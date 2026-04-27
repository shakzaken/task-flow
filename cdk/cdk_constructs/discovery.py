from __future__ import annotations

from dataclasses import dataclass

from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_servicediscovery as servicediscovery
from constructs import Construct

from config_loader import AppConfig


@dataclass(frozen=True)
class DiscoveryResources:
    namespace: servicediscovery.PrivateDnsNamespace
    postgres_hostname: str
    redis_hostname: str
    rabbitmq_hostname: str


class DiscoveryConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, config: AppConfig, cluster: ecs.Cluster) -> None:
        super().__init__(scope, construct_id)

        namespace = cluster.add_default_cloud_map_namespace(
            name=f"{config.app_name}.local",
            type=servicediscovery.NamespaceType.DNS_PRIVATE,
        )

        self.resources = DiscoveryResources(
            namespace=namespace,
            postgres_hostname=f"postgres.{namespace.namespace_name}",
            redis_hostname=f"redis.{namespace.namespace_name}",
            rabbitmq_hostname=f"rabbitmq.{namespace.namespace_name}",
        )

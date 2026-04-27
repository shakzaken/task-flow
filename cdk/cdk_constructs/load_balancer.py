from __future__ import annotations

from dataclasses import dataclass

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from constructs import Construct

from cdk_constructs.network import NetworkResources


@dataclass(frozen=True)
class LoadBalancerResources:
    load_balancer: elbv2.ApplicationLoadBalancer
    http_listener: elbv2.ApplicationListener


class LoadBalancerConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, network: NetworkResources) -> None:
        super().__init__(scope, construct_id)

        load_balancer = elbv2.ApplicationLoadBalancer(
            self,
            "Alb",
            vpc=network.vpc,
            internet_facing=True,
            security_group=network.alb_security_group,
            vpc_subnets=ec2.SubnetSelection(subnet_group_name="PublicIngress"),
        )
        http_listener = load_balancer.add_listener(
            "HttpListener",
            port=80,
            open=False,
        )

        self.resources = LoadBalancerResources(
            load_balancer=load_balancer,
            http_listener=http_listener,
        )

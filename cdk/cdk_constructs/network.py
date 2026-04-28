from __future__ import annotations

from dataclasses import dataclass

from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from config_loader import AppConfig


@dataclass(frozen=True)
class NetworkResources:
    vpc: ec2.Vpc
    alb_security_group: ec2.SecurityGroup
    ecs_security_group: ec2.SecurityGroup


class NetworkConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, config: AppConfig) -> None:
        super().__init__(scope, construct_id)

        vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicIngress",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="PrivateWorkloads",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        alb_security_group = ec2.SecurityGroup(
            self,
            "AlbSecurityGroup",
            vpc=vpc,
            description="Public ingress security group for the task-flow ALB.",
            allow_all_outbound=True,
        )
        alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow public HTTP traffic to the ALB.",
        )

        ecs_security_group = ec2.SecurityGroup(
            self,
            "EcsSecurityGroup",
            vpc=vpc,
            description="Private security group for ECS instances and ECS services.",
            allow_all_outbound=True,
        )
        ecs_security_group.add_ingress_rule(
            alb_security_group,
            ec2.Port.tcp(config.api_port),
            "Allow the ALB to reach api-service.",
        )
        ecs_security_group.add_ingress_rule(
            ecs_security_group,
            ec2.Port.all_traffic(),
            "Allow internal service-to-service traffic.",
        )

        self.resources = NetworkResources(
            vpc=vpc,
            alb_security_group=alb_security_group,
            ecs_security_group=ecs_security_group,
        )

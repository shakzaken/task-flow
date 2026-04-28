from __future__ import annotations

from dataclasses import dataclass

from aws_cdk import aws_autoscaling as autoscaling
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from constructs import Construct

from cdk_constructs.network import NetworkResources
from cdk_constructs.storage import StorageResources
from config_loader import AppConfig


@dataclass(frozen=True)
class ClusterResources:
    cluster: ecs.Cluster
    auto_scaling_group: autoscaling.AutoScalingGroup
    capacity_provider: ecs.AsgCapacityProvider
    ecs_instance_role: iam.Role
    task_execution_role: iam.Role
    api_task_role: iam.Role
    worker_task_role: iam.Role


class ClusterConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: AppConfig,
        network: NetworkResources,
        storage: StorageResources,
    ) -> None:
        super().__init__(scope, construct_id)

        cluster = ecs.Cluster(
            self,
            "Cluster",
            vpc=network.vpc,
            cluster_name=f"{config.app_name}-cluster",
        )

        ecs_instance_role = iam.Role(
            self,
            "EcsInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2ContainerServiceforEC2Role"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchAgentServerPolicy"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"),
            ],
        )

        auto_scaling_group = autoscaling.AutoScalingGroup(
            self,
            "ClusterAsg",
            vpc=network.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_group_name="PrivateWorkloads"),
            instance_type=ec2.InstanceType("t3.small"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(),
            desired_capacity=5,
            min_capacity=5,
            max_capacity=5,
            role=ecs_instance_role,
        )
        auto_scaling_group.add_security_group(network.ecs_security_group)

        capacity_provider = ecs.AsgCapacityProvider(
            self,
            "AsgCapacityProvider",
            auto_scaling_group=auto_scaling_group,
        )
        cluster.add_asg_capacity_provider(capacity_provider)

        task_execution_role = iam.Role(
            self,
            "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
        )

        api_task_role = iam.Role(
            self,
            "ApiTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        storage.artifacts_bucket.grant_read_write(api_task_role)

        worker_task_role = iam.Role(
            self,
            "WorkerTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        storage.artifacts_bucket.grant_read_write(worker_task_role)

        self.resources = ClusterResources(
            cluster=cluster,
            auto_scaling_group=auto_scaling_group,
            capacity_provider=capacity_provider,
            ecs_instance_role=ecs_instance_role,
            task_execution_role=task_execution_role,
            api_task_role=api_task_role,
            worker_task_role=worker_task_role,
        )

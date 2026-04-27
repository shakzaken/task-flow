from __future__ import annotations

from dataclasses import dataclass

from aws_cdk import RemovalPolicy
from aws_cdk import aws_s3 as s3
from constructs import Construct

from config_loader import AppConfig


@dataclass(frozen=True)
class StorageResources:
    artifacts_bucket: s3.Bucket


class StorageConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, config: AppConfig) -> None:
        super().__init__(scope, construct_id)

        artifacts_bucket = s3.Bucket(
            self,
            "ArtifactsBucket",
            bucket_name=config.s3_bucket_name,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=False,
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.resources = StorageResources(artifacts_bucket=artifacts_bucket)

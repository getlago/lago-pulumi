import json

from pulumi import ComponentResource, ResourceOptions
from pulumi_aws import ecs, iam, config, get_caller_identity


class Cluster(ComponentResource):

    def __init__(
        self,
        name: str,
        opts: ResourceOptions = None,
    ):
        super().__init__("custom:resource:Cluster", name, {}, opts)

        # Create an AWS ECS Cluster
        self.cluster = ecs.Cluster(
            f"{name}",
            opts=ResourceOptions(parent=self),
        )

        self.role = iam.Role(
            f"{name}-task-role",
            assume_role_policy=json.dumps(
                {
                    "Version": "2008-10-17",
                    "Statement": [
                        {
                            "Sid": "",
                            "Effect": "Allow",
                            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                            "Action": "sts:AssumeRole",
                        }
                    ],
                }
            ),
            opts=ResourceOptions(parent=self),
        )

        self.rpa = iam.RolePolicyAttachment(
            f"{name}-task-policy",
            role=self.role.name,
            policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
            opts=ResourceOptions(parent=self),
        )

        self.log_policy = iam.Policy(
            f"{name}-task-log-policy",
            policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:DescribeLogStreams",
                            ],
                            # Broad resource specification; consider narrowing down
                            "Resource": [
                                f"arn:aws:logs:{config.region}:{get_caller_identity().account_id}:log-group:/ecs/*",
                                f"arn:aws:logs:{config.region}:{get_caller_identity().account_id}:log-group:/ecs/*:log-stream:*",
                            ],
                        }
                    ],
                }
            ),
            opts=ResourceOptions(parent=self),
        )
        iam.RolePolicyAttachment(
            f"{name}-task-log-policy-attachment",
            policy_arn=self.log_policy.arn,
            role=self.role.name,
            opts=ResourceOptions(parent=self),
        )

        self.register_outputs({})

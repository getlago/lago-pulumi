import json

from pulumi import ComponentResource, Output, ResourceOptions
from pulumi_aws import lb, iam, ecs, cloudwatch, config, get_caller_identity


class FrontendArgs:

    def __init__(
        self,
        lago_version=None,
        cluster_arn=None,
        role={},
        vpc_id=None,
        subnet_ids=None,
        security_group_ids=None,
        api_url=None,
        alb_arn=None,
    ):
        self.lago_version = lago_version
        self.cluster_arn = cluster_arn
        self.role = role
        self.vpc_id = vpc_id
        self.subnet_ids = subnet_ids
        self.security_group_ids = security_group_ids
        self.api_url = api_url
        self.alb_arn = alb_arn


class Frontend(ComponentResource):

    def __init__(
        self,
        name: str,
        args: FrontendArgs,
        opts: ResourceOptions = None,
    ):
        super().__init__("custom:resource:Frontend", name, {}, opts)

        # Create a Target Group
        target_group = lb.TargetGroup(
            f"{name}-tg",
            port=80,
            protocol="HTTP",
            target_type="ip",
            vpc_id=args.vpc_id,
            health_check=lb.TargetGroupHealthCheckArgs(
                healthy_threshold=2,
                interval=5,
                timeout=4,
                protocol="HTTP",
                matcher="200-399",
            ),
            opts=ResourceOptions(parent=self),
        )

        # Create a Listener
        listener = lb.Listener(
            f"{name}-listener",
            load_balancer_arn=args.alb_arn,
            port=80,
            default_actions=[
                lb.ListenerDefaultActionArgs(
                    type="forward",
                    target_group_arn=target_group.arn,
                )
            ],
            opts=ResourceOptions(parent=self),
        )

        # Create the Frontend ECS Task Definition
        task_name = f"{name}-task"
        container_name = f"{name}-container"
        self.task_definition = ecs.TaskDefinition(
            task_name,
            family=task_name,
            cpu="256",
            memory="512",
            network_mode="awsvpc",
            requires_compatibilities=["FARGATE"],
            execution_role_arn=args.role.arn,
            task_role_arn=args.role.arn,
            container_definitions=Output.json_dumps(
                [
                    {
                        "name": container_name,
                        "image": f"getlago/front:v{args.lago_version}",
                        "portMappings": [
                            {
                                "containerPort": 80,
                                "hostPort": 80,
                                "protocol": "tcp",
                            }
                        ],
                        "logConfiguration": {
                            "logDriver": "awslogs",
                            "options": {
                                "awslogs-create-group": "true",
                                "awslogs-group": f"/ecs/{name}-task",
                                "awslogs-region": "eu-west-2",
                                "awslogs-stream-prefix": "ecs",
                            },
                        },
                        "environment": [
                            {
                                "name": "APP_ENV",
                                "value": "production",
                            },
                            {
                                "name": "API_URL",
                                "value": Output.concat("http://", args.api_url),
                            },
                            {
                                "name": "CODEGEN_API",
                                "value": Output.concat("http://", args.api_url),
                            },
                        ],
                    }
                ]
            ),
            opts=ResourceOptions(parent=self),
        )

        # Create the ECS Frontend Service
        self.service = ecs.Service(
            f"{name}-svc",
            cluster=args.cluster_arn,
            desired_count=1,
            launch_type="FARGATE",
            task_definition=self.task_definition.arn,
            network_configuration=ecs.ServiceNetworkConfigurationArgs(
                assign_public_ip=True,
                subnets=args.subnet_ids,
                security_groups=args.security_group_ids,
            ),
            load_balancers=[
                ecs.ServiceLoadBalancerArgs(
                    target_group_arn=target_group.arn,
                    container_name=container_name,
                    container_port=80,
                )
            ],
            opts=ResourceOptions(depends_on=[listener], parent=self),
        )

        self.register_outputs({})

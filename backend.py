import base64
import json
import pulumi_random as random
import pulumi_tls as tls

from pulumi import ComponentResource, Output, ResourceOptions
from pulumi_aws import lb, ecs, cloudwatch, iam, config, get_caller_identity


class BackendArgs:

    def __init__(
        self,
        lago_version=None,
        cluster_arn=None,
        role={},
        vpc_id=None,
        subnet_ids=None,
        app_security_group=None,
        container_security_group=None,
        db_host=None,
        db_port="5432",
        db_name=None,
        db_user=None,
        db_password=None,
        redis_host=None,
        redis_port="6379",
        bucket_name=None,
        front_url=None,
        alb_arn=None,
        api_url=None,
    ):
        self.lago_version = lago_version
        self.cluster_arn = cluster_arn
        self.role = role
        self.vpc_id = vpc_id
        self.subnet_ids = subnet_ids
        self.app_security_group_id = app_security_group
        self.container_security_group = container_security_group
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.bucket_name = bucket_name
        self.front_url = front_url
        self.alb_arn = alb_arn
        self.api_url = api_url


class Backend(ComponentResource):

    def __init__(
        self,
        name: str,
        args: BackendArgs,
        opts: ResourceOptions = None,
    ):
        super().__init__("custom:resource:Backend", name, {}, opts)

        # Create a Load Balancer to listen to HTTP traffic on port 80
        self.alb = lb.LoadBalancer(
            f"{name}-alb",
            security_groups=[args.app_security_group_id],
            subnets=args.subnet_ids,
            opts=ResourceOptions(parent=self),
        )

        # Create a Target Group for API
        api_target_group = lb.TargetGroup(
            f"{name}-api-tg",
            port=3000,
            protocol="HTTP",
            target_type="ip",
            vpc_id=args.vpc_id,
            health_check=lb.TargetGroupHealthCheckArgs(
                path="/health",
                port=3000,
                healthy_threshold=2,
                interval=5,
                timeout=4,
                protocol="HTTP",
                matcher="200-399",
            ),
            opts=ResourceOptions(parent=self),
        )

        # Create a listener for API
        api_listener = lb.Listener(
            f"{name}-api-listener",
            load_balancer_arn=args.alb_arn,
            port=80,
            default_actions=[
                lb.ListenerDefaultActionArgs(
                    type="forward",
                    target_group_arn=api_target_group.arn,
                )
            ],
            opts=ResourceOptions(parent=self),
        )

        database_url = Output.concat(
            "postgres://",
            args.db_user,
            ":",
            args.db_password,
            "@",
            args.db_host,
            ":",
            args.db_port,
            "/",
            args.db_name,
        )

        redis_url = Output.concat(
            "redis://",
            args.redis_host,
            ":",
            args.redis_port,
        )

        rsa_private_key = tls.PrivateKey(
            f"{name}-private-key",
            algorithm="RSA",
        ).private_key_pem.apply(lambda key: base64.b64encode(key.encode()).decode())
        secret_key_base = random.RandomString(
            f"{name}-secret-key-base",
            length=64,
            special=False,
        ).result.apply(lambda key: base64.b64encode(key.encode()).decode())
        encryption_deterministic_key = random.RandomString(
            f"{name}-encryption-deterministic-key",
            length=32,
            special=False,
        ).result.apply(lambda key: base64.b64encode(key.encode()).decode())
        encryption_key_derivation_salt = random.RandomString(
            f"{name}-encryption-key-derivation-salt",
            length=32,
            special=False,
        ).result.apply(lambda key: base64.b64encode(key.encode()).decode())
        encryption_primary_key = random.RandomString(
            f"{name}-encryption-primary-key",
            length=32,
            special=False,
        ).result.apply(lambda key: base64.b64encode(key.encode()).decode())

        environment = [
            {
                "name": "RAILS_ENV",
                "value": "production",
            },
            {
                "name": "DATABASE_URL",
                "value": database_url,
            },
            {
                "name": "REDIS_URL",
                "value": redis_url,
            },
            {
                "name": "REDIS_CACHE_URL",
                "value": redis_url,
            },
            {
                "name": "LAGO_SIDEKIQ_WEB",
                "value": "true",
            },
            {
                "name": "RAILS_LOG_TO_STDOUT",
                "value": "true",
            },
            {
                "name": "LAGO_RSA_PRIVATE_KEY",
                "value": rsa_private_key,
            },
            {
                "name": "SECRET_KEY_BASE",
                "value": secret_key_base,
            },
            {
                "name": "ENCRYPTION_DETERMINISTIC_KEY",
                "value": encryption_deterministic_key,
            },
            {
                "name": "ENCRYPTION_KEY_DERIVATION_SALT",
                "value": encryption_key_derivation_salt,
            },
            {
                "name": "ENCRYPTION_PRIMARY_KEY",
                "value": encryption_primary_key,
            },
            {
                "name": "LAGO_DISABLE_SEGMENT",
                "value": "true",
            },
            {
                "name": "LAGO_DISABLE_SIGNUP",
                "value": "false",
            },
            {
                "name": "DATABASE_POOL",
                "value": "10",
            },
            {
                "name": "RAILS_MAX_THREADS",
                "value": "5",
            },
            {
                "name": "RAILS_MIN_THREADS",
                "value": "0",
            },
            {
                "name": "SIDEKIQ_EVENTS",
                "value": "true",
            },
            {
                "name": "WEB_CONCURRENCY",
                "value": "2",
            },
            {
                "name": "LAGO_USE_AWS_S3",
                "value": "true",
            },
            {
                "name": "AWS_REGION",
                "value": "eu-west-2",
            },
            {
                "name": "LAGO_AWS_S3_REGION",
                "value": "eu-west-2",
            },
            {
                "name": "LAGO_AWS_S3_BUCKET",
                "value": args.bucket_name,
            },
            {
                "name": "LAGO_FRONT_URL",
                "value": Output.concat("http://", args.front_url),
            },
            {
                "name": "LAGO_API_URL",
                "value": Output.concat("http://", args.api_url),
            },
        ]

        # Create the API ECS Task Definition
        api_task_name = f"{name}-api-task"
        api_container_name = f"{name}-api-container"
        self.api_task_definition = ecs.TaskDefinition(
            api_task_name,
            family=api_task_name,
            cpu="1024",
            memory="2048",
            network_mode="awsvpc",
            requires_compatibilities=["FARGATE"],
            execution_role_arn=args.role.arn,
            task_role_arn=args.role.arn,
            container_definitions=Output.json_dumps(
                [
                    {
                        "name": api_container_name,
                        "image": f"getlago/api:v{args.lago_version}",
                        "portMappings": [
                            {
                                "containerPort": 3000,
                                "hostPort": 3000,
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
                        "environment": environment,
                    }
                ]
            ),
            opts=ResourceOptions(parent=self),
        )

        # Create the API ECS Service
        self.api_service = ecs.Service(
            f"{name}-api-svc",
            cluster=args.cluster_arn,
            desired_count=1,
            launch_type="FARGATE",
            task_definition=self.api_task_definition.arn,
            network_configuration=ecs.ServiceNetworkConfigurationArgs(
                assign_public_ip=True,
                subnets=args.subnet_ids,
                security_groups=[args.container_security_group],
            ),
            load_balancers=[
                ecs.ServiceLoadBalancerArgs(
                    target_group_arn=api_target_group.arn,
                    container_name=api_container_name,
                    container_port=3000,
                )
            ],
            opts=ResourceOptions(depends_on=[api_listener], parent=self),
        )

        self.register_outputs({})

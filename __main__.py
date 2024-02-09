"""
Deploys:
- Network: VPC, Subnets, Security Groups
- DB Backend: PostgreSQL RDS, Redis
"""

import pulumi
import pulumi_random as random
import network
import database
import cluster
import frontend
import backend
import bucket

config = pulumi.Config()
service_name = config.get("service_name") or "lago"
lago_version = config.get("lago_version")
db_name = config.get("db_name") or "lago"
db_user = config.get("db_user") or "lago"

db_password = config.get_secret("db_password")
if not db_password:
    password = random.RandomPassword(
        "db_password",
        length=16,
    )
    db_password = password.result

# Create an AWS VPC with Subnets and Security Groups
network = network.Vpc(f"{service_name}-net", network.VpcArgs())
subnet_ids = []
for subnet in network.subnets:
    subnet_ids.append(subnet.id)

# Create an RDS PostgreSQL instance
db = database.Db(
    f"{service_name}-db",
    database.DbArgs(
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        subnet_ids=subnet_ids,
        security_group_ids=[network.rds_security_group.id],
    ),
)

# Create a Elasticache Redis instance
redis = database.Redis(
    f"{service_name}-redis",
    database.RedisArgs(
        redis_name=db_name,
        subnet_ids=subnet_ids,
        security_group_ids=[network.redis_security_group.id],
    ),
)

# Create ECS Cluster
cluster = cluster.Cluster(f"{service_name}-ecs")

bucket = bucket.Bucket(
    f"keel-{service_name}-storage", bucket.BucketArgs(role_name=cluster.role.name)
)

# Create Backend
backend = backend.Backend(
    f"{service_name}-be",
    backend.BackendArgs(
        cluster_arn=cluster.cluster.arn,
        role=cluster.role,
        lago_version=lago_version,
        vpc_id=network.vpc.id,
        subnet_ids=subnet_ids,
        app_security_group=network.app_security_group,
        container_security_group=network.be_security_group,
        db_host=db.db.address,
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        redis_host=redis.redis.cache_nodes[0].address,
        bucket_name=bucket.bucket.bucket,
        front_url=network.front_lb.dns_name,
        api_url=network.back_lb.dns_name,
        alb_arn=network.back_lb.arn,
    ),
)

# Create Frontend
front = frontend.Frontend(
    f"{service_name}-front",
    frontend.FrontendArgs(
        cluster_arn=cluster.cluster.arn,
        role=cluster.role,
        lago_version=lago_version,
        vpc_id=network.vpc.id,
        subnet_ids=subnet_ids,
        security_group_ids=[network.app_security_group.id],
        api_url=network.back_lb.dns_name,
        alb_arn=network.front_lb.arn,
    ),
)

front_url = pulumi.Output.concat("http://", network.front_lb.dns_name)
api_url = pulumi.Output.concat("http://", network.back_lb.dns_name)

pulumi.export("Lago Front URL", front_url)
pulumi.export("Lago API URL", api_url)
pulumi.export("ECS Cluster Name", cluster.cluster.name)
pulumi.export("Lago Version", lago_version)
pulumi.export("Service Name", service_name)

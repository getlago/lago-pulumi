"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

# Create a new Lago VPC
vpc = aws.ec2.Vpc("lago_vpc", cidr_block="172.42.0.0/16")

vpc_sg = aws.ec2.SecurityGroup(
  "lago_security_group",
  description="Lago Security Group",
  vpc_id=vpc.id,
  ingress=[
    aws.ec2.SecurityGroupIngressArgs(
      description="allow HTTP",
      from_port=80,
      to_port=80,
      protocol="tcp",
      cidr_blocks=["0.0.0.0/0"],
    ),
    aws.ec2.SecurityGroupIngressArgs(
      description= "allow HTTPS",
      from_port=443,
      to_port=443,
      protocol="tcp",
      cidr_blocks=["0.0.0.0/0"],
    ),
    aws.ec2.SecurityGroupIngressArgs(
      description="allow POSTGRESQL",
      from_port=5432,
      to_port=5432,
      protocol="tcp",
      cidr_blocks=["172.42.0.0/16"],
    ),
    aws.ec2.SecurityGroupIngressArgs(
      description="allow REDIS",
      from_port=6379,
      to_port=6379,
      protocol="tcp",
      cidr_blocks=["172.42.0.0/16"],
    ),
  ],
  egress=[
    aws.ec2.SecurityGroupEgressArgs(
      from_port=0,
      to_port=0,
      protocol="-1",
      cidr_blocks=["0.0.0.0/0"],
    ),
  ],
  tags={
    "Name": "lago_security_group",
  },
)

# Create a PostgreSQL RDS Instance
# db_subnet = aws.rds.SubnetGroup(
#   "lago_rds_subnet",
#   subnet_ids=vpc.private_subnet_ids,
# )

# db = aws.rds.Instance(
#   "lago-database",
#   allocated_storage=10,
#   db_name="lago",
#   db_subnet_group_name=db_subnet.name,
#   engine="postgresql",
#   engine_version="14.7",
#   instance_class="db.t4g.micro",
#   parameter_group_name="default.postgres14",
#   storage_type="gp2",
#   username="lago",
#   password=config.require_secret('dbPassword'),
#   skip_final_snapshot=True,
#   vpc_security_group_ids=[vpc_sg.id],
# )

# pulumi.export(db.address)
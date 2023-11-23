import json

from pulumi import ComponentResource, ResourceOptions
from pulumi_aws import ecs, iam

class Cluster(ComponentResource):

  def __init__(self,
               name: str,
               opts: ResourceOptions = None,
              ):
    super().__init__('custom:resource:Cluster', name, {}, opts)

    # Create an AWS ECS Cluster
    self.cluster = ecs.Cluster(f'{name}',
      opts=ResourceOptions(parent=self),
    )

    self.role = iam.Role(f'{name}-task-role',
      assume_role_policy=json.dumps({
        'Version': '2008-10-17',
        'Statement': [{
          'Sid': '',
          'Effect': 'Allow',
          'Principal': {
            'Service': 'ecs-tasks.amazonaws.com'
          },
          'Action': 'sts:AssumeRole'
        }]
      }),
      opts=ResourceOptions(parent=self),
    )

    self.rpa = iam.RolePolicyAttachment(f'{name}-task-policy',
      role=self.role.name,
      policy_arn='arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy',
      opts=ResourceOptions(parent=self),
    )

    self.register_outputs({})
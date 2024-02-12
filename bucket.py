import json

from pulumi import ComponentResource, ResourceOptions
from pulumi_aws import ecs, iam, s3


class BucketArgs:

    def __init__(
        self,
        role_name=None,
    ):
        self.role_name = role_name


class Bucket(ComponentResource):

    def __init__(
        self,
        name: str,
        args: BucketArgs,
        opts: ResourceOptions = None,
    ):
        super().__init__("custom:resource:Bucket", name, {}, opts)

        # Create an S3 bucket
        self.bucket = s3.Bucket(name, acl="private", opts=ResourceOptions(parent=self))

        # Grant the ECS task role permission to access the S3 bucket
        self.bucket_policy = iam.Policy(
            f"{name}-access-policy",
            policy=self.bucket.arn.apply(
                lambda arn: json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": "s3:*",
                                "Resource": [
                                    f"{arn}/*",  # Grant access to objects in the bucket
                                    arn,  # Grant access to the bucket itself
                                ],
                            }
                        ],
                    }
                )
            ),
            opts=ResourceOptions(parent=self),
        )

        self.rpa = iam.RolePolicyAttachment(
            f"{name}-s3-role-policy-attachment",
            policy_arn=self.bucket_policy.arn,
            role=args.role_name,
            opts=ResourceOptions(parent=self),
        )

        self.register_outputs({})

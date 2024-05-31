import json
import pulumi
import pulumi_aws as aws

# Create an S3 bucket
bucket = aws.s3.Bucket('my-bucket')

ownership_controls = aws.s3.BucketOwnershipControls(
    'ownership-controls',
    bucket=bucket.id,
    rule=aws.s3.BucketOwnershipControlsRuleArgs(
        object_ownership='BucketOwnerPreferred',
    ),
)

public_access_block = aws.s3.BucketPublicAccessBlock('public-access-block', bucket=bucket.id, block_public_acls=False)

# Upload a file to the S3 bucket
db_file = aws.s3.BucketObject('dbFile',
    bucket=bucket.id,
    key='database.json',
    content=json.dumps({}),
    acl='bucket-owner-full-control',
    opts=pulumi.ResourceOptions(depends_on=[public_access_block, ownership_controls]),
    content_type='application/json')

role = aws.iam.Role("role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com",
            },
        }],
    }),
    managed_policy_arns=[aws.iam.ManagedPolicy.AWS_LAMBDA_BASIC_EXECUTION_ROLE, aws.iam.ManagedPolicy.AMAZON_S3_FULL_ACCESS])


# Attach a policy to the role that allows access to the S3 bucket
s3_policy = aws.iam.RolePolicy('s3Policy',
    role=role.id,
    policy=pulumi.Output.all(bucket.arn).apply(lambda arn: json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": f"{arn}/*"
        },
            {
                "Effect": "Allow",
                "Action": "s3:ListBucket",
                "Resource": arn
            }]
    }))
)

# A Lambda function to handle parking entry
entry_fn = aws.lambda_.Function("entry_fn",
    runtime="python3.9",
    handler="index.lambda_handler",
    role=role.arn,
    code=pulumi.AssetArchive({
        'index.py': pulumi.FileAsset('./entry/index.py'),
        'database.py': pulumi.FileAsset('./database.py')
    }))

# A Lambda function to handle parking exit
exit_fn = aws.lambda_.Function("exit_fn",
    runtime="python3.9",
    handler="index.lambda_handler",
    role=role.arn,
    code=pulumi.AssetArchive({
        'index.py': pulumi.FileAsset('./exit/index.py'),
        'database.py': pulumi.FileAsset('./database.py')
    }))

api = aws.apigatewayv2.Api("api",protocol_type="HTTP")

entry_integration = aws.apigatewayv2.Integration("entry_integration",
    api_id=api.id,
    integration_type="AWS_PROXY",
    integration_uri=entry_fn.arn)

exit_integration = aws.apigatewayv2.Integration("exit_integration",
    api_id=api.id,
    integration_type="AWS_PROXY",
    integration_uri=exit_fn.arn)

# Add a Lambda permission for the API Gateway to invoke the function
entry_permission = aws.lambda_.Permission("entry_permission",
    action="lambda:InvokeFunction",
    function=entry_fn.name,
    principal="apigateway.amazonaws.com",
    source_arn=pulumi.Output.concat(api.execution_arn, "/*/*"))

exit_permission = aws.lambda_.Permission("exit_permission",
    action="lambda:InvokeFunction",
    function=exit_fn.name,
    principal="apigateway.amazonaws.com",
    source_arn=pulumi.Output.concat(api.execution_arn, "/*/*"))

entry_route = aws.apigatewayv2.Route("entryRoute",
    api_id=api.id,
    route_key="POST /entry",
    target=entry_integration.id.apply(lambda id: "integrations/" + id))

exit_route = aws.apigatewayv2.Route("exitRoute",
    api_id=api.id,
    route_key="POST /exit",
    target=exit_integration.id.apply(lambda id: "integrations/" + id))

deployment = aws.apigatewayv2.Deployment("api_deployment",
    api_id=api.id,
    opts=pulumi.ResourceOptions(depends_on=[entry_route, exit_route]))

stage = aws.apigatewayv2.Stage("api_stage",
    api_id=api.id,
    name="parking",
    deployment_id=deployment.id)

pulumi.export("url", pulumi.Output.concat(api.api_endpoint, "/", stage.name))

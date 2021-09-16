import os
import time
import uuid
import yaml
import boto3


def before_all(context):
    context.TEST_ARTIFACT_BUCKET_NAME = 'sceptre-test-artifacts'
    context.region = boto3.session.Session().region_name
    context.uuid = uuid.uuid1().hex
    context.project_code = "sceptre-integration-tests-{0}".format(
        context.uuid
    )

    sts = boto3.client("sts")
    account_number = sts.get_caller_identity()['Account']
    context.bucket_name = "sceptre-integration-tests-templates-{}".format(
        account_number
    )

    context.sceptre_dir = os.path.join(
        os.getcwd(), "integration-tests", "sceptre-project"
    )
    update_config(context)
    context.cloudformation = boto3.resource('cloudformation')
    context.client = boto3.client("cloudformation")

    config_path = os.path.join(
        context.sceptre_dir, "config", "9/B" + ".yaml"
    )

    with open(config_path, "r") as file:
        file_data = file.read()

    file_data = file_data.replace("{project_code}", context.project_code)

    with open(config_path, "w") as file:
        file.write(file_data)


def before_scenario(context, scenario):
    os.environ.pop("AWS_REGION", None)
    os.environ.pop("AWS_CONFIG_FILE", None)
    context.error = None
    context.response = None
    context.output = None


def update_config(context):
    config_path = os.path.join(
        context.sceptre_dir, "config", "config.yaml"
    )
    with open(config_path) as config_file:
        stack_group_config = yaml.safe_load(config_file)

    stack_group_config["template_bucket_name"] = context.bucket_name
    stack_group_config["project_code"] = context.project_code

    with open(config_path, 'w') as config_file:
        yaml.safe_dump(
            stack_group_config, config_file, default_flow_style=False
        )


def after_all(context):
    response = context.client.describe_stacks()
    for stack in response["Stacks"]:
        if stack["StackName"].startswith(context.project_code):
            context.client.delete_stack(
                StackName=stack["StackName"]
            )
            time.sleep(2)
    context.project_code = "sceptre-integration-tests"
    context.bucket_name = "sceptre-integration-tests-templates"
    update_config(context)


def before_feature(context, feature):
    """
    Create a test bucket with a deterministic name so that the S3 template handler
    has a bucket to reference.  The better option would be create a bucket with a
    unique name on every test run however we cannot dynamically reference bucket
    names in the sceptre config file.
    """
    if 's3-template-handler' in feature.tags:
        bucket = boto3.resource('s3').Bucket(context.TEST_ARTIFACT_BUCKET_NAME)
        if bucket.creation_date is None:
            bucket.create(
                Bucket=context.TEST_ARTIFACT_BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': context.region}
            )

def after_feature(context, feature):
    """
    Attempt to do a full cleanup of test artifacts however deleting the bucket
    causes error on the next bucket creation because it can take some time before
    the same bucket name is available.  We need to leave the bucket around.
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/delete-bucket.html
    """
    if 's3-template-handler' in feature.tags:
        bucket = boto3.resource('s3').Bucket(context.TEST_ARTIFACT_BUCKET_NAME)
        if bucket.creation_date is not None:
            bucket.objects.all().delete()
            # bucket.delete()

import json
import os
import boto3
from datetime import datetime, timedelta

ce = boto3.client('ce', region_name='us-east-1')  # Cost Explorer API only available in us-east-1
tagging = boto3.client('resourcegroupstaggingapi')

TAG_KEY = os.environ.get('PROJECT_TAG_KEY', 'Project')
TAG_VALUE = os.environ.get('PROJECT_TAG_VALUE', 'Hey')

# Implicit services: when a tagged service is found, also include these
# related CE services that don't have their own tagged resources
IMPLICIT_SERVICES = {
    'AWS Lambda': ['AmazonCloudWatch'],  # Lambda auto-creates CloudWatch Log Groups
    'Amazon API Gateway': ['AmazonCloudWatch'],  # API GW can log to CloudWatch
    'Amazon Elastic Compute Cloud - Compute': ['EC2 - Other'],  # Data transfer, EBS, etc.
}

# Comprehensive AWS mapping: ARN service prefix -> Cost Explorer display name
ARN_TO_CE = {
    # Compute
    'ec2': 'Amazon Elastic Compute Cloud - Compute',
    'lambda': 'AWS Lambda',
    'ecs': 'Amazon Elastic Container Service',
    'eks': 'Amazon Elastic Kubernetes Service',
    'lightsail': 'Amazon Lightsail',
    'batch': 'AWS Batch',
    'elasticbeanstalk': 'AWS Elastic Beanstalk',
    'apprunner': 'AWS App Runner',
    # Storage
    's3': 'Amazon Simple Storage Service',
    'ebs': 'EC2 - Other',
    'efs': 'Amazon Elastic File System',
    'glacier': 'Amazon S3 Glacier',
    'fsx': 'Amazon FSx',
    'backup': 'AWS Backup',
    # Database
    'dynamodb': 'Amazon DynamoDB',
    'rds': 'Amazon Relational Database Service',
    'elasticache': 'Amazon ElastiCache',
    'neptune': 'Amazon Neptune',
    'redshift': 'Amazon Redshift',
    'dax': 'Amazon DynamoDB Accelerator (DAX)',
    'docdb': 'Amazon DocumentDB (with MongoDB compatibility)',
    'keyspaces': 'Amazon Keyspaces (for Apache Cassandra)',
    'memorydb': 'Amazon MemoryDB',
    'timestream': 'Amazon Timestream',
    # Networking
    'apigateway': 'Amazon API Gateway',
    'execute-api': 'Amazon API Gateway',
    'cloudfront': 'Amazon CloudFront',
    'route53': 'Amazon Route 53',
    'vpc': 'Amazon Virtual Private Cloud',
    'elasticloadbalancing': 'Elastic Load Balancing',
    'directconnect': 'AWS Direct Connect',
    'globalaccelerator': 'AWS Global Accelerator',
    'appmesh': 'AWS App Mesh',
    'location': 'Amazon Location Service',
    # AI/ML
    'textract': 'Amazon Textract',
    'comprehend': 'Amazon Comprehend',
    'rekognition': 'Amazon Rekognition',
    'sagemaker': 'Amazon SageMaker',
    'bedrock': 'Amazon Bedrock',
    'transcribe': 'Amazon Transcribe',
    'translate': 'Amazon Translate',
    'polly': 'Amazon Polly',
    'lex': 'Amazon Lex',
    'personalize': 'Amazon Personalize',
    'forecast': 'Amazon Forecast',
    'kendra': 'Amazon Kendra',
    'q': 'Amazon Q',
    # Monitoring & Management
    'logs': 'AmazonCloudWatch',
    'cloudwatch': 'AmazonCloudWatch',
    'monitoring': 'AmazonCloudWatch',
    'cloudtrail': 'AWS CloudTrail',
    'config': 'AWS Config',
    'cloudformation': 'AWS CloudFormation',
    'servicecatalog': 'AWS Service Catalog',
    'ssm': 'AWS Systems Manager',
    'xray': 'AWS X-Ray',
    # Security & Identity
    'kms': 'AWS Key Management Service',
    'secretsmanager': 'AWS Secrets Manager',
    'acm': 'AWS Certificate Manager',
    'iam': 'AWS Identity and Access Management',
    'cognito-idp': 'Amazon Cognito',
    'cognito-identity': 'Amazon Cognito',
    'waf': 'AWS WAF',
    'wafv2': 'AWS WAF',
    'guardduty': 'Amazon GuardDuty',
    'inspector': 'Amazon Inspector',
    'macie': 'Amazon Macie',
    # Messaging & Integration
    'sqs': 'Amazon Simple Queue Service',
    'sns': 'Amazon Simple Notification Service',
    'ses': 'Amazon Simple Email Service',
    'events': 'Amazon EventBridge',
    'states': 'AWS Step Functions',
    'kinesis': 'Amazon Kinesis',
    'firehose': 'Amazon Kinesis Firehose',
    'mq': 'Amazon MQ',
    'swf': 'Amazon Simple Workflow Service',
    'pipes': 'Amazon EventBridge Pipes',
    # Developer Tools
    'codecommit': 'AWS CodeCommit',
    'codebuild': 'AWS CodeBuild',
    'codepipeline': 'AWS CodePipeline',
    'codedeploy': 'AWS CodeDeploy',
    'codeartifact': 'AWS CodeArtifact',
    'cloudshell': 'AWS CloudShell',
    # Analytics
    'glue': 'AWS Glue',
    'athena': 'Amazon Athena',
    'quicksight': 'Amazon QuickSight',
    'opensearch': 'Amazon OpenSearch Service',
    'es': 'Amazon OpenSearch Service',
    'emr': 'Amazon EMR',
    'lakeformation': 'AWS Lake Formation',
    # IoT
    'iot': 'AWS IoT',
    'iotsitewise': 'AWS IoT SiteWise',
    'iotevents': 'AWS IoT Events',
    'iotanalytics': 'AWS IoT Analytics',
    'greengrass': 'AWS IoT Greengrass',
    # Containers
    'ecr': 'Amazon EC2 Container Registry (ECR)',
    'fargate': 'AWS Fargate',
    # Migration
    'dms': 'AWS Database Migration Service',
    'migration-hub': 'AWS Migration Hub Refactor Spaces',
    'refactor-spaces': 'AWS Migration Hub Refactor Spaces',
    # Other
    'transfer': 'AWS Transfer Family',
    'mediaconvert': 'AWS Elemental MediaConvert',
    'elasticmapreduce': 'Amazon EMR',
}


def discover_project_services():
    """Dynamically discover which AWS services this project uses by finding tagged resources."""
    ce_services = set()
    paginator = tagging.get_paginator('get_resources')
    for page in paginator.paginate(
        TagFilters=[{'Key': TAG_KEY, 'Values': [TAG_VALUE]}]
    ):
        for resource in page.get('ResourceTagMappingList', []):
            arn = resource['ResourceARN']
            parts = arn.split(':')
            if len(parts) >= 3:
                svc_prefix = parts[2]
                ce_name = ARN_TO_CE.get(svc_prefix)
                if ce_name:
                    ce_services.add(ce_name)
    # Add implicit/related services (e.g. CloudWatch for Lambda)
    implicit = set()
    for svc in ce_services:
        for related in IMPLICIT_SERVICES.get(svc, []):
            implicit.add(related)
    ce_services.update(implicit)
    return ce_services


def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': '*'
    }

    try:
        # 1. Discover which services are used by this project via tags
        project_services = discover_project_services()
        print(f"Discovered project services: {project_services}")

        # 2. Query Cost Explorer for the project region
        now = datetime.utcnow()
        params = event.get('queryStringParameters') or {}
        period = params.get('period', 'month')

        if period == 'year':
            start_date = now.strftime('%Y-01-01')
            label = now.strftime('%Y')
        else:
            start_date = now.strftime('%Y-%m-01')
            label = now.strftime('%B %Y')

        end_date = (now + timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"Querying costs from {start_date} to {end_date}")

        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='DAILY',  # Changed to DAILY for accurate partial month sums
            Metrics=['UnblendedCost'],
            Filter={
                'Dimensions': {
                    'Key': 'RECORD_TYPE',
                    'Values': ['Usage']
                }
            },
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        print(f"Cost Explorer response: {json.dumps(response, default=str)}")

        # 3. Only include services discovered via tagging, aggregate across time periods
        service_totals = {}
        total = 0.0

        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                service_name = group['Keys'][0]
                # TEMP: Comment out to show all costs
                # if service_name not in project_services:
                #     continue
                amount = float(group['Metrics']['UnblendedCost']['Amount'])
                service_totals[service_name] = service_totals.get(service_name, 0.0) + amount
                total += amount

        services = [
            {'service': name, 'amount': round(amt, 2)}
            for name, amt in service_totals.items()
        ]
        services.sort(key=lambda x: (-x['amount'], x['service']))
        print(f"Calculated total: {total}, services: {services}")

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'period': period,
                'label': label,
                'total': round(total, 4),
                'currency': 'USD',
                'services': services
            })
        }

    except Exception as e:
        print(f"Cost Explorer error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

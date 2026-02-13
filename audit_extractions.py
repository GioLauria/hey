import boto3
import json
import os
from datetime import datetime

def audit_extractions():
    """Audit S3 files and DynamoDB extractions to ensure completeness"""

    # AWS clients
    s3_client = boto3.client('s3', region_name='eu-west-2')
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
    table = dynamodb.Table('ocr-extractions')

    bucket = 'ocr-site-bc930bd1'

    print("🔍 Starting extraction audit...")
    print("=" * 60)

    # 1. Get all S3 files in the r/ directory
    print("📁 Scanning S3 files...")
    s3_files = []
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix='r/'):
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    if key.endswith(('.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif')):
                        s3_files.append({
                            'key': key,
                            'size': obj['Size'],
                            'last_modified': obj['LastModified']
                        })
    except Exception as e:
        print(f"❌ Error scanning S3: {e}")
        return

    print(f"Found {len(s3_files)} processable files in S3")

    # 2. Get all DynamoDB extractions
    print("🗄️  Scanning DynamoDB extractions...")
    db_extractions = []
    try:
        response = table.scan()
        db_extractions = response.get('Items', [])
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            db_extractions.extend(response.get('Items', []))
    except Exception as e:
        print(f"❌ Error scanning DynamoDB: {e}")
        return

    print(f"Found {len(db_extractions)} extraction records in DynamoDB")

    # 3. Cross-reference S3 files with DB records
    print("\n🔗 Cross-referencing S3 files with DB records...")

    s3_keys_in_db = {item.get('s3_key') for item in db_extractions if item.get('s3_key')}
    db_records_by_key = {item.get('s3_key'): item for item in db_extractions if item.get('s3_key')}

    missing_extractions = []
    existing_extractions = []

    for s3_file in s3_files:
        key = s3_file['key']
        if key in s3_keys_in_db:
            existing_extractions.append((key, db_records_by_key[key]))
        else:
            missing_extractions.append(s3_file)

    print(f"✅ {len(existing_extractions)} files have extraction records")
    print(f"❌ {len(missing_extractions)} files are missing extraction records")

    # 4. Check for data quality issues
    print("\n📊 Checking data quality...")

    quality_issues = []
    for key, record in existing_extractions:
        issues = []

        # Check required fields
        if not record.get('text'):
            issues.append("missing text")
        if not record.get('filename'):
            issues.append("missing filename")
        if not record.get('timestamp'):
            issues.append("missing timestamp")

        # Check file exists in S3
        try:
            s3_client.head_object(Bucket=bucket, Key=key)
            file_exists = True
        except:
            file_exists = False
            issues.append("S3 file not found")

        # Check thumbnail exists if it's a PDF
        if key.lower().endswith('.pdf') and record.get('thumbnail_key'):
            try:
                s3_client.head_object(Bucket=bucket, Key=record['thumbnail_key'])
                thumbnail_exists = True
            except:
                thumbnail_exists = False
                issues.append("thumbnail not found in S3")

        if issues:
            quality_issues.append((key, issues, file_exists))

    print(f"⚠️  {len(quality_issues)} records have quality issues")

    # 5. Generate report
    print("\n📋 AUDIT REPORT")
    print("=" * 60)

    if missing_extractions:
        print(f"\n❌ MISSING EXTRACTIONS ({len(missing_extractions)} files):")
        for file in missing_extractions:
            print(f"  - {file['key']} ({file['size']} bytes, modified {file['last_modified']})")

    if quality_issues:
        print(f"\n⚠️  DATA QUALITY ISSUES ({len(quality_issues)} records):")
        for key, issues, file_exists in quality_issues:
            status = "✅" if file_exists else "❌"
            print(f"  {status} {key}: {', '.join(issues)}")

    # 6. Summary
    total_files = len(s3_files)
    processed_files = len(existing_extractions)
    healthy_records = len(existing_extractions) - len(quality_issues)

    print("
📈 SUMMARY:"    print(f"  Total S3 files: {total_files}")
    print(f"  Processed files: {processed_files} ({processed_files/total_files*100:.1f}%)")
    print(f"  Healthy records: {healthy_records} ({healthy_records/total_files*100:.1f}%)")
    print(f"  Missing extractions: {len(missing_extractions)}")
    print(f"  Records with issues: {len(quality_issues)}")

    return {
        's3_files': s3_files,
        'db_extractions': db_extractions,
        'missing_extractions': missing_extractions,
        'quality_issues': quality_issues,
        'existing_extractions': existing_extractions
    }

if __name__ == "__main__":
    audit_extractions()</content>
<parameter name="filePath">audit_extractions.py
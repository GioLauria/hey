import boto3

def check_extractions():
    # Check DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
    table = dynamodb.Table('ocr-extractions')

    response = table.scan()
    items = response.get('Items', [])
    print(f'Found {len(items)} extraction records in DynamoDB')

    for item in items:
        filename = item.get('filename', 'unknown')
        s3_key = item.get('s3_key', 'no key')
        print(f'  - {filename} ({s3_key})')

    # Check S3 files - look in all locations
    s3_client = boto3.client('s3', region_name='eu-west-2')
    
    # Check r/ directory
    response = s3_client.list_objects_v2(Bucket='ocr-site-bc930bd1', Prefix='r/')
    r_files = response.get('Contents', [])
    print(f'\nFound {len(r_files)} files in S3 r/ directory')
    
    # Check uploads/ directory
    response = s3_client.list_objects_v2(Bucket='ocr-site-bc930bd1', Prefix='uploads/')
    uploads_files = response.get('Contents', [])
    print(f'Found {len(uploads_files)} files in S3 uploads/ directory')
    
    # Check root directory
    response = s3_client.list_objects_v2(Bucket='ocr-site-bc930bd1')
    all_files = response.get('Contents', [])
    root_files = [f for f in all_files if not f['Key'].startswith(('r/', 'uploads/'))]
    print(f'Found {len(root_files)} files in S3 root directory')
    
    files = r_files + uploads_files + root_files
    print(f'\nTotal files found: {len(files)}')

    pdf_files = [f for f in files if f['Key'].endswith('.pdf')]
    image_files = [f for f in files if f['Key'].endswith(('.jpg', '.jpeg', '.png'))]

    print(f'PDF files: {len(pdf_files)}')
    for f in pdf_files:
        print(f'  - {f["Key"]}')
    print(f'Image files: {len(image_files)}')
    for f in image_files:
        print(f'  - {f["Key"]}')

    # Check which files have extractions
    s3_keys_in_db = {item.get('s3_key') for item in items if item.get('s3_key')}
    missing_extractions = []

    for file in files:
        if file['Key'].endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            if file['Key'] not in s3_keys_in_db:
                missing_extractions.append(file['Key'])

    print(f'\nMissing extractions: {len(missing_extractions)}')
    for key in missing_extractions:
        print(f'  - {key}')

    return missing_extractions

if __name__ == "__main__":
    check_extractions()
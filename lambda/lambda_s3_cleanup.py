import os
import json
import pg8000
import boto3

def lambda_handler(event, context):
    # Database connection
    conn = pg8000.connect(
        host=os.environ['DB_HOST'],
        port=int(os.environ.get('DB_PORT', 5432)),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'password123'),  # Use environment variable
        database=os.environ.get('DB_NAME', 'hey')
    )
    cursor = conn.cursor()

    # Process S3 events
    for record in event['Records']:
        s3_key = record['s3']['object']['key']
        print(f"Processing S3 event for object: {s3_key}")

        if record['eventName'].startswith('ObjectCreated'):
            # Insert into tblUploads
            # Parse restaurant_id from key: r/{restaurant_id}/{filename}
            parts = s3_key.split('/')
            if len(parts) >= 3 and parts[0] == 'r':
                try:
                    restaurant_id = int(parts[1])
                    cursor.execute(
                        'INSERT INTO tblUploads (Restaurant_ID, S3_Path) VALUES (%s, %s)',
                        (restaurant_id, s3_key)
                    )
                    print(f"Inserted record into tblUploads for S3 key: {s3_key}")
                except ValueError:
                    print(f"Invalid restaurant ID in S3 key: {s3_key}")
                except Exception as e:
                    print(f"Error inserting into tblUploads: {e}")
            else:
                print(f"S3 key does not match expected format: {s3_key}")

        elif record['eventName'].startswith('ObjectRemoved'):
            # Delete from tblUploads
            try:
                cursor.execute(
                    'DELETE FROM tblUploads WHERE S3_Path = %s',
                    (s3_key,)
                )
                deleted_count = cursor.rowcount
                print(f"Deleted {deleted_count} record(s) from tblUploads for S3 key: {s3_key}")
            except Exception as e:
                print(f"Error deleting from tblUploads: {e}")

    conn.commit()
    conn.close()

    return {
        'statusCode': 200,
        'body': json.dumps('S3 event processing completed')
    }
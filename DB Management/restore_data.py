import pg8000
import csv
import os
import boto3
import json
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_host():
    """Get DB_HOST from environment or Terraform output"""
    db_host = os.environ.get('DB_HOST')
    if db_host:
        return db_host
    
    # Get from Terraform output
    try:
        result = subprocess.run(['terraform', 'output', '-raw', 'rds_endpoint'], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            endpoint = result.stdout.strip()
            return endpoint.split(':')[0]
    except Exception as e:
        print(f"Warning: Could not get DB_HOST from Terraform: {e}")
    
def get_s3_bucket():
    """Get S3 bucket name from environment or Terraform output"""
    bucket = os.environ.get('S3_BUCKET')
    if bucket:
        return bucket
    
    # Get from Terraform output
    try:
        result = subprocess.run(['terraform', 'output', '-raw', 's3_bucket_name'], 
                              capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"Warning: Could not get S3_BUCKET from Terraform: {e}")
    
    # Fallback - search for bucket with prefix
    try:
        s3_client = boto3.client('s3', region_name='eu-west-2')
        buckets = s3_client.list_buckets()
        for bucket in buckets['Buckets']:
            if bucket['Name'].startswith('ocr-site-'):
                return bucket['Name']
    except Exception as e:
        print(f"Warning: Could not find S3 bucket: {e}")
    
    return None

# Database connection details - loaded from environment variables
DB_HOST = get_db_host()
DB_NAME = os.environ.get('DB_NAME', 'hey')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password123')  # Fallback for development
DB_PORT = int(os.environ.get('DB_PORT', 5432))

def restore_postgresql(backup_dir):
    """Restore PostgreSQL data from CSV files"""
    print("📊 Restoring PostgreSQL database...")

    pg_backup_dir = os.path.join(backup_dir, "postgresql")
    if not os.path.exists(pg_backup_dir):
        print("⚠️  No PostgreSQL backup directory found, skipping...")
        return

    try:
        # Connect to the database
        conn = pg8000.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )

        cursor = conn.cursor()

        # First, run init_db.sql to create tables if they don't exist
        init_sql_path = os.path.join(os.path.dirname(__file__), 'init_db.sql')
        if os.path.exists(init_sql_path):
            print("🏗️  Creating database tables...")
            with open(init_sql_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Split SQL into individual statements
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    try:
                        cursor.execute(statement)
                        conn.commit()  # Commit after each successful statement
                        print(f"✅ Executed: {statement[:50]}...")
                    except Exception as e:
                        conn.rollback()  # Rollback on error
                        print(f"⚠️  Statement failed (might already exist): {statement[:50]}... - {e}")
                        # Continue with next statement
        else:
            print("⚠️  init_db.sql not found, assuming tables already exist")

        # Get list of CSV files
        csv_files = [f for f in os.listdir(pg_backup_dir) if f.endswith('.csv')]
        if not csv_files:
            print("⚠️  No CSV files found in backup, skipping...")
            return

        print(f"📋 Found {len(csv_files)} CSV files to restore:")
        for csv_file in csv_files:
            print(f"  - {csv_file}")

        for csv_file in csv_files:
            table_name = csv_file.replace('.csv', '')
            csv_path = os.path.join(pg_backup_dir, csv_file)

            try:
                # Read CSV data
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    headers = next(reader)  # Skip header row
                    rows = list(reader)

                if not rows:
                    print(f"⚠️  {csv_file} is empty, skipping...")
                    continue

                # For fresh deployments, assume tables are empty
                # Check if table has data
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]

                if count > 0:
                    print(f"⚠️  {table_name} already has {count} records. Skipping to avoid conflicts...")
                    continue

                # Prepare INSERT statement
                placeholders = ', '.join(['%s'] * len(headers))
                columns = ', '.join(headers)
                insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

                # Insert data in batches
                batch_size = 100
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]
                    cursor.executemany(insert_sql, batch)

                conn.commit()
                print(f"✅ Restored {len(rows)} records to {table_name}")

            except Exception as e:
                print(f"❌ Error restoring {table_name}: {e}")
                conn.rollback()

        cursor.close()
        conn.close()

        print("✅ PostgreSQL restore completed!")

    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")

def restore_dynamodb(backup_dir):
    """Restore DynamoDB tables from JSON files"""
    print("📊 Restoring DynamoDB tables...")

    ddb_backup_dir = os.path.join(backup_dir, "dynamodb")
    if not os.path.exists(ddb_backup_dir):
        print("⚠️  No DynamoDB backup directory found, skipping...")
        return

    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')

        # Get list of JSON files
        json_files = [f for f in os.listdir(ddb_backup_dir) if f.endswith('.json')]
        if not json_files:
            print("⚠️  No JSON files found in backup, skipping...")
            return

        print(f"📋 Found {len(json_files)} JSON files to restore:")
        for json_file in json_files:
            print(f"  - {json_file}")

        for json_file in json_files:
            table_name = json_file.replace('.json', '')
            json_path = os.path.join(ddb_backup_dir, json_file)

            try:
                # Read JSON data
                with open(json_path, 'r', encoding='utf-8') as f:
                    items = json.load(f)

                if not items:
                    print(f"⚠️  {json_file} is empty, skipping...")
                    continue

                # Check if table exists, create if not
                try:
                    table = dynamodb.Table(table_name)
                    table.table_status  # This will raise exception if table doesn't exist
                except Exception:
                    print(f"⚠️  Table {table_name} doesn't exist, skipping...")
                    continue

                # Clear existing items (optional)
                # Note: This is expensive for large tables, consider if needed
                try:
                    scan_response = table.scan()
                    if scan_response['Items']:
                        print(f"🧹 Clearing existing items from {table_name}...")
                        with table.batch_writer() as batch:
                            for item in scan_response['Items']:
                                batch.delete_item(Key={k: v for k, v in item.items() if k in table.key_schema})
                except Exception as e:
                    print(f"⚠️  Could not clear table {table_name}: {e}")

                # Restore items
                with table.batch_writer() as batch:
                    for item in items:
                        # Convert Decimal to float for JSON serialization
                        processed_item = {}
                        for k, v in item.items():
                            if isinstance(v, dict) and 'S' in v:  # DynamoDB JSON format
                                processed_item[k] = v['S']
                            elif isinstance(v, dict) and 'N' in v:
                                processed_item[k] = float(v['N']) if '.' in v['N'] else int(v['N'])
                            else:
                                processed_item[k] = v
                        batch.put_item(Item=processed_item)

                print(f"✅ Restored {len(items)} items to {table_name}")

            except Exception as e:
                print(f"❌ Error restoring {table_name}: {e}")

        print("✅ DynamoDB restore completed!")

    except Exception as e:
        print(f"❌ Error initializing DynamoDB: {e}")

def restore_s3(backup_dir):
    """Restore S3 objects from backup files"""
    print("📊 Restoring S3 bucket...")

    s3_backup_dir = os.path.join(backup_dir, "s3")
    if not os.path.exists(s3_backup_dir):
        print("⚠️  No S3 backup directory found, skipping...")
        return

    try:
        s3_client = boto3.client('s3', region_name='eu-west-2')

        # Get the bucket name from Terraform output
        bucket_name = get_s3_bucket()

        if not bucket_name:
            print("⚠️  Could not determine S3 bucket name, skipping S3 restore...")
            return

        print(f"📦 Found S3 bucket: {bucket_name}")

        # Get list of files to restore
        files = os.listdir(s3_backup_dir)
        if not files:
            print("⚠️  No files found in S3 backup, skipping...")
            return

        print(f"📋 Found {len(files)} files to restore:")

        restored_count = 0
        for filename in files:
            local_path = os.path.join(s3_backup_dir, filename)

            # Reverse the flattening: convert underscores back to slashes
            if filename.startswith('r_') and '_' in filename:
                # This was originally in a restaurant subdirectory like r_2_filename.jpg -> r/2/filename.jpg
                parts = filename.split('_', 2)  # Split into ['r', '2', 'filename.jpg']
                if len(parts) >= 3:
                    restaurant_id = parts[1]
                    original_filename = parts[2]
                    original_key = f"r/{restaurant_id}/{original_filename}"
                else:
                    original_key = filename  # Fallback
            else:
                # This was in the root directory
                original_key = filename

            try:
                # Upload the file
                with open(local_path, 'rb') as f:
                    s3_client.put_object(
                        Bucket=bucket_name,
                        Key=original_key,
                        Body=f
                    )

                print(f"  ✅ Restored: {original_key}")
                restored_count += 1

            except Exception as e:
                print(f"  ❌ Error restoring {filename}: {e}")

        print(f"✅ Restored {restored_count} objects to S3 bucket {bucket_name}")

        print("✅ S3 restore completed!")

    except Exception as e:
        print(f"❌ Error restoring S3: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python restore_data.py <backup_directory>")
        print("Example: python restore_data.py backup_20260212_003438")
        sys.exit(1)

    backup_dir = sys.argv[1]

    if not os.path.exists(backup_dir):
        print(f"❌ Backup directory '{backup_dir}' does not exist!")
        sys.exit(1)

    print(f"🚀 Starting restore from directory: {backup_dir}")
    print("=" * 50)

    # Restore in order: PostgreSQL first, then DynamoDB, then S3
    restore_postgresql(backup_dir)
    print()
    restore_dynamodb(backup_dir)
    print()
    restore_s3(backup_dir)
    print()

    print("=" * 50)
    print(f"✅ Restore completed from: {backup_dir}")
    print("🔍 Verify your application is working with the restored data!")

if __name__ == "__main__":
    main()
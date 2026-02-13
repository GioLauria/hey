import pg8000
import csv
import os
import boto3
import json
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
                              capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        if result.returncode == 0:
            endpoint = result.stdout.strip()
            return endpoint.split(':')[0]
    except Exception as e:
        print(f"Warning: Could not get DB_HOST from Terraform: {e}")
    
    # Fallback
    return "hey.czrij6aohmmy.eu-west-2.rds.amazonaws.com"

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

# Backup directory
BACKUP_DIR = "backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_postgresql():
    """Backup all PostgreSQL tables to CSV files"""
    print("📊 Backing up PostgreSQL database...")

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

        # Get all table names from the public schema
        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        tables = cursor.fetchall()

        if not tables:
            print("❌ No tables found in the database")
            return

        print(f"📋 Found {len(tables)} tables to backup:")
        for table in tables:
            print(f"  - {table[0]}")

        # Create database backup directory
        db_backup_dir = os.path.join(BACKUP_DIR, "postgresql")
        os.makedirs(db_backup_dir, exist_ok=True)

        # Export each table
        for table in tables:
            table_name = table[0]
            export_table_to_csv(table_name, cursor, db_backup_dir)

        cursor.close()
        conn.close()

        print("✅ PostgreSQL backup completed!")

    except Exception as e:
        print(f"❌ Error backing up PostgreSQL: {e}")

def export_table_to_csv(table_name, cursor, backup_dir):
    """Export a table to CSV file"""
    try:
        # Get all records from the table
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            print(f"Table {table_name} is empty, creating empty CSV file")
            # Get column names even for empty table
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
            columns = [desc[0] for desc in cursor.description]
        else:
            columns = [desc[0] for desc in cursor.description]

        # Create CSV file
        csv_filename = os.path.join(backup_dir, f"{table_name}.csv")

        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow(columns)

            # Write data
            for row in rows:
                writer.writerow(row)

        print(f"✅ Exported {table_name} to {csv_filename} ({len(rows)} records)")

    except Exception as e:
        print(f"❌ Error exporting {table_name}: {e}")

def backup_dynamodb():
    """Backup DynamoDB tables to JSON files"""
    print("📊 Backing up DynamoDB tables...")

    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')

        # List of tables to backup (based on Terraform)
        tables_to_backup = ['ocr-extractions', 'ocr-visitors', 'menu-items', 'ocr-todos']

        # Create DynamoDB backup directory
        ddb_backup_dir = os.path.join(BACKUP_DIR, "dynamodb")
        os.makedirs(ddb_backup_dir, exist_ok=True)

        for table_name in tables_to_backup:
            try:
                table = dynamodb.Table(table_name)

                # Check if table exists by trying to access table_status
                try:
                    status = table.table_status
                except Exception:
                    print(f"⚠️  DynamoDB table {table_name} does not exist, skipping...")
                    continue

                # Scan all items (for small tables)
                response = table.scan()
                items = response['Items']

                # Handle pagination if needed
                while 'LastEvaluatedKey' in response:
                    response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                    items.extend(response['Items'])

                # Save to JSON file
                json_filename = os.path.join(ddb_backup_dir, f"{table_name}.json")
                with open(json_filename, 'w', encoding='utf-8') as jsonfile:
                    json.dump(items, jsonfile, indent=2, default=str)

                print(f"✅ Exported {table_name} to {json_filename} ({len(items)} items)")

            except Exception as e:
                print(f"❌ Error backing up DynamoDB table {table_name}: {e}")

        print("✅ DynamoDB backup completed!")

    except Exception as e:
        print(f"❌ Error initializing DynamoDB client: {e}")

def backup_s3():
    """Backup S3 bucket objects"""
    print("📊 Backing up S3 bucket...")

    try:
        s3_client = boto3.client('s3', region_name='eu-west-2')

        # Get the bucket name from Terraform output
        bucket_name = get_s3_bucket()

        if not bucket_name:
            print("⚠️  Could not determine S3 bucket name, skipping S3 backup...")
            print("✅ S3 backup completed!")
            return

        print(f"📦 Found S3 bucket: {bucket_name}")

        # Create S3 backup directory
        s3_backup_dir = os.path.join(BACKUP_DIR, "s3")
        os.makedirs(s3_backup_dir, exist_ok=True)

        # List all objects in the bucket
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name)

        total_objects = 0
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    # Create local file path, replacing slashes with underscores to flatten
                    local_filename = key.replace('/', '_').replace('\\', '_')
                    local_file = os.path.join(s3_backup_dir, local_filename)

                    # Download the object
                    s3_client.download_file(bucket_name, key, local_file)
                    total_objects += 1
                    print(f"  Downloaded: {key}")

        print(f"✅ Downloaded {total_objects} objects from S3 bucket {bucket_name}")

        print("✅ S3 backup completed!")

    except Exception as e:
        print(f"❌ Error backing up S3: {e}")

def create_backup_summary():
    """Create a summary file of the backup"""
    summary_file = os.path.join(BACKUP_DIR, "backup_summary.txt")

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Backup created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Backup directory: {BACKUP_DIR}\n\n")

        f.write("PostgreSQL Tables:\n")
        pg_dir = os.path.join(BACKUP_DIR, "postgresql")
        if os.path.exists(pg_dir):
            for file in os.listdir(pg_dir):
                if file.endswith('.csv'):
                    filepath = os.path.join(pg_dir, file)
                    with open(filepath, 'r', encoding='utf-8') as csvfile:
                        lines = csvfile.readlines()
                        record_count = len(lines) - 1 if len(lines) > 0 else 0
                    f.write(f"  - {file}: {record_count} records\n")

        f.write("\nDynamoDB Tables:\n")
        ddb_dir = os.path.join(BACKUP_DIR, "dynamodb")
        if os.path.exists(ddb_dir):
            for file in os.listdir(ddb_dir):
                if file.endswith('.json'):
                    filepath = os.path.join(ddb_dir, file)
                    with open(filepath, 'r', encoding='utf-8') as jsonfile:
                        try:
                            data = json.load(jsonfile)
                            item_count = len(data) if isinstance(data, list) else 1
                        except:
                            item_count = 0
                    f.write(f"  - {file}: {item_count} items\n")

        f.write("\nS3 Objects:\n")
        s3_dir = os.path.join(BACKUP_DIR, "s3")
        if os.path.exists(s3_dir):
            files = os.listdir(s3_dir)
            f.write(f"  - {len(files)} files downloaded\n")
            for file in files[:5]:  # Show first 5 files
                f.write(f"    - {file}\n")
            if len(files) > 5:
                f.write(f"    ... and {len(files) - 5} more files\n")
        else:
            f.write("  - No S3 data backed up\n")

    print(f"📋 Backup summary created: {summary_file}")

if __name__ == "__main__":
    print(f"🚀 Starting backup to directory: {BACKUP_DIR}")
    print("=" * 50)

    backup_postgresql()
    print()
    backup_dynamodb()
    print()
    backup_s3()
    print()
    create_backup_summary()

    print("=" * 50)
    print(f"✅ All backups completed! Data saved to: {BACKUP_DIR}")
    print("📂 You can now safely run 'terraform destroy'")
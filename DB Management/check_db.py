import pg8000
import os
import subprocess
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

# Database connection details - loaded from environment variables
DB_HOST = get_db_host()  # From Terraform output
DB_NAME = os.environ.get('DB_NAME', 'hey')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password123')  # Fallback for development
DB_PORT = int(os.environ.get('DB_PORT', 5432))

def check_database_content():
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

        # Check each table
        tables = ['tblReferenti', 'tblRistoranti', 'tblUploads']

        for table in tables:
            print(f"\n=== {table} ===")

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Total records: {count}")

            if count > 0:
                # Get all records
                cursor.execute(f"SELECT * FROM {table} LIMIT 10")  # Limit to 10 records for display
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                print(f"Columns: {', '.join(columns)}")
                print("-" * 50)

                for row in rows:
                    print(row)

                if count > 10:
                    print(f"... and {count - 10} more records")
            else:
                print("No records found")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    check_database_content()
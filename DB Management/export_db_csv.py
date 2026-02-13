import pg8000
import csv
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
DB_HOST = get_db_host()
DB_NAME = os.environ.get('DB_NAME', 'hey')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password123')  # Fallback for development
DB_PORT = int(os.environ.get('DB_PORT', 5432))

# Output directory
OUTPUT_DIR = "PSQL"

def export_table_to_csv(table_name, cursor):
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
        csv_filename = os.path.join(OUTPUT_DIR, f"{table_name}.csv")

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

def export_database_to_csv():
    """Export all tables to CSV files"""
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

        print(f"📊 Found {len(tables)} tables to export:")
        for table in tables:
            print(f"  - {table[0]}")

        print(f"\n📁 Exporting to directory: {OUTPUT_DIR}")
        print("=" * 50)

        # Export each table
        for table in tables:
            table_name = table[0]
            export_table_to_csv(table_name, cursor)

        cursor.close()
        conn.close()

        print("\n✅ All tables exported successfully!")
        print(f"📂 Check the '{OUTPUT_DIR}' folder for CSV files")

    except Exception as e:
        print(f"❌ Error connecting to database: {e}")

if __name__ == "__main__":
    export_database_to_csv()
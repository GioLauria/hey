import json
import pg8000
import os

def lambda_handler(event, context):
    # Database connection
    conn = pg8000.connect(
        host=os.environ.get('DB_HOST', 'hey.czrij6aohmmy.eu-west-2.rds.amazonaws.com'),
        port=int(os.environ.get('DB_PORT', 5432)),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'password123'),  # Use environment variable
        database=os.environ.get('DB_NAME', 'hey')
    )
    cursor = conn.cursor()

    # Create tables if not exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tblReferenti (
            ID SERIAL PRIMARY KEY,
            Nome VARCHAR(255) NOT NULL,
            Email VARCHAR(255),
            Telefono VARCHAR(50)
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tblRistoranti (
            ID SERIAL PRIMARY KEY,
            Name VARCHAR(255) NOT NULL,
            Address VARCHAR(255),
            City VARCHAR(255),
            Country VARCHAR(255),
            Referente_ID INTEGER REFERENCES tblReferenti(ID) UNIQUE
        );
    ''')

    # Check if data exists
    cursor.execute('SELECT COUNT(*) FROM tblRistoranti')
    if cursor.fetchone()[0] == 0:
        # Insert sample data
        cursor.execute("INSERT INTO tblReferenti (Nome) VALUES ('Mario Rossi') RETURNING ID")
        ref_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO tblRistoranti (Name, City, Referente_ID) VALUES ('Trattoria Roma', 'Turin', %s)", (ref_id,))
        
        cursor.execute("INSERT INTO tblReferenti (Nome) VALUES ('Luigi Bianchi') RETURNING ID")
        ref_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO tblRistoranti (Name, City, Referente_ID) VALUES ('Pizzeria Milano', 'Milan', %s)", (ref_id,))
        
        conn.commit()

    # Query restaurants
    cursor.execute('SELECT ID, Name, City FROM tblRistoranti')
    rows = cursor.fetchall()
    restaurants = [{'id': row[0], 'name': f"{row[1]} - {row[2]}"} for row in rows]

    conn.close()
    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(restaurants)
    }
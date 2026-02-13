import json
import pg8000
import os

def handler(event, context):
    try:
        # Database connection using pg8000 (pure Python)
        conn = pg8000.connect(
            host=os.environ.get('DB_HOST', "hey.czrij6aohmmy.eu-west-2.rds.amazonaws.com"),
            database=os.environ.get('DB_NAME', "hey"),
            user=os.environ.get('DB_USER', "postgres"),
            password=os.environ.get('DB_PASSWORD', "password123"),  # Use environment variable
            port=int(os.environ.get('DB_PORT', 5432))
        )
        cur = conn.cursor()
        
        # Create tables if not exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tblReferenti (
                ID SERIAL PRIMARY KEY,
                Nome VARCHAR(255) NOT NULL,
                Email VARCHAR(255),
                Telefono VARCHAR(50)
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tblRistoranti (
                ID SERIAL PRIMARY KEY,
                Name VARCHAR(255) NOT NULL,
                Address VARCHAR(255),
                City VARCHAR(255),
                Country VARCHAR(255),
                Referente_ID INTEGER REFERENCES tblReferenti(ID) UNIQUE
            );
        """)
        
        # Insert sample data if not exists
        cur.execute("SELECT COUNT(*) FROM tblReferenti")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO tblReferenti (Nome, Email, Telefono) VALUES
                ('Mario Rossi', 'mario.rossi@example.com', '+39 123 456 7890'),
                ('Luca Bianchi', 'luca.bianchi@example.com', '+39 234 567 8901'),
                ('Giulia Verdi', 'giulia.verdi@example.com', '+39 345 678 9012'),
                ('Anna Neri', 'anna.neri@example.com', '+39 456 789 0123'),
                ('Paolo Blu', 'paolo.blu@example.com', '+39 567 890 1234');
            """)
            cur.execute("""
                INSERT INTO tblRistoranti (Name, Address, City, Country, Referente_ID) VALUES
                ('Trattoria Roma', 'Via Roma 1', 'Roma', 'Italia', 1),
                ('Pizzeria Napoli', 'Via Napoli 2', 'Napoli', 'Italia', 2),
                ('Osteria Milano', 'Via Milano 3', 'Milano', 'Italia', 3),
                ('Ristorante Firenze', 'Via Firenze 4', 'Firenze', 'Italia', 4),
                ('Bar Torino', 'Via Torino 5', 'Torino', 'Italia', 5);
            """)
        
        cur.execute("SELECT Name, City FROM tblRistoranti")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Format as list of "Name - City"
        restaurants = [f"{row[0]} - {row[1]}" for row in rows]

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(restaurants)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }
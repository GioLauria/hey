# Lambda: Restaurants List (`lambda/restaurants/main.py`)

## Overview
This Lambda function provides a REST API endpoint to retrieve a list of restaurants from the PostgreSQL database. It creates the necessary tables and inserts sample data if they don't exist, then returns the restaurant list formatted as "Name - City".

## Configuration
- **Runtime**: Python 3.9
- **Handler**: `main.handler`
- **Timeout**: 60 seconds
- **Memory**: 128 MB
- **VPC**: Configured with RDS subnets and security group for database access

## Dependencies
- `pg8000`: Pure Python PostgreSQL driver for database connectivity

## Database Schema
### tblReferenti
- `ID` (SERIAL PRIMARY KEY)
- `Nome` (VARCHAR(255) NOT NULL)
- `Email` (VARCHAR(255))
- `Telefono` (VARCHAR(50))

### tblRistoranti
- `ID` (SERIAL PRIMARY KEY)
- `Name` (VARCHAR(255) NOT NULL)
- `Address` (VARCHAR(255))
- `City` (VARCHAR(255))
- `Country` (VARCHAR(255))
- `Referente_ID` (INTEGER REFERENCES tblReferenti(ID) UNIQUE)

## API Response
Returns JSON array of strings in format "Restaurant Name - City":
```json
[
  "Trattoria Roma - Roma",
  "Pizzeria Napoli - Napoli",
  "Osteria Milano - Milano",
  "Ristorante Firenze - Firenze",
  "Bar Torino - Torino"
]
```

## Error Handling
Returns JSON error object with error message on database connection or query failures.

## CORS
Includes `Access-Control-Allow-Origin: *` header for web access.
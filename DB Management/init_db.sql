-- Create table tblreferenti
CREATE TABLE IF NOT EXISTS tblreferenti (
    ID SERIAL PRIMARY KEY,
    Nome VARCHAR(255) NOT NULL,
    Email VARCHAR(255),
    Telefono VARCHAR(50)
);

-- Create table tblristoranti
CREATE TABLE IF NOT EXISTS tblristoranti (
    ID SERIAL PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    Address VARCHAR(255),
    City VARCHAR(255),
    Country VARCHAR(255),
    Referente_ID INTEGER REFERENCES tblreferenti(ID) UNIQUE
);

-- Create table tbluploads
CREATE TABLE IF NOT EXISTS tbluploads (
    ID SERIAL PRIMARY KEY,
    Restaurant_ID INTEGER REFERENCES tblristoranti(ID),
    S3_Path VARCHAR(500) NOT NULL
);
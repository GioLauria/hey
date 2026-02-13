-- Insert sample data into tblReferenti
INSERT INTO tblReferenti (Nome, Email, Telefono) VALUES
('Mario Rossi', 'mario.rossi@example.com', '+39 123 456 7890'),
('Luca Bianchi', 'luca.bianchi@example.com', '+39 234 567 8901'),
('Giulia Verdi', 'giulia.verdi@example.com', '+39 345 678 9012'),
('Anna Neri', 'anna.neri@example.com', '+39 456 789 0123'),
('Paolo Blu', 'paolo.blu@example.com', '+39 567 890 1234');

-- Insert sample data into tblRistoranti (1:1 with referenti)
INSERT INTO tblRistoranti (Name, Address, City, Country, Referente_ID) VALUES
('Trattoria Roma', 'Via Roma 1', 'Roma', 'Italia', 1),
('Pizzeria Napoli', 'Via Napoli 2', 'Napoli', 'Italia', 2),
('Osteria Milano', 'Via Milano 3', 'Milano', 'Italia', 3),
('Ristorante Firenze', 'Via Firenze 4', 'Firenze', 'Italia', 4),
('Bar Torino', 'Via Torino 5', 'Torino', 'Italia', 5);
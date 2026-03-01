# Hey - OCR Restaurant Management System

Un sistema completo per la gestione di ristoranti con funzionalità OCR per l'estrazione di testo da documenti e immagini.

## 🚀 Caratteristiche

- **OCR Automatico**: Estrazione testo da PDF e immagini usando AWS Textract e pypdf
- **Gestione Ristoranti**: Database PostgreSQL per ristoranti e referenti
- **Archiviazione Cloud**: AWS S3 per documenti e immagini
- **API Serverless**: AWS Lambda per elaborazione backend
- **Frontend Web**: Interfaccia utente per upload e visualizzazione risultati
- **Storico Estrazioni**: Visualizza e scarica file elaborati in precedenza
- **Analisi NLP**: Validazione testo con Amazon Comprehend
- **Monitoraggio Costi**: Dashboard per costi AWS in tempo reale

## 📋 Prerequisiti

- Python 3.8+
- AWS CLI configurato
- Terraform 1.0+
- Account AWS

## 🛠️ Installazione e Configurazione

### 1. Clona il repository
```bash
git clone <repository-url>
cd Hey
```

### 2. Installa dipendenze Python
```bash
pip install -r requirements.txt
```

### 3. Configura le variabili d'ambiente

Copia il file di esempio e configura le tue credenziali:
```bash
cp .env.example .env
```

Modifica `.env` con i tuoi valori reali:
```env
# Database PostgreSQL
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_NAME=hey
DB_USER=postgres
DB_PASSWORD=your-secure-password-here
DB_PORT=5432

# AWS (opzionale, usa AWS CLI)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=eu-west-2
```

### 4. Configura Terraform

Copia il file di variabili Terraform:
```bash
cp terraform.tfvars.example terraform.tfvars
```

Modifica `terraform.tfvars` con i tuoi valori:
```hcl
# Database password
db_username = "postgres"
db_password = "your-secure-password-here"

# AWS Region
region = "eu-west-2"

# Project name
project_name = "Hey"
```

### 5. Deploy dell'infrastruttura
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## 🌐 Stato Deploy Corrente (Febbraio 2026)

### Servizi AWS Deployati
- ✅ **API Gateway** con 6 routes (GET/POST/PUT)
- ✅ **Lambda Functions**: validate-text, visitor-stats (+ altre in deploy)
- ✅ **DynamoDB Tables**: ocr-extractions, ocr-visitors, menu-items, ocr-todos
Note: I recently adjusted the Terraform DynamoDB configuration. The project keeps `hash_key` in `terraform/dynamodb.tf` to stay compatible with the current AWS provider in this repo; do `terraform validate` in the `terraform` folder before applying changes. If you upgrade the provider to a version that supports `key_schema`, consider migrating accordingly.

**Developer Setup**

- **Enable repository hooks (recommended)**: the project provides a repository hooks folder `.githooks` with a `pre-commit` script that validates Terraform and Python syntax. To enable locally run:

```bash
git config core.hooksPath .githooks
```

- **Quick validation workflow**:

```bash
cd terraform
terraform init -backend=false
terraform validate
```

- **Commits**: We sign commits in this repo. Configure GPG signing or use your platform key. To skip hooks for a one-off commit, use `--no-verify`.

- **Docs**: Additional developer docs are available in the `docs/` folder — see `docs/index.md`.
- ✅ **RDS PostgreSQL**: Database per gestione ristoranti
- ✅ **S3 Bucket**: Hosting sito statico con CloudFront
- ✅ **VPC**: Rete isolata con subnet private/public
- ✅ **WAF**: Protezione sicurezza per il sito web

### Come Accedere
1. **Sito Web**: Visita l'URL S3 website per l'interfaccia utente
2. **API**: Usa l'API Gateway URL per chiamate backend
3. **Database**: PostgreSQL accessibile via Lambda functions

## 🔒 Sicurezza e Credenziali

**IMPORTANTE**: Questo progetto è configurato per NON includere credenziali nel codice sorgente.

### File esclusi dal Git:
- `.env` (variabili d'ambiente locali)
- `terraform.tfvars` (variabili Terraform)
- `terraform.tfstate*` (stato Terraform con dati sensibili)

### Alternative per la produzione:

#### 1. AWS Secrets Manager (Raccomandato)
```python
import boto3

secrets_client = boto3.client('secretsmanager')
secret = secrets_client.get_secret_value(SecretId='your-db-secret')
db_config = json.loads(secret['SecretString'])
```

#### 2. AWS Systems Manager Parameter Store
```python
import boto3

ssm_client = boto3.client('ssm')
password = ssm_client.get_parameter(
    Name='/prod/db/password',
    WithDecryption=True
)['Parameter']['Value']
```

#### 3. Variabili d'ambiente Lambda
Configura le variabili d'ambiente direttamente nella console AWS Lambda o tramite Terraform.

## 🚀 Utilizzo

### Database Management
```bash
# Esporta dati
python 'DB Management/export_db_csv.py'

# Controlla contenuto database
python 'DB Management/check_db.py'

# Backup completo
python 'DB Management/backup_data.py'

# Restore da backup
python 'DB Management/restore_data.py' backup_20240101_120000
```

### Sito Web
Apri `site/index.html` nel browser per accedere all'interfaccia web.

## 📁 Struttura del Progetto

```
Hey/
├── DB Management/          # Script gestione database
├── lambda/                 # Funzioni AWS Lambda
├── site/                   # Frontend web
├── scripts/                # Documentazione funzioni
├── main.tf                 # Configurazione Terraform
├── variables.tf            # Variabili Terraform
├── requirements.txt        # Dipendenze Python
├── .env.example           # Template variabili ambiente
├── terraform.tfvars.example # Template variabili Terraform
└── .gitignore             # File da escludere dal Git
```

## 🔧 Troubleshooting

### Errore connessione database
1. Verifica che `.env` sia configurato correttamente
2. Controlla che l'RDS sia accessibile: `terraform output rds_endpoint`
3. Assicurati che la security group permetta connessioni

### Errore deploy Lambda
1. Verifica che le variabili d'ambiente siano configurate in Terraform
2. Controlla i log CloudWatch per errori specifici

## 📝 Note di Sviluppo

- Le password di default sono `password123` per sviluppo locale
- In produzione, usa password complesse e ruota regolarmente
- Monitora i costi AWS, specialmente Textract e Lambda

## 🤝 Contributi

1. Crea un fork del progetto
2. Crea un branch per la tua feature (`git checkout -b feature/nuova-feature`)
3. Committa le modifiche (`git commit -am 'Aggiunge nuova feature'`)
4. Pusha il branch (`git push origin feature/nuova-feature`)
5. Crea una Pull Request

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi il file `LICENSE` per dettagli.
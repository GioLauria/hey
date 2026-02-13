# Data Backup and Restore Scripts

This project includes both backup (`backup_data.py`) and restore (`restore_data.py`) scripts to safely migrate your data when redeploying the infrastructure.

## Backup Script

### Usage:
```bash
python backup_data.py
```

## Restore Script

After redeploying your infrastructure with `terraform apply`, restore your data:

### Usage:
```bash
python restore_data.py <backup_directory>
```

Example:
```bash
python restore_data.py backup_20260212_003438
```

### What the restore script does:

#### PostgreSQL Restore:
- Connects to your RDS database
- Clears existing data from tables (optional)
- Imports CSV data back into tables
- Handles errors gracefully

#### DynamoDB Restore:
- Checks if tables exist
- Clears existing items (optional)
- Restores items from JSON files
- Handles DynamoDB data types correctly

#### S3 Restore:
- Finds your S3 bucket (ocr-site-*)
- Uploads files back to their original keys
- Reverses the filename flattening from backup

### Important Notes:
- **Run restore AFTER `terraform apply`** - Make sure your infrastructure is deployed first
- **PostgreSQL tables should be empty** - The script assumes fresh deployment with empty tables
- **DynamoDB tables should be empty** - Same for DynamoDB tables
- **S3 bucket should be empty** - The bucket should be freshly created by Terraform
- **Foreign key constraints** - The script handles relationships correctly by checking for existing data
- **Data merging** - If tables have data, the script skips restoration to avoid conflicts

## Complete Migration Workflow

### Before Destroying Infrastructure:
```bash
# 1. Backup all data
python backup_data.py
# Creates: backup_YYYYMMDD_HHMMSS/

# 2. Destroy infrastructure
terraform destroy

# 3. Make any code/infrastructure changes
# Edit your Terraform files, Lambda code, etc.

# 4. Redeploy infrastructure
terraform apply
```

### After Redeploying Infrastructure:
```bash
# 5. Restore all data
python restore_data.py backup_YYYYMMDD_HHMMSS

# 6. Verify application works
# - Check restaurant data loads
# - Test OCR functionality
# - Verify uploaded images display
```

## What Gets Backed Up and Restored:

### PostgreSQL Database:
- `tblreferenti` - Contact references
- `tblristoranti` - Restaurant information
- `tbluploads` - Upload records with S3 paths

### DynamoDB Tables:
- `ocr-extractions` - OCR text extraction results
- `ocr-visitors` - Visitor counter data
- `menu-items` - Menu item data
- `ocr-todos` - To-do list items

### S3 Bucket:
- All uploaded images and files
- Website assets (HTML, CSS, JS)
- Maintains original directory structure

### Restore Order:
1. PostgreSQL (database schema and relationships)
2. DynamoDB (application data)
3. S3 (uploaded files and images)

### Troubleshooting:
- If PostgreSQL restore fails due to foreign keys, ensure tables are empty
- If DynamoDB tables don't exist, they will be skipped
- If S3 bucket is not found, check your Terraform deployment
- Check the backup_summary.txt for what was backed up

## What it backs up:

### PostgreSQL Database:
- All tables in the `hey` database
- Exports each table to CSV format
- Includes table schema (column headers)

### S3 Bucket:
- All objects from the `ocr-site-*` bucket
- Downloads all uploaded images and files
- Flattens directory structure for local storage

## Usage:

1. **Before running `terraform destroy`**, run this backup script:
   ```bash
   python backup_data.py
   ```

2. The script will create a timestamped backup directory (e.g., `backup_20260212_003338`)

3. Check the `backup_summary.txt` file in the backup directory to verify what was backed up

4. After confirming the backup is complete, you can safely run:
   ```bash
   terraform destroy
   ```

## Backup Directory Structure:
```
backup_YYYYMMDD_HHMMSS/
├── postgresql/
│   ├── tblreferenti.csv
│   ├── tblristoranti.csv
│   └── tbluploads.csv
├── dynamodb/
│   ├── extractions.json
│   ├── visitors.json
│   ├── menu_items.json
│   └── todos.json
├── s3/
│   ├── r_1_image1.jpg
│   ├── r_2_image2.png
│   └── ...
└── backup_summary.txt
```

## Notes:
- The script handles missing DynamoDB tables gracefully (they may not exist if Terraform hasn't been applied)
- PostgreSQL connection uses the same credentials as your Lambda functions
- AWS credentials must be configured for DynamoDB access
- Backup files are saved locally in the current directory
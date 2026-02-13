# HeyAWS - OCR Web Application

This repository contains an OCR (Optical Character Recognition) web application built with AWS services using Terraform for infrastructure as code.

## Features

- Upload images and PDFs to extract text using AWS Textract
- Store OCR results in DynamoDB
- PostgreSQL database for restaurant management
- Serverless backend with AWS Lambda
- Static website hosted on S3 with CloudFront CDN
- Real-time visitor analytics
- Cost monitoring dashboard

## Quick Start

1. Clone the repository
2. Copy `terraform.tfvars.example` to `terraform.tfvars` and configure your database credentials
3. Run `terraform init`, `terraform plan`, `terraform apply`
4. Access the website via the CloudFront URL output

## Architecture

The application uses a serverless architecture with the following AWS services:
- S3 for static website hosting and file storage
- CloudFront for CDN and security (WAF)
- API Gateway for REST API
- Lambda functions for backend logic
- DynamoDB for OCR data storage
- RDS PostgreSQL for relational data
- Textract for OCR processing
- Comprehend for text analysis

## Development

### Prerequisites
- Git
- Terraform >= 1.0
- AWS CLI configured with appropriate permissions
- Python 3.11 (for local development/testing)

### Git Setup and Workflow

#### Cloning the Repository
```bash
git clone https://github.com/GioLauria/hey.git
cd hey
```

#### Branching Strategy
- `main`: Production-ready code
- Feature branches: `feature/feature-name` for new features
- Bug fixes: `fix/bug-description`

#### Commit Guidelines
- Use clear, descriptive commit messages
- All commits must be signed with GPG for verification
- Follow conventional commit format when possible

#### Setting up GPG Signing
1. Generate a GPG key using Kleopatra (Windows) or `gpg --gen-key`
2. Add your public key to GitHub: Settings → SSH and GPG keys → New GPG key
3. Configure Git to use your key:
   ```bash
   git config --global user.signingkey YOUR_KEY_ID
   git config --global commit.gpgsign true
   ```
4. Export public key and add to GitHub

#### Development Workflow
1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make changes following the maintenance rules:
   - Update `MAIN.md` for infrastructure changes
   - Update `scripts/<name>.md` for Lambda/frontend changes
   - Test changes locally
   - Run `terraform plan` and `terraform apply` if infrastructure changes

3. Commit changes:
   ```bash
   git add .
   git commit -S -m "feat: add your feature description"
   ```

4. Push and create pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

#### Maintenance Rules
- **ALWAYS update MAIN.md** after any infrastructure changes
- **ALWAYS update the corresponding `scripts/<name>.md`** file when modifying Lambda or frontend code
- Run `terraform apply` after infrastructure changes
- Ensure all commits are GPG signed
- Keep the repository synchronized with AWS infrastructure

---

# OCR Web Application — Master Prompt

Use this prompt to recreate the entire project from scratch. Everything is managed via Terraform and deployed to AWS.

**MANDATORY MAINTENANCE RULES:**
1. **ALWAYS update MAIN.md** after every change request.
2. **ALWAYS update the corresponding `scripts/<name>.md`** file whenever a script (Lambda or frontend) is modified. The `scripts/` folder must stay in sync with the actual code at all times.

---

## Prompt

Create a complete OCR web application using Terraform and AWS. Host everything in the **London region (eu-west-2)**. Always use the **cheapest service configuration** (pay-per-request DynamoDB, minimal Lambda memory, S3 static website hosting).

### Infrastructure (single `main.tf` file)

Use Terraform with AWS provider >= 5.0. All resources go in a single `main.tf` file. Use `random_id` for unique S3 bucket naming (`ocr-site-<hex>`). Output the API Gateway endpoint URL, the CloudFront distribution URL, the S3 website URL, and the RDS endpoint URL.

**Provider Configuration:**

- AWS provider with `region = "eu-west-2"`.
- Additional AWS provider aliased as `us-east-1` with `region = "us-east-1"` for CloudFront and WAF services.
- `default_tags` block with `Project = "HeyAWS"` tag applied to all resources. This tag is used by the Cost Explorer Lambda to dynamically discover which AWS services belong to this project.

**S3 Bucket:**

- S3 bucket with `force_destroy = true` for static website hosting (index.html).
- S3 website configuration with `index.html` as the index document.
- S3 CORS configuration: allow GET, PUT, POST, HEAD from all origins, expose ETag header.
- S3 lifecycle configuration: delete objects in `uploads/` prefix after 24 hours, and `r/` prefix after 24 hours to clean up uploaded images.
- Disable all public access blocks (block_public_acls, block_public_policy, ignore_public_acls, restrict_public_buckets all false).
- S3 bucket policy allowing `s3:GetObject` and `s3:PutObject` for all principals on bucket objects, plus CloudFront Origin Access Identity access.
- S3 object resources for `index.html`, `config.js`, `styles.css`, `script.js`, and `stats.html` uploaded from `site/` directory with appropriate content types and `etag = filemd5(...)` so Terraform detects content changes and re-uploads.

**CloudFront Distribution:**

- CloudFront distribution with Origin Access Identity for secure S3 access.
- Origin pointing to S3 bucket with OAI for enhanced security.
- Default cache behavior with HTTPS redirect and optimized caching settings (0-second TTL for immediate refresh).
- Web ACL (WAF) integrated directly with comprehensive security rules:
  - AWS Managed Rules Common Rule Set (general web protections)
  - AWS Managed Rules SQL Injection Rule Set (SQLi protection)
  - AWS Managed Rules Known Bad Inputs Rule Set (malicious input filtering)
  - AWS Managed Rules Bot Control Rule Set (bot traffic management)
- CloudWatch metrics enabled for monitoring WAF activity.
- Custom domain name output for the CloudFront distribution URL.

**DynamoDB Table:**

- Table named `ocr-extractions` with `PAY_PER_REQUEST` billing mode.
- Hash key `id` of type String.

**DynamoDB Table (Visitors):**

- Table named `ocr-visitors` with `PAY_PER_REQUEST` billing mode.
- Hash key `ip` of type String.
- Additional attributes: `first_visit`, `last_visit`, `visit_count`, `user_agent`, `browser`, `browser_version`, `os`, `device_type`, `accept_language`, `referer`, `country`, `country_code`, `city`, `region`, `timezone`, `isp`.

**RDS PostgreSQL Instance:**

- Instance named `hey` with PostgreSQL engine version 15.
- Instance class `db.t3.micro`, allocated storage 20 GB (gp2), publicly accessible for demo.
- Username and password configured via Terraform variables (`var.db_username`, `var.db_password`).
- Database name `hey`.
- Custom VPC with two subnets in eu-west-2a and eu-west-2b, internet gateway, and route table.
- Security group allowing inbound on port 5432 from all IPs (restrict in production).
- DB subnet group using the custom subnets.
- Output the RDS endpoint URL.

**Database Tables:**

- Table `tblReferenti`: ID (SERIAL PRIMARY KEY), Nome (VARCHAR(255) NOT NULL), Email (VARCHAR(255)), Telefono (VARCHAR(50)).
- Table `tblRistoranti`: ID (SERIAL PRIMARY KEY), Name (VARCHAR(255) NOT NULL), Address (VARCHAR(255)), City (VARCHAR(255)), Country (VARCHAR(255)), Referente_ID (INTEGER REFERENCES tblReferenti(ID)).
- Table `tblUploads`: ID (SERIAL PRIMARY KEY), Restaurant_ID (INTEGER REFERENCES tblRistoranti(ID)), S3_Path (VARCHAR(500) NOT NULL).
- Initialization script in `init_db.sql` to be run after RDS creation.

**API Gateway:**

- Single HTTP API (API Gateway v2) with CORS enabled (allow all origins, allow GET, DELETE, PUT, POST, and OPTIONS, allow all headers including Content-Type, max_age 600).
- A `$default` stage with `auto_deploy = true`.
- Twenty routes: `GET /presign`, `GET /ocr`, `GET /extractions`, `DELETE /extractions`, `PUT /extractions`, `POST /validate`, `GET /counter`, `GET /stats`, `GET /costs`, `GET /menu`, `POST /menu`, `PUT /menu`, `DELETE /menu`, `GET /todos`, `POST /todos`, `PUT /todos`, `DELETE /todos`, `POST /cache/invalidate`, `GET /cache/status`, `GET /restaurants`.
- The GET, DELETE, and PUT `/extractions` routes all point to the same list Lambda integration (it dispatches by HTTP method).
- The `POST /validate` route points to the validate Lambda integration.
- The `GET /counter` route points to the visitor counter Lambda integration.
- The `GET /costs` route points to the cost explorer Lambda integration.
- The GET, POST, PUT, DELETE `/menu` routes all point to the menu Lambda integration (it dispatches by HTTP method).
- The `GET /restaurants` route points to the restaurants Lambda integration.
- Each route has its own AWS_PROXY integration (payload_format_version 2.0) pointing to its respective Lambda.
- Lambda permissions allowing API Gateway to invoke each function.

**Lambda 1 — Presign URL (`lambda_presign.py`):**

- Python 3.11, timeout 5s, memory 128MB, handler `lambda_presign.lambda_handler`.
- IAM role with `s3:PutObject` on the bucket, `dynamodb:Scan` on the extractions table, and CloudWatch Logs permissions.
- Environment variables: `BUCKET` = the S3 bucket name, `TABLE_NAME` = DynamoDB table name.
- **CRITICAL**: The Lambda must create the S3 client with an **explicit regional endpoint**: `endpoint_url='https://s3.eu-west-2.amazonaws.com'` and `config=Config(signature_version='s3v4')`. Without this, the presigned URL uses the global S3 endpoint (`s3.amazonaws.com`) and CORS preflight OPTIONS requests fail with InternalServerError for regional buckets.
- Reads `key`, `hash`, and `restaurant` from query string parameters.
- Computes SHA256 hash of the uploaded image content client-side (in browser) and sends it as `hash` parameter.
- Scans DynamoDB extractions table for existing items with the same hash; if found, returns 409 error "Image has already been processed" to prevent duplicate uploads.
- If no duplicate found, queries the restaurant details from PostgreSQL using the `restaurant` parameter, constructs S3 key as `"r/{restaurant_id}/{key}"`, generates a presigned PUT URL (expires in 300s) with `ContentType: 'application/octet-stream'`.
- Returns JSON `{ url, s3_key }` with `Access-Control-Allow-Origin: *` header.

**Lambda 2 — OCR Textract (`lambda_ocr.py`):**

- Python 3.11, timeout 30s, memory 1024MB, handler `lambda_ocr.lambda_handler`.
- IAM role with `s3:GetObject`, `s3:DeleteObject` on bucket, `textract:DetectDocumentText` and `textract:AnalyzeDocument` on `*`, `dynamodb:PutItem`, `dynamodb:Scan` on the extractions table, and CloudWatch Logs permissions.
- Environment variables: `BUCKET` = S3 bucket name, `TABLE_NAME` = DynamoDB table name.
- Reads `s3_key` from query string parameters.
- Uses `s3_key` as the S3 object key, extracts `filename` from the last part of `s3_key`.
- Computes SHA256 hash of the uploaded file content.
- Checks DynamoDB for existing extractions with the same hash; if found, deletes the uploaded file from S3 and returns 409 error "Image has already been processed".
- **Dual OCR Processing**: Detects file type and processes accordingly:
  - **PDF files**: Uses pypdf library to extract text from all pages. Creates `all_lines` array with `{text, words, indent}` structure and `words` array with confidence set to 100.0. Sets `avg_confidence = 100.0`.
  - **Image files** (PNG, JPG, JPEG, TIFF): Calls `textract.detect_document_text()` with the S3Object. Processes LINE and WORD blocks with per-word confidence scores.
- Layout sections are separated by double newlines; lines within a section by single newlines.
- Saves the result to DynamoDB with fields: `id` (UUID4), `filename` (original filename), `text` (extracted text), `line_count` (int), `avg_confidence` (Decimal), `timestamp` (UTC ISO format), `hash` (SHA256 of file content), `words` (array of word objects).
- Returns JSON `{ text, lines, key, id, timestamp, avg_confidence, words }` with CORS header. The `lines` array has `{text, words, indent}` per line where `words` is `[{text, confidence}]`.
- If DynamoDB write fails, log the error but don't fail the request.

**Lambda 3 — List, Delete & Save Extractions (`lambda_list.py`):**

- Python 3.11, timeout 10s, memory 128MB, handler `lambda_list.lambda_handler`.
- IAM role with `dynamodb:Scan`, `dynamodb:GetItem`, `dynamodb:DeleteItem`, `dynamodb:UpdateItem` on the extractions table, `s3:GetObject` on the bucket, plus CloudWatch Logs.
- Environment variables: `TABLE_NAME` = DynamoDB table name, `BUCKET` = S3 bucket name.
- Handles three HTTP methods (detected from `event.requestContext.http.method`):
  - **GET**: Scans the DynamoDB table, filters to keep only the most recent extraction per unique filename (removes duplicates), sorts items by `timestamp` descending (newest first), limits to top 10 results, converts `line_count` from Decimal to int, converts `avg_confidence` from Decimal to float, defaults `corrected` to False if missing. For each item, checks if the S3 file exists using `head_object` and adds `file_exists` boolean. Returns JSON `{ extractions: [...] }`.
  - **DELETE**: Reads `id` from query string parameters, calls `table.delete_item(Key={'id': id})`. Returns JSON `{ deleted: id }`.
  - **PUT**: Reads JSON body `{id, text}`, calls `table.update_item()` to set `text` and `corrected = True`. Uses `ExpressionAttributeNames` for reserved word `text` (`#t`). Returns JSON `{ updated: id }`.
- All responses include `Access-Control-Allow-Origin: *` header.

**Lambda 4 — Validate Text (`lambda_validate.py`):**

- Python 3.11, timeout 15s, memory 128MB, handler `lambda_validate.lambda_handler`.
- IAM role with `comprehend:DetectDominantLanguage`, `comprehend:DetectEntities`, `comprehend:DetectKeyPhrases`, `comprehend:DetectSentiment`, `comprehend:DetectSyntax` on `*`, plus CloudWatch Logs.
- No environment variables needed.
- Reads JSON POST body `{text}`. Truncates text to 5000 chars (Comprehend sync limit).
- Calls 5 Amazon Comprehend APIs:
  1. **DetectDominantLanguage**: Returns `languages` array `[{code, score}]`.
  2. **DetectEntities**: Returns `entities` array `[{text, type, score}]` (people, places, dates, etc.).
  3. **DetectKeyPhrases**: Returns `key_phrases` array `[{text, score}]`.
  4. **DetectSentiment**: Returns `sentiment` object `{label, scores}`.
  5. **DetectSyntax**: Checks POS tagging confidence. Tokens with confidence < 70% are flagged as `low_confidence_syntax` array `[{text, tag, score}]`.
- **Quality heuristic**: Computes a `quality` object with `rating` (good/fair/poor) based on language confidence and suspicious token count:
  - `poor` if language confidence < 80% or suspicious tokens > 10
  - `fair` if language confidence < 95% or suspicious tokens > 3
  - `good` otherwise
- Returns JSON with `languages`, `entities`, `key_phrases`, `sentiment`, `low_confidence_syntax`, and `quality`.

**Lambda 5 — Enhanced Visitor Counter (`lambda_counter.py`):**

- Python 3.11, timeout 10s, memory 128MB, handler `lambda_counter.lambda_handler`.
- IAM role with `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:UpdateItem`, `dynamodb:Scan` on the visitors table, plus CloudWatch Logs.
- Environment variable: `TABLE_NAME` = visitors DynamoDB table name.
- **Enhanced Tracking**: Extracts comprehensive visitor data including IP geolocation, User-Agent parsing, and request headers.
- **Geolocation**: Uses ipapi.co API to get country, city, region, timezone, and ISP information from visitor IP.
- **User-Agent Parsing**: Extracts browser name/version, operating system, and device type from User-Agent header.
- **Device Detection**: Enhanced device type detection including Desktop, Mobile, Tablet, TV, Console, and Bot categories.
- **Data Collection**: Stores first visit, last visit, visit count, user agent, browser info, OS, device type, language preferences, referer, and geolocation data.
- **Analytics**: Tracks return visitors by incrementing visit count and updating last visit timestamp.
- Returns JSON `{ count }` with `Access-Control-Allow-Origin: *` header.

**Lambda 6 — Visitor Statistics (`lambda_stats.py`):**

- Python 3.11, timeout 10s, memory 128MB, handler `lambda_stats.lambda_handler`.
- IAM role with `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:UpdateItem`, `dynamodb:Scan` on the visitors table, plus CloudWatch Logs.
- Environment variable: `TABLE_NAME` = visitors DynamoDB table name.
- **Statistics Endpoint**: Provides detailed visitor analytics when called with `?stats=detailed` query parameter.
- **Data Analysis**: Aggregates visitor data by time periods (today, this week, this month), browsers, operating systems, countries, and device types.
- **Top Lists**: Returns top 10 most popular browsers, OS, countries, and device types.
- **Recent Visitors**: Shows last 10 visitors with their details (IP, location, browser, OS, device type).
- Returns comprehensive JSON statistics with CORS header.

**Lambda 7 — Cost Explorer (`lambda_costs.py`):**

- Python 3.11, timeout 10s, memory 128MB, handler `lambda_costs.lambda_handler`.
- IAM role with `ce:GetCostAndUsage` and `tag:GetResources` on `*`, plus CloudWatch Logs.
- Environment variables: `PROJECT_REGION` = `eu-west-2`, `PROJECT_TAG_KEY` = `Project`, `PROJECT_TAG_VALUE` = `HeyAWS`.
- Uses the Cost Explorer client in **us-east-1** (Cost Explorer API is only available in us-east-1 regardless of the region your resources are in).
- **Dynamic service discovery**: Uses the Resource Groups Tagging API (`resourcegroupstaggingapi`) to find all resources tagged with `Project = HeyAWS`. Extracts the AWS service type from each resource ARN and maps it to the Cost Explorer display name using a comprehensive `ARN_TO_CE` dictionary (covering 100+ AWS services across Compute, Storage, Database, Networking, AI/ML, Monitoring, Security, Messaging, Developer Tools, Analytics, IoT, Containers, and Migration categories).
- **Cost query**: Calls `ce.get_cost_and_usage()` with `Granularity`: DAILY (for accurate partial month sums). `Metrics`: UnblendedCost. `GroupBy`: DIMENSION by SERVICE. `Filter`: RECORD_TYPE = Usage. No region filter applied.
- `TimePeriod`: Start = first day of current month, End = tomorrow (to include today).
- Service filtering is currently commented out to show all costs.
- Sorts services by cost descending, then alphabetically for equal costs.
- Returns JSON `{ period, label, total, currency, services: [{service, amount}] }` with CORS header.

**Lambda 8 — Restaurants List (`lambda/restaurants/main.py`):**

- Python 3.9, timeout 60s, memory 128MB, handler `main.handler`.
- IAM role with CloudWatch Logs.
- VPC configuration with RDS subnets and security group for database access.
- Uses pg8000 to connect to PostgreSQL RDS instance.
- Creates tables `tblReferenti` and `tblRistoranti` if not exist.
- Inserts sample data if tables are empty.
- Queries restaurants and returns JSON array of "Name - City" strings with CORS header.

**Terraform packaging:** Each Lambda source file is zipped using `null_resource` to install pg8000 dependencies and zip the folder. The Lambda function uses `depends_on` for change detection.

### Frontend (`site/index.html`)

Single-page HTML application with embedded CSS and JavaScript. Clean, modern UI using Segoe UI font, light gray background, white card containers with rounded corners and subtle shadows. Features a logo image (hey.png) at the top and favicon.

**Upload Section (top card):**

- File input accepting `image/*` with an "Extract Text" submit button.
- **Restaurant dropdown** below the file input: dynamically loads restaurant options from the `/restaurants` API on page load. Each option shows "Name - City" from the database. Falls back to hardcoded options if API fails.
- Progress bar that advances through stages: getting URL (10%) → uploading (30%) → OCR processing (60%→80%) → done (100%). Animated blue gradient bar.
- Status text showing current operation step.
- Button disables during processing.

**Extraction History Section (second card below upload):**

- Title "Extraction History" with a "Refresh" button.
- Loads all past extractions from the `/extractions` API on page load.
- Each history item shows: filename (bold, truncated with ellipsis), a green "Corrected" badge if the text has been manually edited, timestamp + line count + avg confidence % as metadata.
- Each item has a "View" button that opens the overlay with that extraction's text. The View button carries `data-id` and `data-conf` attributes for the overlay.
- Each item has a **download icon** (📥 character, styled as a borderless button, blue). Clicking it downloads the original file directly without opening the overlay.
- Each item has a **delete icon** (✕ character, styled as a borderless button, gray turning red on hover). Clicking it shows a `confirm()` dialog, then calls `DELETE /extractions?id=<id>`. On success, the row is removed from the DOM immediately without a full reload. If the list becomes empty, the "No extractions yet" placeholder is shown.
- Shows "Loading..." while fetching, "No extractions yet" when empty.

**Visitor Counter:**

- Displayed below the history section, centered, subtle gray text with the count number in bold blue.
- On page load, calls `GET /counter` which records the visitor's IP and returns the unique visitor count.
- Shows "N unique visitors" (or "1 unique visitor" for singular).
- **Now clickable**: Clicking the visitor count navigates to `stats.html` for detailed analytics.

**Statistics Page (`stats.html`):**

- Dedicated analytics dashboard accessible by clicking the visitor counter.
- **Summary Cards**: Four cards showing Total Visitors, Today's Visitors, This Week's Visitors, and This Month's Visitors.
- **Browser Chart**: Horizontal bar chart showing top browsers by visitor count.
- **OS Chart**: Horizontal bar chart showing top operating systems by visitor count.
- **Country Chart**: Horizontal bar chart showing top countries by visitor count.
- **Recent Visitors Table**: Shows last 10 visitors with IP, location, browser, OS, and device type.
- **Navigation**: "Back to Main Page" button returns to `index.html`.
- **Data Source**: Calls `GET /stats?stats=detailed` API endpoint for comprehensive visitor analytics.

**Cache Note:**

- Interactive cache refresh controls at the bottom of the page.
- **Status Display**: Shows current cache refresh interval and next refresh time.
- **Immediate Refresh Button**: "Refresh Now" triggers CloudFront invalidation with progress feedback.
- **Interval Selector**: Dropdown with options from immediate (0 min) to 1 hour.
- Updates display when interval changes, but actual CloudFront TTL is set to 0 (no caching).

**Overlay/Modal Layer:**

- Full-screen semi-transparent dark overlay (`rgba(0,0,0,0.55)`).
- Centered white modal (max 780px wide, max 90vh tall) with rounded corners.
- Header with title (filename + date) and ✕ close button.
- Scrollable body with:
  - **Confidence meter bar** below the image — horizontal bar showing average confidence as a percentage. Color-coded: green (≥95%), yellow (≥80%), red (<80%). Only shown when `avg_confidence` is available.
  - **Three-tab interface** below the confidence bar:
    1. **Confidence View tab** (default): Renders extracted text with per-word color-coded highlighting. Each word is a `<span>` with a tooltip showing its confidence %. Colors: green background (`conf-high`, ≥95%), yellow (`conf-med`, ≥80%), red (`conf-low`, <80%). Lines are separated by `<br>`, indentation uses `&nbsp;`. Falls back to plain text when per-word data isn't available (history views).
    2. **Edit Text tab**: A `<textarea>` with the full extracted text, editable by the user. "Save Corrections" button appears in the footer when this tab is active. Saving calls `PUT /extractions` with `{id, text}` and marks the extraction as corrected in DynamoDB. Shows "Saving..."/"Saved!" feedback.
    3. **NLP Validation tab**: Displays Amazon Comprehend analysis results. Initially shows a prompt to click the validate button. After validation runs, shows:
       - **Overall Quality**: Badge (good=green, fair=yellow, poor=red) with language confidence %, entity count, key phrase count, suspicious token count.
       - **Detected Languages**: Language code tags with confidence scores.
       - **Sentiment**: Sentiment label tag (POSITIVE, NEGATIVE, NEUTRAL, MIXED).
       - **Entities Detected**: Up to 30 entity tags showing text and type (PERSON, LOCATION, DATE, etc.). "+N more" shown if truncated.
       - **Key Phrases**: Up to 20 purple phrase tags with confidence tooltips. "+N more" shown if truncated.
       - **Suspicious Tokens**: Red tags for low-confidence syntax tokens, showing text, POS tag, and confidence.
- Footer with two groups:
  - **Left**: "Copy Text" button (copies edited/displayed text to clipboard, shows "Copied!" feedback) and "Run NLP Validation" button (yellow/warn style, triggers POST to `/validate` and switches to validation tab).
  - **Right**: "Save Corrections" button (green, only shown on Edit tab) and "Close" button (gray).
- Dismissible by clicking outside the modal, the ✕ button, or the Close button.
- The overlay tracks `currentExtractionId` for save operations.

**JavaScript Flow:**

1. On form submit: disable button, show progress bar.
2. Compute SHA256 hash of the selected file using Web Crypto API.
3. Fetch presigned URL from `GET /presign?key=<filename>&hash=<sha256hash>` — this checks for duplicates before allowing upload.
4. PUT the file to the presigned S3 URL with `Content-Type: application/octet-stream`.
5. Call `GET /ocr?key=<filename>` — this triggers Textract AND saves to DynamoDB.
6. Display the extracted text in the overlay with confidence-colored words (from `ocrData.lines[].words`) and the confidence meter.
7. Auto-refresh the history list after successful extraction.
8. The API base URL is hardcoded in the JS as the API Gateway endpoint.
9. `siteBaseUrl` is derived from `window.location.origin` to construct image URLs (same S3 bucket).
10. The `showOverlay` function accepts `(text, title, imageKey, ocrData)` — `ocrData` provides `id`, `avg_confidence`, and `lines` with per-word confidence for color-coded rendering.
11. Tab switching with `switchTab(tab)` — shows/hides save button based on active tab.
12. `saveCorrection()` — sends PUT to `/extractions` with `{id, text}`, refreshes history on success.
13. `runValidation()` — sends POST to `/validate` with `{text}`, renders Comprehend results in the validation tab.
14. On page load, `GET /counter` is called to record the visit and display the unique visitor count.
15. On page load, if `window.APP_CONFIG.showCostPanel` is `true` (loaded from `config.js`), the cost dashboard panel is shown and `GET /costs` is called to fetch current month costs.

**Cost Dashboard Panel (right side, controlled by `site/config.js`):**

- **Configuration file** (`site/config.js`): Loaded via `<script src="config.js">` in the `<head>`. Sets `window.APP_CONFIG = { showCostPanel: true, apiUrl: "<api-gateway-url>" }`. Contains the dynamic API Gateway URL from Terraform outputs and cost panel toggle. The `apiUrl` is used by all frontend API calls instead of hardcoded URLs.
- **Panel UI**: Fixed-position panel on the right side of the page (`position: fixed; top: 20px; right: 20px; width: 320px`). White card with dark header, rounded corners, subtle shadow. **Mobile responsive**: On screens ≤768px, repositions to bottom of screen with page padding-bottom to prevent overlap; on screens ≤480px, spans full width with reduced padding. **Resizable**: Can be resized horizontally up to 496px maximum width.
- **Header**: Dark background (`#1e293b`) with "AWS Costs" title and current month/year. Collapsible via ▲/▼ toggle button (starts collapsed by default, showing only the toggle).
- **Period toggle**: Two buttons ("This Month" / "This Year") to switch between current month and year-to-date costs. Year view aggregates costs across all months.
- **Total section**: Shows the total cost for the selected period in USD with large bold text. Label updates dynamically ("Total This Month" / "Total This Year").
- **Services list**: Scrollable list of all AWS services (service filtering currently commented out to show all costs), sorted by cost descending then alphabetically. Each row shows service name and cost amount ($X.XX, 2 decimal places). Free tier services are hidden from the list.
- **Cost accuracy**: Queries Cost Explorer with `RECORD_TYPE=Usage` filter and DAILY granularity for accurate partial month sums, excluding credits, refunds, and discounts. No region filter applied.
- **Error handling**: Shows error message if the cost API fails.
- **Z-index**: 900 (below the overlay at higher z-index).

**Important:** The `Content-Type` header sent in the browser's PUT request to S3 MUST match the `ContentType` in the presigned URL parameters (`application/octet-stream`), otherwise S3 returns 403 Forbidden (signature mismatch).

### File Structure

```
main.tf              # All Terraform infrastructure
lambda_presign.py    # Presigned URL Lambda
lambda_ocr.py        # Textract OCR + confidence + DynamoDB save Lambda
lambda_list.py       # List/Delete/Save extractions Lambda
lambda_validate.py   # Comprehend NLP validation Lambda
lambda_counter.py    # Unique IP visitor counter Lambda
lambda_costs.py      # AWS Cost Explorer Lambda
lambda_menu.py       # Menu management Lambda with AI image generation
lambda_todo.py       # To-Do list management Lambda
lambda_cache.py      # Cache invalidation Lambda
lambda_s3_cleanup.py # S3 lifecycle cleanup Lambda
site/
  index.html         # Frontend with confidence view, edit, NLP validation, visitor counter, cost panel, menu tab, todo panel, cache controls
  stats.html         # Visitor statistics page with charts and analytics
  config.js          # Configuration file — toggle showCostPanel on/off and API URL
scripts/             # Auto-maintained documentation for every script
  lambda_presign.md  # Docs for lambda_presign.py
  lambda_ocr.md      # Docs for lambda_ocr.py
  lambda_list.md     # Docs for lambda_list.py
  lambda_validate.md # Docs for lambda_validate.py
  lambda_counter.md  # Docs for lambda_counter.py
  lambda_stats.md    # Docs for lambda_stats.py
  lambda_costs.md    # Docs for lambda_costs.py
  lambda_menu.md     # Docs for lambda_menu.py
  lambda_todo.md     # Docs for lambda_todo.py
  lambda_cache.md    # Docs for lambda_cache.py
  lambda_s3_cleanup.md # Docs for lambda_s3_cleanup.py
  index_html.md      # Docs for site/index.html
  stats_html.md      # Docs for site/stats.html
  config_js.md       # Docs for site/config.js
```

### Deployment

```bash
terraform init
terraform apply -auto-approve
```

The CloudFront distribution URL, S3 website URL, and API endpoint URL are shown as Terraform outputs. After applying, hard-refresh the browser (Ctrl+Shift+R) to see changes.

### Key Lessons (avoid these pitfalls)

1. **S3 presigned URLs MUST use the regional endpoint** (`https://s3.eu-west-2.amazonaws.com`) with `signature_version='s3v4'`. The global endpoint causes CORS preflight failures on regional buckets.
2. **Content-Type in the presigned URL params must match** the Content-Type header in the actual PUT request, or S3 rejects with 403.
3. **Terraform `aws_s3_object` needs `etag = filemd5(...)`** to detect file content changes and re-upload.
4. **DynamoDB Decimal types** must be converted to int/float before `json.dumps()` in Python.
5. **All Lambda responses** need `Access-Control-Allow-Origin: *` header for browser CORS.
6. **DynamoDB `text` is a reserved word** — use `ExpressionAttributeNames` (`#t`) in UpdateExpression when updating a `text` field.
7. **Comprehend sync API limit** is ~5000 bytes of text. Truncate before calling.
8. **CORS config must include all HTTP methods** used by the frontend (GET, DELETE, PUT, POST) or preflight requests will fail.
9. **Web Crypto API requires secure context** — CloudFront with HTTPS is needed for SHA256 hashing in the browser.
10. **WAF v2 for CloudFront must be created in us-east-1** — use a separate provider alias for WAF resources.
11. **CloudFront WAF integration** — add `web_acl_id` directly to the CloudFront distribution instead of using separate association resources.
12. **Mobile responsive design** — fixed-position panels need media queries to reposition on small screens (bottom instead of sides) and adjust sizing.

---

## Menu Management Feature

After successful OCR extraction, the application allows treating the extracted text as a restaurant menu. Users can create structured menu items from the OCR text, with AI-generated dish images using Amazon Bedrock.

### Infrastructure Additions

**DynamoDB Table (Menu Items):**

- Table named `menu-items` with `PAY_PER_REQUEST` billing mode.
- Hash key `id` of type String.
- Additional fields: `extraction_id` (String), `dish_name` (String), `description` (String), `ingredients` (List of Maps: {name: String, quantity: String}), `tts` (String, time to serve), `ptb` (Decimal, price to public), `image_key` (String, S3 key for generated image), `timestamp` (String, UTC ISO format).

**Lambda 7 — Menu Management (`lambda_menu.py`):**

- Python 3.11, timeout 30s, memory 256MB, handler `lambda_menu.lambda_handler`.
- IAM role with `bedrock:InvokeModel` on Titan Image Generator model, `s3:PutObject` on the bucket, `dynamodb:PutItem`, `dynamodb:GetItem`, `dynamodb:UpdateItem`, `dynamodb:Scan`, `dynamodb:DeleteItem` on the menu-items table, and CloudWatch Logs permissions.
- Environment variables: `BUCKET` = S3 bucket name, `TABLE_NAME` = menu-items DynamoDB table name.
- Handles HTTP methods:
  - **GET**: Scans menu items for a given `extraction_id` (query param), sorts by timestamp descending. Returns JSON `{ menu_items: [...] }`.
  - **POST**: Creates a new menu item. Body: `{extraction_id, dish_name, description, ingredients: [{name, quantity}], tts, ptb}`. Generates AI image using Bedrock Titan Image Generator with prompt like "A delicious photo of [dish_name] dish with [ingredients]". Uploads image to S3 with key `menu-images/<id>.png`, saves to DynamoDB with `image_key`. Returns JSON `{ id, image_key }`.
  - **PUT**: Updates an existing menu item by `id`. Body: same as POST. Regenerates image if dish_name or ingredients changed. Returns JSON `{ updated: id }`.
  - **DELETE**: Deletes menu item by `id` (query param). Also deletes the S3 image object. Returns JSON `{ deleted: id }`.
- For image generation: Uses `bedrock-runtime` client, model `amazon.titan-image-generator-v1`, with text prompt, generates 1 image (512x512), saves as PNG to S3.
- All responses include `Access-Control-Allow-Origin: *` header.

**API Gateway Routes:**

- Add routes: `GET /menu`, `POST /menu`, `PUT /menu`, `DELETE /menu`.
- All point to the menu Lambda integration (AWS_PROXY, payload_format_version 2.0).
- Lambda permissions for API Gateway to invoke the menu Lambda.

### Frontend Additions

**Menu Tab in Overlay:**

- Add a fourth tab "Menu" in the overlay's three-tab interface.
- **Menu Items List**: Displays existing menu items for the current extraction (fetched from `GET /menu?extraction_id=<id>`). Each item shows dish image (from S3), name, description, ingredients list, TTS, PTB. Edit and delete buttons.
- **Add New Item Button**: Opens a form to add a new menu item.
- **Form Fields**: Dish Name (text), Description (textarea), Ingredients (dynamic list: name + quantity, add/remove rows), TTS (text, e.g., "15 mins"), PTB (number, e.g., 12.50).
- **Generate Image Button**: When adding/editing, button to generate AI image based on dish name and ingredients. Shows loading, then previews the image.
- **Save Button**: Saves the item via POST/PUT to `/menu`. On success, refreshes the list and closes form.
- **Delete**: Confirm dialog, then DELETE request, removes from list.
- Ingredients displayed as bullet list, editable in form.

**File Structure Update:**

```
lambda_menu.py      # Menu management Lambda with AI image generation
scripts/
  lambda_menu.md    # Docs for lambda_menu.py
```

### Key Lessons for Menu Feature

1. **Bedrock Image Generation**: Use `amazon.titan-image-generator-v1` model, provide detailed text prompts for better results. Handle base64 image response and upload to S3.
2. **Cross-Service Permissions**: Ensure Lambda has permissions for Bedrock in the same region.
3. **Image Storage**: Store generated images in S3 under `menu-images/` prefix, use presigned URLs or direct bucket access for display.

---

## To-Do List Feature

A collapsible To-Do list panel on the right side of the page for managing tasks.

### Infrastructure Additions

**DynamoDB Table (To-Dos):**

- Table named `ocr-todos` with `PAY_PER_REQUEST` billing mode.
- Hash key `id` of type String.
- Additional fields: `text` (String), `completed` (Boolean), `timestamp` (String, UTC ISO format).

**Lambda 8 — To-Do Management (`lambda_todo.py`):**

- Python 3.11, timeout 10s, memory 128MB, handler `lambda_todo.lambda_handler`.
- IAM role with `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:UpdateItem`, `dynamodb:DeleteItem`, `dynamodb:Scan` on the todos table, and CloudWatch Logs permissions.
- Environment variable: `TABLE_NAME` = todos DynamoDB table name.
- Handles HTTP methods:
  - **GET**: Scans all todo items, sorts by timestamp descending. Returns JSON `{ todos: [...] }`.
  - **POST**: Creates a new todo item. Body: `{text, completed}`. Generates UUID for id, current timestamp. Returns JSON `{ id }`.
  - **PUT**: Updates an existing todo item. Body: `{id, completed}`. Updates the completed status. Returns JSON `{ updated: id }`.
  - **DELETE**: Deletes a todo item by `id` (query param). Returns JSON `{ deleted: id }`.
- All responses include `Access-Control-Allow-Origin: *` header.

**API Gateway Routes:**

- Add routes: `GET /todos`, `POST /todos`, `PUT /todos`, `DELETE /todos`.
- All point to the todo Lambda integration (AWS_PROXY, payload_format_version 2.0).
- Lambda permissions for API Gateway to invoke the todo Lambda.

### Frontend Additions

**To-Do Panel:**

- Fixed-position panel on the **left side** of the page (`position: fixed; top: 20px; left: 20px; width: 320px`).
- White card with dark header, rounded corners, subtle shadow. **Mobile responsive**: On screens ≤768px, repositions to bottom of screen; on screens ≤480px, spans full width. **Resizable**: Can be resized horizontally up to 496px maximum width.
- Collapsible with toggle button (starts collapsed).
- **Header**: "To-Do Lists" title with ▲/▼ toggle.
- **Add Task**: Input field and "Add" button to create new tasks.
- **Task List**: Shows all tasks with checkboxes for completion, task text, and delete (×) button.
- **Completed Tasks**: Visually distinguished with strikethrough and different styling.
- Tasks load automatically on page load and refresh after add/delete/toggle operations.

**File Structure Update:**

```
lambda_todo.py      # To-Do list management Lambda
scripts/
  lambda_todo.md    # Docs for lambda_todo.py
```

---

## Cache Management Feature

Interactive cache refresh controls with immediate invalidation and configurable refresh intervals.

### Infrastructure Additions

**Lambda 10 — Restaurants List (`lambda_restaurants.py`):**

- Python 3.11, timeout 30s, memory 128MB, handler `lambda_restaurants.lambda_handler`.
- IAM role with CloudWatch Logs permissions.
- Queries `SELECT Name, City FROM tblRistoranti` from RDS PostgreSQL.
- Returns JSON array of strings formatted as "Restaurant - City" with CORS header.

**Lambda 11 — S3 Cleanup (`lambda_s3_cleanup.py`):**

- Python 3.11, timeout 30s, memory 128MB, handler `lambda_s3_cleanup.lambda_handler`.
- IAM role with CloudWatch Logs permissions and VPC access for RDS connectivity.
- Triggered by S3 bucket notifications on `ObjectRemoved` events for objects under the `r/` prefix.
- Parses the deleted S3 object key and removes the corresponding record from PostgreSQL `tblUploads` table.
- Logs the cleanup operation for monitoring.

**API Gateway Routes:**

- Add route: `GET /restaurants`.
- Points to the restaurants Lambda integration (AWS_PROXY, payload_format_version 2.0).
- Lambda permissions for API Gateway to invoke the restaurants Lambda.

### Frontend Additions

**Cache Controls:**

- **Status Display**: Shows current cache refresh interval and next refresh time.
- **Immediate Refresh Button**: "Refresh Now" button that triggers CloudFront invalidation and shows progress/status.
- **Interval Selector**: Dropdown with options: Immediate (0 min), 1 minute, 5 minutes, 10 minutes, 15 minutes, 30 minutes, 1 hour.
- Updates the display when interval is changed, but actual CloudFront TTL remains at 5 minutes (frontend display only).

**File Structure Update:**

```
lambda_cache.py        # Cache invalidation Lambda
lambda_s3_cleanup.py   # S3 lifecycle cleanup Lambda
scripts/
  lambda_cache.md      # Docs for lambda_cache.py
  lambda_s3_cleanup.md # Docs for lambda_s3_cleanup.py
```

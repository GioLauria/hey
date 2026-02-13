# lambda_ocr.py

## Purpose
Performs **OCR (Optical Character Recognition)** on images and PDFs stored in S3. Uses AWS Textract for images and pypdf library for PDF text extraction. Computes confidence scores, preserves layout, and saves results to DynamoDB.

## Trigger
`GET /ocr?key=<filename>` via API Gateway HTTP API.

## AWS Services Used
- **Textract** — `detect_document_text` for image OCR
- **pypdf** — PDF text extraction library
- **DynamoDB** — `put_item` to persist extraction results, `scan` to check for duplicates
- **S3** — `get_object` to read files for processing and hashing, `delete_object` to remove duplicates

## Environment Variables
| Variable     | Description |
|--------------|-------------|
| `BUCKET`     | S3 bucket name containing uploaded files |
| `TABLE_NAME` | DynamoDB table name (`ocr-extractions`) |

## Input
| Parameter | Source | Required | Description |
|-----------|--------|----------|-------------|
| `s3_key`  | Query string | Yes | The full S3 key of the file to process (e.g., r/turin/turin_delcambio_1234/uuid/filename.pdf) |

## Output
```json
{
  "text": "extracted text with layout...",
  "lines": [{"text": "line text", "words": [{"text": "word", "confidence": 100.0}], "indent": 0}],
  "key": "r/turin/turin_delcambio_1234/uuid/filename.pdf",
  "id": "uuid-v4",
  "timestamp": "2026-02-13T10:21:44+00:00",
  "avg_confidence": 100.0,
  "words": [{"text": "word", "confidence": 100.0, "top": 0, "left": 0}]
}
```

## Logic Flow
1. Reads `s3_key` from query string. Returns 400 if missing.
2. Extracts `filename` as the last part of `s3_key`.
3. Retrieves the file from S3 using `s3_key` and computes SHA256 hash of its content.
4. Scans DynamoDB for existing extractions with the same hash. If found, deletes the S3 object and returns 409 "File has already been processed".
5. **File Type Detection**: Checks filename extension to determine processing method.
6. **PDF Processing** (if `.pdf`):
   - Downloads file from S3 using `get_object`
   - Uses pypdf `PdfReader` to extract text from all pages
   - Splits text into lines and words with confidence set to 100.0
   - Sets `avg_confidence = 100.0`
7. **Image Processing** (if `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`):
   - Calls `textract.detect_document_text()` pointing to the S3 object
   - Processes LINE and WORD blocks with actual confidence scores
   - Computes average confidence from word-level scores
8. **Layout reconstruction**: Creates `all_lines` array with `{text, words, indent}` structure
9. **DynamoDB save**: Writes extraction results with all metadata. Logs but doesn't fail on write errors.
10. Returns full result including `text`, `lines`, `words`, and `avg_confidence`.

## DynamoDB Item Schema
| Field            | Type    | Description |
|------------------|---------|-------------|
| `id`             | String  | UUID v4 primary key |
| `filename`       | String  | S3 object key |
| `text`           | String  | Extracted text with layout formatting |
| `line_count`     | Number  | Total lines extracted |
| `avg_confidence` | Number  | Mean word confidence (Decimal) |
| `timestamp`      | String  | UTC ISO 8601 timestamp |
| `hash`           | String  | SHA256 hash of file content |
| `words`          | List    | Array of word objects with confidence |

## IAM Permissions Required
- `s3:GetObject` on the bucket
- `textract:DetectDocumentText` on `*`
- `dynamodb:PutItem`, `dynamodb:Scan` on the extractions table
- CloudWatch Logs

## Runtime
Python 3.11 | Timeout: 30s | Memory: 1024MB
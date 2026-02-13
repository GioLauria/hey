# lambda_stats.py

## Purpose
Provides **detailed visitor analytics and statistics**. Returns total visitor counts, time-based breakdowns (today/week/month), browser/OS/country distributions, and recent visitor details. Supports both simple count and detailed statistics modes.

## Trigger
`GET /stats` via API Gateway HTTP API.

## AWS Services Used
- **DynamoDB** — `scan` (full table scan with pagination)

## Environment Variables
| Variable     | Description |
|--------------|-------------|
| `TABLE_NAME` | DynamoDB table name (`ocr-visitors`) |

## Input
Query parameter `stats=detailed` for full statistics, otherwise returns simple count.

## Output
### Simple Count Mode
```json
{ "count": 51 }
```

### Detailed Statistics Mode (`?stats=detailed`)
```json
{
  "total_visitors": 51,
  "today_visitors": 0,
  "week_visitors": 16,
  "month_visitors": 31,
  "browsers": [["Chrome", 26], ["Safari", 12], ["Edge", 7], ["Firefox", 5]],
  "operating_systems": [["Windows", 18], ["macOS", 15], ["Linux", 10], ["Android", 8]],
  "countries": [["United States", 20], ["United Kingdom", 12], ["Germany", 8], ["France", 6], ["Canada", 5]],
  "devices": [["Desktop", 35], ["Mobile", 12], ["Tablet", 3], ["TV", 1]],
  "recent_visitors": [
    {
      "ip": "192.168.1.1",
      "country": "United States",
      "city": "New York",
      "browser": "Chrome",
      "os": "Windows",
      "device_type": "Desktop"
    }
  ]
}
```

## Logic Flow
1. **Query Parameter Check**: If `stats=detailed` is present, returns detailed analytics; otherwise returns simple count.
2. **Simple Count**: Uses `table.scan(Select='COUNT')` to get total unique visitor count.
3. **Detailed Stats**: Performs full table scan with pagination to collect all visitor records.
4. **Data Analysis**: Processes visitor records to calculate:
   - Time-based counts (today/week/month based on `last_visit` timestamps)
   - Browser distribution from `browser` field
   - OS distribution from `os` field
   - Country distribution from `country` field
   - Device type distribution from `device_type` field
   - Recent visitors list (top 10 by `last_visit`, sorted descending)
5. **Data Formatting**: Converts defaultdicts to sorted arrays, handles Decimal serialization for JSON output.

## DynamoDB Item Schema (ocr-visitors table)
| Field         | Type   | Description |
|---------------|--------|-------------|
| `ip`          | String | Visitor IP address (hash key) |
| `first_visit` | String | UTC ISO 8601 timestamp of first visit |
| `last_visit`  | String | UTC ISO 8601 timestamp of most recent visit |
| `visit_count` | Number | Total number of visits from this IP |
| `browser`     | String | Browser name (Chrome, Firefox, Safari, Edge, etc.) |
| `os`          | String | Operating system (Windows, macOS, Linux, Android, iOS, etc.) |
| `country`     | String | Country name |
| `city`        | String | City name |

## Data Processing Notes
- Skips old records without timestamps
- Handles both old and new record formats
- Uses UTC datetime comparisons for time-based filtering
- Limits recent visitors to top 10 most recent
- Sorts all distributions by count (descending)
- Custom JSON encoder converts Decimal objects to integers

## IAM Permissions Required
- `dynamodb:Scan` on the visitors table
- CloudWatch Logs

## Runtime
Python 3.11 | Timeout: 10s | Memory: 128MB
# lambda_counter.py

## Purpose
Tracks **unique visitors by IP address** with comprehensive analytics data. Records detailed visitor information including geolocation, user agent parsing, and device type detection. Returns the total unique visitor count while storing rich analytics data for statistics.

## Trigger
`GET /counter` via API Gateway HTTP API.

## AWS Services Used
- **DynamoDB** — `put_item` (conditional), `update_item`, `scan` (count only)
- **External API** — ipapi.co for geolocation data

## Environment Variables
| Variable     | Description |
|--------------|-------------|
| `TABLE_NAME` | DynamoDB table name (`ocr-visitors`) |

## Input
None (all data extracted from request headers and context).

## Output
```json
{ "count": 42 }
```

## Logic Flow
1. **IP Extraction**: Gets visitor IP from `event.requestContext.http.sourceIp` or `x-forwarded-for` header.
2. **Data Collection**: Extracts comprehensive visitor data:
   - User-Agent parsing (browser, OS, device type)
   - Geolocation data from IP address
   - Language preferences, referer, timestamps
3. **Device Detection**: Enhanced device type detection including:
   - Mobile (Android, iPhone, Windows Phone, etc.)
   - Tablet (iPad, Kindle, etc.)
   - Desktop (default)
   - TV (Smart TV, Google TV, Apple TV, Roku, Fire TV)
   - Console (PlayStation, Xbox, Nintendo)
   - Bot (crawlers, spiders)
4. **Database Operation**: 
   - New visitor: `put_item` with full data
   - Return visitor: `update_item` with refreshed data
5. **Count**: Returns total unique visitor count.

## DynamoDB Item Schema (ocr-visitors table)
| Field            | Type   | Description |
|------------------|--------|-------------|
| `ip`             | String | Visitor IP address (hash key) |
| `first_visit`    | String | UTC ISO 8601 timestamp of first visit |
| `last_visit`     | String | UTC ISO 8601 timestamp of most recent visit |
| `visit_count`    | Number | Total number of visits from this IP |
| `user_agent`     | String | Raw User-Agent string |
| `browser`        | String | Parsed browser name (Chrome, Firefox, Safari, Edge, etc.) |
| `browser_version`| String | Browser version number |
| `os`             | String | Operating system (Windows, macOS, Linux, Android, iOS) |
| `device_type`    | String | Device category (Desktop, Mobile, Tablet, TV, Console, Bot) |
| `accept_language`| String | Browser language preferences |
| `referer`        | String | Referring URL |
| `country`        | String | Country name from geolocation |
| `country_code`   | String | ISO country code |
| `city`           | String | City name |
| `region`         | String | Region/state name |
| `timezone`       | String | Timezone identifier |
| `isp`            | String | Internet service provider |

## Device Type Detection Logic
- **TV**: Contains 'tv', 'smarttv', 'googletv', 'appletv', 'roku', 'firetv'
- **Tablet**: Contains 'tablet', 'ipad', 'kindle', 'playbook'
- **Mobile**: Contains 'mobile', 'android', 'iphone', 'blackberry', 'windows phone', 'opera mini'
- **Console**: Contains 'console', 'playstation', 'xbox', 'nintendo', 'wii'
- **Bot**: Contains 'bot', 'crawler', 'spider', 'scraper'
- **Desktop**: Default fallback

## Why Conditional Put?
Using `ConditionExpression='attribute_not_exists(ip)'` ensures idempotent counting:
- New IP → item is created (count goes up by 1)
- Existing IP → conditional put fails, caught by exception handler, only `last_visit` is updated
- This avoids race conditions and ensures accuracy without needing an atomic counter

## IAM Permissions Required
- `dynamodb:PutItem`, `dynamodb:UpdateItem`, `dynamodb:Scan` on the visitors table
- CloudWatch Logs

## Runtime
Python 3.11 | Timeout: 5s | Memory: 128MB

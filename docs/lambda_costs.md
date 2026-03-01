# lambda_costs.py — AWS Cost Explorer Lambda

## Purpose
Dynamically discovers which AWS services this project uses (via resource tagging), then retrieves Cost Explorer data for the current month, returning per-service costs and total. Service filtering is currently commented out to show all costs.

## Runtime
- Python 3.11, timeout 10s, memory 128MB
- Handler: `lambda_costs.lambda_handler`

## IAM Permissions
- `ce:GetCostAndUsage` on `*`
- `tag:GetResources` on `*`
- CloudWatch Logs (`logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`)

## Environment Variables
- `PROJECT_REGION` — AWS region to filter costs (default: `eu-west-2`)
- `PROJECT_TAG_KEY` — Tag key used to identify project resources (default: `Project`)
- `PROJECT_TAG_VALUE` — Tag value used to identify project resources (default: `Hey`)

## API Route
- `GET /costs`

## How It Works
1. **Service discovery** — Calls the Resource Groups Tagging API (`get_resources`) to find all AWS resources tagged with `Project = Hey`. Paginates through all results.
2. **ARN-to-CE mapping** — Extracts the service prefix from each resource ARN (e.g., `s3`, `lambda`, `dynamodb`) and maps it to the Cost Explorer display name via a comprehensive `ARN_TO_CE` dictionary covering 100+ AWS services.
3. **Cost query** — Creates a Cost Explorer client in **us-east-1** (the only region where the CE API is available). Calls `get_cost_and_usage()` with:
   - **TimePeriod**: First day of current month → tomorrow
   - **Granularity**: `DAILY` (for accurate partial month sums)
   - **Metrics**: `UnblendedCost`
   - **GroupBy**: `DIMENSION` by `SERVICE`
   - **Filter**: `RECORD_TYPE = Usage` (no region filter)
4. **Filtering** — Service filtering is currently commented out to show all services. Previously only included services discovered in the tagging step.
5. **Sorting** — Services sorted by cost descending, then alphabetically for equal costs.
6. Returns JSON response.

## Response Format
```json
{
  "period": "month",
  "label": "February 2026",
  "total": 0.00,
  "currency": "USD",
  "services": [
    { "service": "Amazon Simple Storage Service", "amount": 0.00 },
    { "service": "AWS Lambda", "amount": 0.00 }
  ]
}
```

## Error Handling
- On any exception, returns HTTP 500 with `{ "error": "<message>" }`.
- Errors are logged to CloudWatch.

## Key Notes
- Cost Explorer client must use `region_name='us-east-1'` — the API is not available in other regions.
- Cost query is filtered by `RECORD_TYPE=Usage` to show actual usage costs, excluding credits, refunds, and discounts. No region filter is applied.
- Accepts `?period=month|year` query parameter. Month (default) shows current month; year shows Jan 1 to today, aggregated across months.
- Services are discovered dynamically via Terraform `default_tags` (`Project = Hey`) — adding a new service to Terraform automatically includes it in the cost panel with no code changes.
- Implicit service mapping: when a tagged service is found, related untagged services are included (e.g. CloudWatch for Lambda, EC2-Other for EC2).
- The `ARN_TO_CE` mapping covers all major AWS service categories: Compute, Storage, Database, Networking, AI/ML, Monitoring, Security, Messaging, Developer Tools, Analytics, IoT, Containers, and Migration.
- Costs are `UnblendedCost` — the actual usage cost.
- Amounts are rounded to 2 decimal places for services; total is rounded to 4 decimal places but displayed as 2 decimals in the UI.

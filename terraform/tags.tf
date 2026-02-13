# --- Centralized Tag Management ---

locals {
  # Common tags applied to all resources
  common_tags = {
    Project     = var.project_name
    Environment = "production"
    ManagedBy   = "Terraform"
    Owner       = "Hey Team"
  }

  # Resource-specific tag functions
  vpc_tags = merge(local.common_tags, {
    Component = "network"
    Type      = "vpc"
  })

  database_tags = merge(local.common_tags, {
    Component = "database"
    Type      = "rds"
  })

  storage_tags = merge(local.common_tags, {
    Component = "storage"
    Type      = "s3"
  })

  compute_tags = merge(local.common_tags, {
    Component = "compute"
    Type      = "lambda"
  })

  api_tags = merge(local.common_tags, {
    Component = "api"
    Type      = "apigateway"
  })

  cdn_tags = merge(local.common_tags, {
    Component = "cdn"
    Type      = "cloudfront"
  })

  # DynamoDB specific tags
  dynamodb_tags = merge(local.common_tags, {
    Component = "database"
    Type      = "dynamodb"
  })
}
# --- S3 Bucket and Website ---

resource "aws_s3_bucket" "site" {
  bucket = "ocr-site-${random_id.site_id.hex}"
  force_destroy = true
  tags = merge(local.storage_tags, {
    Name = "ocr_site"
  })
}

resource "random_id" "site_id" {
  byte_length = 4
}

resource "aws_s3_bucket_website_configuration" "site" {
  bucket = aws_s3_bucket.site.id
  index_document {
    suffix = "index.html"
  }
}

resource "aws_s3_bucket_cors_configuration" "site_cors" {
  bucket = aws_s3_bucket.site.id
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 300
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "site_lifecycle" {
  bucket = aws_s3_bucket.site.id

  rule {
    id     = "delete_uploads_after_24h"
    status = "Enabled"

    filter {
      prefix = "uploads/"
    }

    expiration {
      days = 1
    }
  }

  rule {
    id     = "delete_restaurant_menus_after_24h"
    status = "Enabled"

    filter {
      prefix = "r/"
    }

    expiration {
      days = 1
    }
  }
}

resource "aws_s3_bucket_public_access_block" "site_pab" {
  bucket = aws_s3_bucket.site.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "site_public" {
  bucket = aws_s3_bucket.site.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.site.iam_arn
        },
        Action   = "s3:GetObject",
        Resource = "${aws_s3_bucket.site.arn}/*"
      }
    ]
  })
}

# --- S3 Objects (Website Files) ---

resource "aws_s3_object" "site_index" {
  bucket       = aws_s3_bucket.site.id
  key          = "index.html"
  source       = "${path.module}/../site/index.html"
  content_type = "text/html"
  etag         = filemd5("${path.module}/../site/index.html")
}

resource "aws_s3_object" "site_config" {
  bucket       = aws_s3_bucket.site.id
  key          = "config.js"
  content      = <<EOF
// Cost Dashboard Configuration
// Set showCostPanel to false (or delete this file) to disable the cost panel
window.APP_CONFIG = {
  showCostPanel: true,
  apiUrl: "${aws_apigatewayv2_api.presign_api.api_endpoint}"
};
EOF
  content_type = "application/javascript"
  etag         = md5(<<EOF
// Cost Dashboard Configuration
// Set showCostPanel to false (or delete this file) to disable the cost panel
window.APP_CONFIG = {
  showCostPanel: true,
  apiUrl: "${aws_apigatewayv2_api.presign_api.api_endpoint}"
};
EOF
  )
}

resource "aws_s3_object" "site_styles" {
  bucket       = aws_s3_bucket.site.id
  key          = "styles.css"
  source       = "${path.module}/../site/styles.css"
  content_type = "text/css"
  etag         = filemd5("${path.module}/../site/styles.css")
}

resource "aws_s3_object" "site_script" {
  bucket       = aws_s3_bucket.site.id
  key          = "script.js"
  source       = "${path.module}/../site/script.js"
  content_type = "application/javascript"
  etag         = filemd5("${path.module}/../site/script.js")
}

resource "aws_s3_object" "site_favicon" {
  bucket       = aws_s3_bucket.site.id
  key          = "favicon.ico"
  source       = "${path.module}/../site/favicon.ico"
  content_type = "image/x-icon"
  etag         = filemd5("${path.module}/../site/favicon.ico")
}

resource "aws_s3_object" "site_logo" {
  bucket       = aws_s3_bucket.site.id
  key          = "hey.png"
  source       = "${path.module}/../site/hey.png"
  content_type = "image/png"
  etag         = filemd5("${path.module}/../site/hey.png")
}

resource "aws_s3_object" "site_stats" {
  bucket       = aws_s3_bucket.site.id
  key          = "stats.html"
  source       = "${path.module}/../site/stats.html"
  content_type = "text/html"
  etag         = filemd5("${path.module}/../site/stats.html")
}

# --- Outputs ---

output "s3_website_url" {
  value = aws_s3_bucket_website_configuration.site.website_endpoint
}

output "s3_bucket_name" {
  value = aws_s3_bucket.site.bucket
}
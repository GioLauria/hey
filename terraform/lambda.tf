# --- Lambda Functions ---

# --- Presign Lambda ---

resource "aws_iam_role" "presign_lambda" {
  name = "presign-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "presign_lambda_policy" {
  name = "presign-lambda-policy"
  role = aws_iam_role.presign_lambda.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = ["s3:PutObject"],
        Resource = "${aws_s3_bucket.site.arn}/*"
      },
      {
        Effect = "Allow",
        Action = ["dynamodb:Scan"],
        Resource = aws_dynamodb_table.extractions.arn
      },
      {
        Effect = "Allow",
        Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow",
        Action = ["ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DeleteNetworkInterface"],
        Resource = "*"
      }
    ]
  })
}

data "archive_file" "presign_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/presign_package"
  output_path = "${path.module}/../lambda/presign_lambda_deploy.zip"
}

data "archive_file" "restaurants_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/package"
  output_path = "${path.module}/../lambda/restaurants_lambda_deploy.zip"
}

resource "aws_lambda_function" "presign" {
  filename         = data.archive_file.presign_lambda_zip.output_path
  function_name    = "presign-url"
  role             = aws_iam_role.presign_lambda.arn
  handler          = "lambda_presign.lambda_handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.presign_lambda_zip.output_base64sha256
  environment {
    variables = {
      BUCKET     = aws_s3_bucket.site.bucket
      TABLE_NAME = aws_dynamodb_table.extractions.name
      DB_HOST    = split(":", aws_db_instance.hey_postgres.endpoint)[0]
    }
  }
  timeout     = 10
  memory_size = 128
  vpc_config {
    subnet_ids         = [aws_subnet.rds_subnet1.id, aws_subnet.rds_subnet2.id]
    security_group_ids = [aws_security_group.rds_sg.id]
  }
}

# --- OCR Lambda ---

resource "aws_iam_role" "ocr_lambda" {
  name = "ocr-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "ocr_lambda_policy" {
  name = "ocr-lambda-policy"
  role = aws_iam_role.ocr_lambda.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
        Resource = ["${aws_s3_bucket.site.arn}/*", aws_s3_bucket.site.arn]
      },
      {
        Effect   = "Allow",
        Action   = ["textract:DetectDocumentText", "textract:AnalyzeDocument"],
        Resource = "*"
      },
      {
        Effect   = "Allow",
        Action   = ["dynamodb:PutItem", "dynamodb:Scan"],
        Resource = aws_dynamodb_table.extractions.arn
      },
      {
        Effect   = "Allow",
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow",
        Action = ["ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DeleteNetworkInterface"],
        Resource = "*"
      }
    ]
  })
}

data "archive_file" "ocr_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/ocr_package"
  output_path = "${path.module}/../lambda/lambda_ocr.zip"
}

resource "aws_lambda_function" "ocr" {
  filename         = data.archive_file.ocr_lambda_zip.output_path
  function_name    = "ocr-textract"
  role             = aws_iam_role.ocr_lambda.arn
  handler          = "lambda_ocr.lambda_handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.ocr_lambda_zip.output_base64sha256
  environment {
    variables = {
      BUCKET = aws_s3_bucket.site.bucket
      TABLE_NAME = aws_dynamodb_table.extractions.name
      DB_HOST = split(":", aws_db_instance.hey_postgres.endpoint)[0]
    }
  }
  timeout     = 120
  memory_size = 1024
}

# --- List Extractions Lambda ---

resource "aws_iam_role" "list_lambda" {
  name = "list-extractions-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "list_lambda_policy" {
  name = "list-extractions-lambda-policy"
  role = aws_iam_role.list_lambda.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["dynamodb:Scan", "dynamodb:GetItem", "dynamodb:DeleteItem", "dynamodb:UpdateItem"],
        Resource = aws_dynamodb_table.extractions.arn
      },
      {
        Effect   = "Allow",
        Action   = ["s3:GetObject"],
        Resource = "${aws_s3_bucket.site.arn}/*"
      },
      {
        Effect   = "Allow",
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

data "archive_file" "list_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/lambda_list.py"
  output_path = "${path.module}/../lambda/lambda_list.zip"
}

resource "aws_lambda_function" "list_extractions" {
  filename         = data.archive_file.list_lambda_zip.output_path
  function_name    = "list-extractions"
  role             = aws_iam_role.list_lambda.arn
  handler          = "lambda_list.lambda_handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.list_lambda_zip.output_base64sha256
  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.extractions.name
      BUCKET     = aws_s3_bucket.site.bucket
    }
  }
  timeout     = 10
  memory_size = 128
}

# --- Validate Lambda ---

resource "aws_iam_role" "validate_lambda" {
  name = "validate-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "validate_lambda_policy" {
  name = "validate-lambda-policy"
  role = aws_iam_role.validate_lambda.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "comprehend:DetectDominantLanguage",
          "comprehend:DetectEntities",
          "comprehend:DetectKeyPhrases",
          "comprehend:DetectSentiment",
          "comprehend:DetectSyntax"
        ],
        Resource = "*"
      },
      {
        Effect   = "Allow",
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

data "archive_file" "validate_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/lambda_validate.py"
  output_path = "${path.module}/../lambda/lambda_validate.zip"
}

resource "aws_lambda_function" "validate" {
  filename         = data.archive_file.validate_lambda_zip.output_path
  function_name    = "validate-text"
  role             = aws_iam_role.validate_lambda.arn
  handler          = "lambda_validate.lambda_handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.validate_lambda_zip.output_base64sha256
  timeout     = 15
  memory_size = 128
}

# --- Counter Lambda ---

resource "aws_iam_role" "counter_lambda" {
  name = "counter-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "counter_lambda_policy" {
  name = "counter-lambda-policy"
  role = aws_iam_role.counter_lambda.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Scan"],
        Resource = aws_dynamodb_table.visitors.arn
      },
      {
        Effect   = "Allow",
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

data "archive_file" "counter_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/lambda_counter.py"
  output_path = "${path.module}/../lambda/lambda_counter.zip"
}

resource "aws_lambda_function" "counter" {
  filename         = data.archive_file.counter_lambda_zip.output_path
  function_name    = "visitor-counter"
  role             = aws_iam_role.counter_lambda.arn
  handler          = "lambda_counter.lambda_handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.counter_lambda_zip.output_base64sha256
  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.visitors.name
    }
  }
  timeout     = 10
  memory_size = 128
}

# --- Stats Lambda ---

resource "aws_iam_role" "stats_lambda" {
  name = "stats-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "stats_lambda_policy" {
  name = "stats-lambda-policy"
  role = aws_iam_role.stats_lambda.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Scan"],
        Resource = aws_dynamodb_table.visitors.arn
      },
      {
        Effect   = "Allow",
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

data "archive_file" "stats_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/lambda_stats.py"
  output_path = "${path.module}/../lambda/lambda_stats.zip"
}

resource "aws_lambda_function" "stats" {
  filename         = data.archive_file.stats_lambda_zip.output_path
  function_name    = "visitor-stats"
  role             = aws_iam_role.stats_lambda.arn
  handler          = "lambda_stats.lambda_handler"
  runtime          = "python3.11"
  timeout          = 10
  memory_size      = 128
  source_code_hash = data.archive_file.stats_lambda_zip.output_base64sha256

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.visitors.name
    }
  }
}
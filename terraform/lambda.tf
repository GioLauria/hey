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

resource "aws_iam_role_policy_attachment" "presign_lambda_basic" {
  role       = aws_iam_role.presign_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "presign_lambda_s3" {
  role       = aws_iam_role.presign_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "presign_lambda_dynamodb" {
  role       = aws_iam_role.presign_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess"
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

resource "aws_iam_role_policy_attachment" "ocr_lambda_basic" {
  role       = aws_iam_role.ocr_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "ocr_lambda_s3" {
  role       = aws_iam_role.ocr_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "ocr_lambda_textract" {
  role       = aws_iam_role.ocr_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonTextractFullAccess"
}

resource "aws_iam_role_policy_attachment" "ocr_lambda_dynamodb" {
  role       = aws_iam_role.ocr_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
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
  memory_size = 128
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

resource "aws_iam_role_policy_attachment" "list_lambda_basic" {
  role       = aws_iam_role.list_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "list_lambda_dynamodb" {
  role       = aws_iam_role.list_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

resource "aws_iam_role_policy_attachment" "list_lambda_s3" {
  role       = aws_iam_role.list_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
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

resource "aws_iam_role_policy_attachment" "validate_lambda_basic" {
  role       = aws_iam_role.validate_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "validate_lambda_comprehend" {
  role       = aws_iam_role.validate_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/ComprehendFullAccess"
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

resource "aws_iam_role_policy_attachment" "counter_lambda_basic" {
  role       = aws_iam_role.counter_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "counter_lambda_dynamodb" {
  role       = aws_iam_role.counter_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
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

resource "aws_iam_role_policy_attachment" "stats_lambda_basic" {
  role       = aws_iam_role.stats_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "stats_lambda_dynamodb" {
  role       = aws_iam_role.stats_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
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
# --- DynamoDB Tables ---

resource "aws_dynamodb_table" "extractions" {
  name         = "ocr-extractions"
  billing_mode = var.dynamodb_billing_mode
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name = "ocr-extractions"
  }
}

resource "aws_dynamodb_table" "visitors" {
  name         = "ocr-visitors"
  billing_mode = var.dynamodb_billing_mode
  hash_key     = "ip"

  attribute {
    name = "ip"
    type = "S"
  }

  attribute {
    name = "visit"
    type = "S"
  }

  global_secondary_index {
    name            = "visit-index"
    hash_key        = "visit"
    projection_type = "ALL"
    write_capacity  = 0
    read_capacity   = 0
  }
}

resource "aws_dynamodb_table" "menu_items" {
  name         = "menu-items"
  billing_mode = var.dynamodb_billing_mode
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "todos" {
  name         = "ocr-todos"
  billing_mode = var.dynamodb_billing_mode
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name = "ocr-todos"
  }
}
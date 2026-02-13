# --- API Gateway ---

resource "aws_apigatewayv2_api" "presign_api" {
  name          = "presign-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_headers  = ["*", "Content-Type"]
    allow_methods  = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_origins  = ["*"]
    max_age        = 600
  }
}

# --- Integrations ---

resource "aws_apigatewayv2_integration" "presign_lambda" {
  api_id                 = aws_apigatewayv2_api.presign_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.presign.arn
  integration_method     = "GET"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "ocr_lambda" {
  api_id                 = aws_apigatewayv2_api.presign_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.ocr.arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "list_lambda" {
  api_id                 = aws_apigatewayv2_api.presign_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.list_extractions.arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "validate_lambda" {
  api_id                 = aws_apigatewayv2_api.presign_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.validate.arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "counter_lambda" {
  api_id                 = aws_apigatewayv2_api.presign_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.counter.arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "stats_lambda" {
  api_id                 = aws_apigatewayv2_api.presign_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.stats.arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

# Add more integrations as needed...

# --- Routes ---

resource "aws_apigatewayv2_route" "presign_route" {
  api_id    = aws_apigatewayv2_api.presign_api.id
  route_key = "GET /presign"
  target    = "integrations/${aws_apigatewayv2_integration.presign_lambda.id}"
}

resource "aws_apigatewayv2_route" "ocr_route" {
  api_id    = aws_apigatewayv2_api.presign_api.id
  route_key = "GET /ocr"
  target    = "integrations/${aws_apigatewayv2_integration.ocr_lambda.id}"
}

resource "aws_apigatewayv2_route" "list_route" {
  api_id    = aws_apigatewayv2_api.presign_api.id
  route_key = "GET /extractions"
  target    = "integrations/${aws_apigatewayv2_integration.list_lambda.id}"
}

resource "aws_apigatewayv2_route" "delete_route" {
  api_id    = aws_apigatewayv2_api.presign_api.id
  route_key = "DELETE /extractions"
  target    = "integrations/${aws_apigatewayv2_integration.list_lambda.id}"
}

resource "aws_apigatewayv2_route" "put_route" {
  api_id    = aws_apigatewayv2_api.presign_api.id
  route_key = "PUT /extractions"
  target    = "integrations/${aws_apigatewayv2_integration.list_lambda.id}"
}

resource "aws_apigatewayv2_route" "validate_route" {
  api_id    = aws_apigatewayv2_api.presign_api.id
  route_key = "POST /validate"
  target    = "integrations/${aws_apigatewayv2_integration.validate_lambda.id}"
}

resource "aws_apigatewayv2_route" "counter_route" {
  api_id    = aws_apigatewayv2_api.presign_api.id
  route_key = "GET /counter"
  target    = "integrations/${aws_apigatewayv2_integration.counter_lambda.id}"
}

resource "aws_apigatewayv2_route" "stats_route" {
  api_id    = aws_apigatewayv2_api.presign_api.id
  route_key = "GET /stats"
  target    = "integrations/${aws_apigatewayv2_integration.stats_lambda.id}"
}

# --- Stage ---

resource "aws_apigatewayv2_stage" "presign_stage" {
  api_id      = aws_apigatewayv2_api.presign_api.id
  name        = "$default"
  auto_deploy = true
}

# --- Lambda Permissions ---

resource "aws_lambda_permission" "apigw_presign" {
  statement_id  = "AllowAPIGatewayInvokePresign"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.presign.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.presign_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_ocr" {
  statement_id  = "AllowAPIGatewayInvokeOCR"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ocr.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.presign_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_list" {
  statement_id  = "AllowAPIGatewayInvokeList"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.list_extractions.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.presign_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_validate" {
  statement_id  = "AllowAPIGatewayInvokeValidate"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.validate.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.presign_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_counter" {
  statement_id  = "AllowAPIGatewayInvokeCounter"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.counter.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.presign_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_stats" {
  statement_id  = "AllowAPIGatewayInvokeStats"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.stats.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.presign_api.execution_arn}/*/*"
}

# --- Outputs ---

output "presign_api_url" {
  value = aws_apigatewayv2_api.presign_api.api_endpoint
}
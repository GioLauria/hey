# Terraform Variables Definition

variable "db_username" {
  description = "Username for the PostgreSQL database"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Password for the PostgreSQL database"
  type        = string
  sensitive   = true
  default     = "password123"  # Fallback for development - override in terraform.tfvars
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-2"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "Hey"
}

variable "dynamodb_billing_mode" {
  description = "Billing mode for DynamoDB tables"
  type        = string
  default     = "PAY_PER_REQUEST"
}
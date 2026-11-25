variable "aws_region" {
  type    = string
  default = "us-west-2"
}
variable "project_name" {
  type    = string
  default = "pkt-scrape"
}
variable "environment" {
  type        = string
  default     = "demo"
  description = "The deployment environment (e.g., dev, staging, prod)."
  validation {
    condition     = contains(["dev", "staging", "demo"], var.environment)
    error_message = "The environment must be one of: dev, staging, demo."
  }
}
variable "kms_key_arn" {
  description = "The ARN of the KMS key to use for DynamoDB encryption."
  type        = string
  default     = null
}
variable "name_prefix" {
  description = "A prefix for resource naming to allow for easy migrations."
  type        = string
  default     = "pkt-scrape"
}
variable "owner" {
  description = "The team or person responsible for this infrastructure."
  type        = string
  default     = "platform-team"
}
variable "cost_center" {
  description = "The cost center for budget allocation."
  type        = string
  default     = "it-operations"
}

variable "aws_region" {
  type    = string
  default = "us-west-2"
}
variable "project_name" {
  type    = string
  default = "pkt-scrape"
}
variable "kms_key_arn" {
  description = "The ARN of the KMS key to use for DynamoDB encryption."
  type        = string
  default     = null
}

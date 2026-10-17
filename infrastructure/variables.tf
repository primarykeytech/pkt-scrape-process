variable "aws_region" {
  type    = string
  default = "us-west-2"
}
variable "project_name" {
  type    = string
  default = "pkt-scrape"
}
variable "environment" {
  type = string
  default = "demo"
  validation {
    condition     = var.environment != "prod"
    error_message = "This demonstration stack must not use prod."
  }
}

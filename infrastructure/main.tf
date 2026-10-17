terraform {
  required_version = ">= 1.6"
  required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" } }
}
provider "aws" { region = var.aws_region }
resource "aws_dynamodb_table" "experiences" {
  name = "${var.project_name}-${var.environment}-experiences"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "uuid"
  attribute {
    name = "uuid"
    type = "S"
  }
  point_in_time_recovery { enabled = true }
  server_side_encryption { enabled = true }
  tags = { Project = var.project_name, Environment = var.environment, ManagedBy = "Terraform" }
}
data "aws_iam_policy_document" "writer" {
  statement {
    actions   = ["dynamodb:PutItem", "dynamodb:GetItem"]
    resources = [aws_dynamodb_table.experiences.arn]
  }
}
resource "aws_iam_policy" "writer" {
  name   = "${var.project_name}-${var.environment}-writer"
  policy = data.aws_iam_policy_document.writer.json
}

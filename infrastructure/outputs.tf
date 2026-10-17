output "table_name" {
  value = aws_dynamodb_table.experiences.name
}
output "writer_policy_arn" {
  value = aws_iam_policy.writer.arn
}

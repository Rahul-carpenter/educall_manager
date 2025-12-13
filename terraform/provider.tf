provider "aws" {
  region = var.aws_region
  # authentication via environment (AWS_PROFILE), or IAM role on CI runner
}

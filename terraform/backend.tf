terraform {
  backend "s3" {
    bucket         = "educall-terraform-state-<your-suffix>"
    key            = "global/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "educall-terraform-locks"
    encrypt        = true
  }
}

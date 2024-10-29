# s3.tf | AWS S3

resource "aws_s3_bucket" "documents_bucket" {
  bucket        = var.documents_bucket_name
  force_destroy = true
  tags = {
    Name        = "${var.documents_bucket_name}-bucket"
    Environment = "Dev"
  }
}

resource "aws_s3_bucket" "dashboard_bucket" {
  bucket        = var.dashboard_bucket_name
  force_destroy = true
  tags = {
    Name        = "${var.dashboard_bucket_name}-buckets"
    Environment = "Dev"
  }
}
# AWS Conf
variable "AWS_ACCESS_KEY_ID" {
  type    = string
  default = "AWS_ACCESS_KEY_ID"
}

variable "AWS_SECRET_ACCESS_KEY" {
  type    = string
  default = "AWS_SECRET_ACCESS_KEY"
}

variable "AWS_REGION" {
  description = "Region"
  #Update the below to your desired region
  default = "us-east-1"
}

variable "documents_bucket_name" {
  description = "Name of the Documents Bucket"
  #Update the below to a unique bucket name
  default = "urc-charo"
}

variable "dashboard_bucket_name" {
  description = "Name of the Reports Bucket"
  #Update the below to a unique bucket name
  default = "evidently-workspace"
}
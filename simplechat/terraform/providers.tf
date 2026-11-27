provider "aws" {
  region = var.aws_region

  # 想定外のアカウントへ適用しないための安全装置。
  # terraform.tfvars で自分のアカウント ID を指定すると、別アカウントの
  # 認証情報で plan / apply したときにエラーで止まる。
  allowed_account_ids = var.allowed_account_ids

  # このプロバイダーで作るすべてのリソースに付けるタグ
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = "Dev"
      ManagedBy   = "Terraform"
    }
  }
}

# 実行先（アカウント・リージョン）を確認するためのデータソース
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

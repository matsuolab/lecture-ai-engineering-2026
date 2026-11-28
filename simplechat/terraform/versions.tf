# Terraform 本体と provider（クラウドを操作するための接続部品）のバージョンを固定する。
# 実際に使うバージョンは .terraform.lock.hcl に記録され、Git で共有する。
terraform {
  required_version = ">= 1.10.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.73"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.8"
    }
  }

  # state（構成と実物の対応を記録するデータ）は、自分の AWS アカウントの
  # S3 バケットに保存する。Codespace を削除しても state は失われない。
  # バケット名などは backend.hcl に書き、次のように読み込む:
  #   terraform init -backend-config=backend.hcl
  # backend.hcl は scripts/setup-state-bucket.sh が作成する。
  # use_lockfile = true により、S3 上のロックファイルで同時実行を防ぐ。
  backend "s3" {}
}

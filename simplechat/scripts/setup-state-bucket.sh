#!/usr/bin/env bash
# ------------------------------------------------------------
# Terraform の state を保存する S3 バケットを作り、terraform/backend.hcl を作成する。
#
# 使い方（リポジトリのルートで実行）:
#   ./scripts/setup-state-bucket.sh
#
# - バケットがすでにある場合は作り直さず、設定の確認と backend.hcl の作成だけを行う。
#   新しい Codespace で作業を再開するときも、このスクリプトを実行すればよい。
# - リージョンは環境変数 AWS_REGION（未設定なら us-east-1）を使う。
# ------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="${SCRIPT_DIR}/../terraform"

REGION="${AWS_REGION:-us-east-1}"
STATE_KEY="simplechat/terraform.tfstate"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
CALLER_ARN="$(aws sts get-caller-identity --query Arn --output text)"
BUCKET="${STATE_BUCKET:-simplechat-tfstate-${ACCOUNT_ID}-${REGION}}"

# SSO でログインしたときの Arn の末尾（セッション名）には、メールアドレスが入るので表示しない
CALLER_ROLE="${CALLER_ARN}"
if [[ "${CALLER_ARN}" == *":assumed-role/"*/* ]]; then
  CALLER_ROLE="${CALLER_ARN%/*}/（セッション名は省略）"
fi

echo "AWS アカウント : ${ACCOUNT_ID}"
echo "実行ロール     : ${CALLER_ROLE}"
echo "リージョン     : ${REGION}"
echo "state バケット : ${BUCKET}"
echo

if aws s3api head-bucket --bucket "${BUCKET}" --expected-bucket-owner "${ACCOUNT_ID}" >/dev/null 2>&1; then
  echo "バケットはすでにあります。設定を確認します。"
else
  echo "バケットを作成します。"
  if [ "${REGION}" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "${BUCKET}" --region "${REGION}" >/dev/null
  else
    aws s3api create-bucket --bucket "${BUCKET}" --region "${REGION}" \
      --create-bucket-configuration "LocationConstraint=${REGION}" >/dev/null
  fi
  aws s3api wait bucket-exists --bucket "${BUCKET}" --expected-bucket-owner "${ACCOUNT_ID}"
fi

# 一般公開を禁止する
aws s3api put-public-access-block --bucket "${BUCKET}" \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# バージョニング：state を誤って壊したときに、前の版へ戻せるようにする
aws s3api put-bucket-versioning --bucket "${BUCKET}" \
  --versioning-configuration Status=Enabled

# 保存時の暗号化（SSE-S3）
aws s3api put-bucket-encryption --bucket "${BUCKET}" \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"},"BucketKeyEnabled":true}]}'

# HTTPS 以外でのアクセスを拒否する
aws s3api put-bucket-policy --bucket "${BUCKET}" --policy "$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": ["arn:aws:s3:::${BUCKET}", "arn:aws:s3:::${BUCKET}/*"],
      "Condition": {"Bool": {"aws:SecureTransport": "false"}}
    }
  ]
}
EOF
)"

aws s3api put-bucket-tagging --bucket "${BUCKET}" \
  --tagging 'TagSet=[{Key=Project,Value=simplechat},{Key=Purpose,Value=terraform-state}]'

# Terraform に渡すバックエンド設定
cat > "${TF_DIR}/backend.hcl" <<EOF
bucket       = "${BUCKET}"
key          = "${STATE_KEY}"
region       = "${REGION}"
encrypt      = true
use_lockfile = true
EOF

echo
echo "完了しました。terraform/backend.hcl を作成しました:"
cat "${TF_DIR}/backend.hcl"
echo
echo "次に、terraform ディレクトリで次のコマンドを実行してください:"
echo "  terraform init -backend-config=backend.hcl"

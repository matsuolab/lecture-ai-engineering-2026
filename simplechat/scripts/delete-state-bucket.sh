#!/usr/bin/env bash
# ------------------------------------------------------------
# Terraform の state を保存した S3 バケットを削除する（演習の最後の片付け）。
#
# 使い方（リポジトリのルートで実行）:
#   ./scripts/delete-state-bucket.sh
#
# - 先に terraform destroy を済ませておくこと。
#   state に管理中のリソースが残っている場合は、削除せずに終了する。
# - バケット内のすべての版（バージョン）を削除するため、元に戻せない。
# ------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="${SCRIPT_DIR}/../terraform"

REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="${STATE_BUCKET:-simplechat-tfstate-${ACCOUNT_ID}-${REGION}}"

echo "AWS アカウント : ${ACCOUNT_ID}"
echo "state バケット : ${BUCKET}"
echo

if ! aws s3api head-bucket --bucket "${BUCKET}" --expected-bucket-owner "${ACCOUNT_ID}" >/dev/null 2>&1; then
  echo "バケットが見つかりません。削除するものはありません。"
  exit 0
fi

# state に管理中のリソースが残っていないか確認する
if [ -z "${SKIP_STATE_CHECK:-}" ]; then
  REMAINING="$(terraform -chdir="${TF_DIR}" state list 2>/dev/null || echo "__ERROR__")"
  if [ "${REMAINING}" = "__ERROR__" ]; then
    echo "terraform state list を実行できませんでした。"
    echo "terraform ディレクトリで terraform init -backend-config=backend.hcl を実行してから、やり直してください。"
    exit 1
  fi
  if [ -n "${REMAINING}" ]; then
    echo "state にまだリソースが残っています。先に terraform destroy を実行してください:"
    echo "${REMAINING}"
    exit 1
  fi
  echo "state に管理中のリソースはありません。"
fi

read -r -p "削除するには、バケット名を入力してください: " ANSWER
if [ "${ANSWER}" != "${BUCKET}" ]; then
  echo "入力がバケット名と一致しないため、中止しました。"
  exit 1
fi

# すべての版と削除マーカーを消してから、バケットを削除する
for KIND in Versions DeleteMarkers; do
  while :; do
    COUNT="$(aws s3api list-object-versions --bucket "${BUCKET}" --max-items 500 \
      --query "length(${KIND} || \`[]\`)" --output text)"
    [ "${COUNT}" = "0" ] && break
    aws s3api delete-objects --bucket "${BUCKET}" --delete "$(aws s3api list-object-versions \
      --bucket "${BUCKET}" --max-items 500 \
      --query "{Objects: ${KIND}[].{Key: Key, VersionId: VersionId}, Quiet: \`true\`}" --output json)" >/dev/null
    echo "${KIND}: ${COUNT} 件を削除しました。"
  done
done

aws s3api delete-bucket --bucket "${BUCKET}" --region "${REGION}"
rm -f "${TF_DIR}/backend.hcl"
echo "バケット ${BUCKET} を削除しました。"

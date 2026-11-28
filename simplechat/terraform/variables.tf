variable "aws_region" {
  description = "デプロイ先の AWS リージョン"
  type        = string
  default     = "us-east-1"
}

variable "allowed_account_ids" {
  description = "適用を許可する AWS アカウント ID のリスト。null の場合は制限しない"
  type        = list(string)
  default     = null
}

variable "allowed_emails" {
  description = "ログインできるユーザーのメールアドレスのリスト。ここにないアドレスではサインアップもログインもできない"
  type        = list(string)

  validation {
    condition     = length(var.allowed_emails) > 0
    error_message = "allowed_emails に、ログインに使うメールアドレスを 1 つ以上書いてください。"
  }

  validation {
    condition     = alltrue([for e in var.allowed_emails : can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", e))])
    error_message = "allowed_emails には、メールアドレスの形（例：name@example.ac.jp）で書いてください。"
  }

  validation {
    condition     = alltrue([for e in var.allowed_emails : !endswith(lower(e), "@example.com")])
    error_message = "allowed_emails が例のまま（@example.com）です。自分のメールアドレスに書き換えてください。"
  }

  validation {
    condition     = length(distinct([for e in var.allowed_emails : lower(e)])) == length(var.allowed_emails)
    error_message = "allowed_emails に同じメールアドレスが重複しています。"
  }
}

variable "project_name" {
  description = "リソース名の接頭辞とタグに使うプロジェクト名（英小文字・数字・ハイフン）"
  type        = string
  default     = "simplechat"

  validation {
    condition     = can(regex("^[a-z0-9-]{3,20}$", var.project_name))
    error_message = "project_name は英小文字・数字・ハイフンで 3〜20 文字にしてください。"
  }
}

variable "model_id" {
  description = "Lambda から呼び出す Bedrock のモデル ID（推論プロファイル ID）"
  type        = string
  default     = "us.amazon.nova-lite-v1:0"
}

# 第 7 回の授業のための一時的な仕組み。最終課題などでは利用不可。
# 共有のロールは宿題提出期限のあとに消える。
variable "shared_bedrock_role_arn" {
  description = "このアカウントで Bedrock がまだ使えないときに Lambda が使う、共有の Bedrock のロール（空にすると使わない）"
  type        = string
  default     = "arn:aws:iam::801829805030:role/simplechat-shared-bedrock"
}

variable "lambda_timeout_seconds" {
  description = "チャット用 Lambda のタイムアウト（秒）"
  type        = number
  default     = 30
}

variable "log_retention_days" {
  description = "Lambda のログ（CloudWatch Logs）の保持日数"
  type        = number
  default     = 7
}

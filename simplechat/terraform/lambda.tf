# ------------------------------------------------------------
# アプリの処理：AWS Lambda（lambda/index.py）
# ------------------------------------------------------------
locals {
  chat_function_name = "${var.project_name}-chat"
}

# Lambda が引き受ける実行ロール
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "chat_lambda" {
  name               = "${var.project_name}-chat-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# CloudWatch Logs へログを書き込む権限（AWS 管理ポリシー）
resource "aws_iam_role_policy_attachment" "chat_lambda_basic" {
  role       = aws_iam_role.chat_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Bedrock のモデルを呼び出す権限
data "aws_iam_policy_document" "chat_lambda_bedrock" {
  statement {
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "chat_lambda_bedrock" {
  name   = "bedrock-invoke"
  role   = aws_iam_role.chat_lambda.id
  policy = data.aws_iam_policy_document.chat_lambda_bedrock.json
}

# ロググループを Terraform で管理し、保持期間を設定する。
# （Lambda 任せで自動作成させると、terraform destroy 後もログが残る）
resource "aws_cloudwatch_log_group" "chat_lambda" {
  name              = "/aws/lambda/${local.chat_function_name}"
  retention_in_days = var.log_retention_days
}

# lambda/ ディレクトリを zip にまとめる
data "archive_file" "chat_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda"
  output_path = "${path.module}/.build/chat_lambda.zip"
  excludes    = ["__pycache__"]
}

resource "aws_lambda_function" "chat" {
  function_name = local.chat_function_name
  role          = aws_iam_role.chat_lambda.arn

  runtime     = "python3.14"
  handler     = "index.lambda_handler"
  timeout     = var.lambda_timeout_seconds
  memory_size = 128

  filename         = data.archive_file.chat_lambda.output_path
  source_code_hash = data.archive_file.chat_lambda.output_base64sha256

  environment {
    variables = {
      MODEL_ID = var.model_id
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.chat_lambda_basic,
    aws_iam_role_policy.chat_lambda_bedrock,
    aws_cloudwatch_log_group.chat_lambda,
  ]
}

output "aws_account_id" {
  description = "デプロイ先の AWS アカウント ID（共有するときは必要に応じて伏せる）"
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  description = "デプロイ先のリージョン"
  value       = data.aws_region.current.region
}

output "cloudfront_url" {
  description = "アプリの公開 URL（CloudFront）"
  value       = "https://${aws_cloudfront_distribution.website.domain_name}"
}

output "api_gateway_url" {
  description = "API Gateway のステージ URL"
  value       = "${aws_api_gateway_stage.prod.invoke_url}/"
}

output "chat_api_endpoint" {
  description = "画面から呼び出すチャット API の URL"
  value       = local.chat_api_endpoint
}

output "model_id" {
  description = "Lambda が呼び出す Bedrock のモデル ID"
  value       = var.model_id
}

output "chat_lambda_function_name" {
  description = "チャット用 Lambda の関数名（ログ確認・テスト用）"
  value       = aws_lambda_function.chat.function_name
}

output "user_pool_id" {
  description = "Cognito ユーザープール ID"
  value       = aws_cognito_user_pool.chatbot.id
}

output "user_pool_client_id" {
  description = "Cognito ユーザープールクライアント ID"
  value       = aws_cognito_user_pool_client.chatbot.id
}

output "website_bucket_name" {
  description = "画面ファイルを置く S3 バケット名"
  value       = aws_s3_bucket.website.bucket
}

output "cloudfront_distribution_id" {
  description = "CloudFront ディストリビューション ID（キャッシュ削除などに使う）"
  value       = aws_cloudfront_distribution.website.id
}

# ------------------------------------------------------------
# API の入口：Amazon API Gateway（REST API）＋ Cognito 認証
#   POST /chat  → Lambda（Cognito のトークンが必要）
#   OPTIONS     → CORS のプリフライト応答（認証なし）
# ------------------------------------------------------------
locals {
  cors_allow_headers = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
  cors_allow_methods = "OPTIONS,GET,PUT,POST,DELETE,PATCH,HEAD"

  # 画面（config.js）に渡すチャット API の URL
  chat_api_endpoint = "${aws_api_gateway_stage.prod.invoke_url}/${aws_api_gateway_resource.chat.path_part}"
}

resource "aws_api_gateway_rest_api" "chatbot" {
  name        = "${var.project_name}-api"
  description = "API for Bedrock Converse chatbot"
}

resource "aws_api_gateway_resource" "chat" {
  rest_api_id = aws_api_gateway_rest_api.chatbot.id
  parent_id   = aws_api_gateway_rest_api.chatbot.root_resource_id
  path_part   = "chat"
}

# Cognito ユーザープールのトークン（Authorization ヘッダー）を検証する
resource "aws_api_gateway_authorizer" "cognito" {
  name            = "${var.project_name}-cognito-authorizer"
  rest_api_id     = aws_api_gateway_rest_api.chatbot.id
  type            = "COGNITO_USER_POOLS"
  provider_arns   = [aws_cognito_user_pool.chatbot.arn]
  identity_source = "method.request.header.Authorization"
}

# ---------- POST /chat → Lambda ----------
resource "aws_api_gateway_method" "chat_post" {
  rest_api_id   = aws_api_gateway_rest_api.chatbot.id
  resource_id   = aws_api_gateway_resource.chat.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "chat_post" {
  rest_api_id             = aws_api_gateway_rest_api.chatbot.id
  resource_id             = aws_api_gateway_resource.chat.id
  http_method             = aws_api_gateway_method.chat_post.http_method
  type                    = "AWS_PROXY" # リクエストをそのまま Lambda に渡す
  integration_http_method = "POST"
  uri                     = aws_lambda_function.chat.invoke_arn
}

# API Gateway から Lambda を呼び出す許可
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.chat.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.chatbot.execution_arn}/*/POST/chat"
}

# ---------- OPTIONS（CORS プリフライト）----------
locals {
  cors_resources = {
    root = aws_api_gateway_rest_api.chatbot.root_resource_id
    chat = aws_api_gateway_resource.chat.id
  }
}

resource "aws_api_gateway_method" "options" {
  for_each = local.cors_resources

  rest_api_id   = aws_api_gateway_rest_api.chatbot.id
  resource_id   = each.value
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options" {
  for_each = local.cors_resources

  rest_api_id = aws_api_gateway_rest_api.chatbot.id
  resource_id = each.value
  http_method = aws_api_gateway_method.options[each.key].http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{ statusCode: 200 }"
  }
}

resource "aws_api_gateway_method_response" "options" {
  for_each = local.cors_resources

  rest_api_id = aws_api_gateway_rest_api.chatbot.id
  resource_id = each.value
  http_method = aws_api_gateway_method.options[each.key].http_method
  status_code = "204"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers"     = true
    "method.response.header.Access-Control-Allow-Origin"      = true
    "method.response.header.Access-Control-Allow-Methods"     = true
    "method.response.header.Access-Control-Allow-Credentials" = true
  }
}

resource "aws_api_gateway_integration_response" "options" {
  for_each = local.cors_resources

  rest_api_id = aws_api_gateway_rest_api.chatbot.id
  resource_id = each.value
  http_method = aws_api_gateway_method.options[each.key].http_method
  status_code = aws_api_gateway_method_response.options[each.key].status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers"     = "'${local.cors_allow_headers}'"
    "method.response.header.Access-Control-Allow-Origin"      = "'*'"
    "method.response.header.Access-Control-Allow-Methods"     = "'${local.cors_allow_methods}'"
    "method.response.header.Access-Control-Allow-Credentials" = "'true'"
  }

  depends_on = [aws_api_gateway_integration.options]
}

# 認証エラー（401/403）などを API Gateway が返すときにも CORS ヘッダーを付ける。
# これがないと、ブラウザでは 401 ではなく「CORS エラー」として見えてしまう。
resource "aws_api_gateway_gateway_response" "cors" {
  for_each = toset(["DEFAULT_4XX", "DEFAULT_5XX"])

  rest_api_id   = aws_api_gateway_rest_api.chatbot.id
  response_type = each.value

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'*'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'${local.cors_allow_headers}'"
  }

  # AWS の既定と同じ本文テンプレート（省略すると毎回差分が出るため明示する）
  response_templates = {
    "application/json" = "{\"message\":$context.error.messageString}"
  }
}

# ---------- デプロイとステージ ----------
resource "aws_api_gateway_deployment" "chatbot" {
  rest_api_id = aws_api_gateway_rest_api.chatbot.id

  # API の定義が変わったときに、新しいデプロイを作り直す
  # （ここに並べた値のどれかが変わると、plan に deployment の置き換えが表示される）
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.chat.id,
      aws_api_gateway_authorizer.cognito.id,
      aws_api_gateway_authorizer.cognito.provider_arns,
      aws_api_gateway_method.chat_post.id,
      aws_api_gateway_method.chat_post.authorization,
      aws_api_gateway_integration.chat_post.id,
      aws_api_gateway_integration.chat_post.uri,
      [for m in aws_api_gateway_method.options : m.id],
      [for i in aws_api_gateway_integration.options : i.id],
      [for r in aws_api_gateway_integration_response.options : r.response_parameters],
      [for g in aws_api_gateway_gateway_response.cors : g.response_parameters],
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "prod" {
  rest_api_id   = aws_api_gateway_rest_api.chatbot.id
  deployment_id = aws_api_gateway_deployment.chatbot.id
  stage_name    = "prod"
}

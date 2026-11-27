# ------------------------------------------------------------
# 画面ファイルのアップロード
#   事前に frontend/ で `npm run build` を実行し、frontend/build を作っておく。
# ------------------------------------------------------------
locals {
  frontend_build_dir = "${path.module}/../frontend/build"
  index_html_path    = "${local.frontend_build_dir}/index.html"

  # index.html と config.js は個別に扱うため、それ以外のビルド成果物を列挙する
  frontend_files = setsubtract(fileset(local.frontend_build_dir, "**"), ["index.html", "config.js"])

  # 拡張子から Content-Type を決める
  content_types = {
    html  = "text/html"
    js    = "application/javascript"
    css   = "text/css"
    json  = "application/json"
    map   = "application/json"
    txt   = "text/plain"
    ico   = "image/x-icon"
    png   = "image/png"
    jpg   = "image/jpeg"
    jpeg  = "image/jpeg"
    gif   = "image/gif"
    svg   = "image/svg+xml"
    webp  = "image/webp"
    woff  = "font/woff"
    woff2 = "font/woff2"
  }
}

# ビルド成果物（JS・CSS など）。ファイル名にハッシュが付くので通常どおりキャッシュさせる
resource "aws_s3_object" "frontend" {
  for_each = local.frontend_files

  bucket       = aws_s3_bucket.website.id
  key          = each.value
  source       = "${local.frontend_build_dir}/${each.value}"
  etag         = filemd5("${local.frontend_build_dir}/${each.value}")
  content_type = lookup(local.content_types, lower(element(split(".", each.value), length(split(".", each.value)) - 1)), "application/octet-stream")
}

# index.html：config.js を読み込む <script> タグを差し込んでアップロードする
resource "aws_s3_object" "index_html" {
  bucket        = aws_s3_bucket.website.id
  key           = "index.html"
  content_type  = "text/html"
  cache_control = "no-cache" # 再デプロイ後すぐに新しい画面が届くようにする

  content = fileexists(local.index_html_path) ? replace(
    file(local.index_html_path),
    "</head>",
    "<script src=\"/config.js\"></script></head>",
  ) : ""

  lifecycle {
    precondition {
      condition     = fileexists(local.index_html_path)
      error_message = "frontend/build/index.html が見つかりません。先に `cd frontend && npm install && npm run build` を実行してください。"
    }
  }
}

# config.js：API の URL や Cognito の ID を画面に渡す設定ファイル
resource "aws_s3_object" "config_js" {
  bucket        = aws_s3_bucket.website.id
  key           = "config.js"
  content_type  = "application/javascript"
  cache_control = "no-cache"

  content = templatefile("${path.module}/templates/config.js.tftpl", {
    api_endpoint        = local.chat_api_endpoint
    user_pool_id        = aws_cognito_user_pool.chatbot.id
    user_pool_client_id = aws_cognito_user_pool_client.chatbot.id
    region              = data.aws_region.current.region
  })
}

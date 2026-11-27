# ------------------------------------------------------------
# 画面配信：S3（画面ファイルの保存）＋ CloudFront（CDN）
# ------------------------------------------------------------

# 画面ファイル（HTML・JS・CSS）を置く S3 バケット
resource "aws_s3_bucket" "website" {
  bucket_prefix = "${var.project_name}-web-"

  # terraform destroy 時に、中のファイルごとバケットを削除する（演習用の設定）
  force_destroy = true
}

# バケットを直接公開しない（CloudFront 経由でのみ読ませる）
resource "aws_s3_bucket_public_access_block" "website" {
  bucket = aws_s3_bucket.website.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_cors_configuration" "website" {
  bucket = aws_s3_bucket.website.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    max_age_seconds = 3000
  }
}

# CloudFront から S3 へ署名付きでアクセスするための設定（Origin Access Control）
resource "aws_cloudfront_origin_access_control" "website" {
  name                              = "${var.project_name}-oac-${data.aws_caller_identity.current.account_id}"
  description                       = "OAC for ${var.project_name} website bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# AWS が用意しているキャッシュポリシー（静的ファイル向け）
data "aws_cloudfront_cache_policy" "caching_optimized" {
  name = "Managed-CachingOptimized"
}

# AWS が用意しているセキュリティヘッダーのポリシー。
# HTTPS の強制（HSTS）、ほかのサイトの枠内への表示の禁止（X-Frame-Options）などを付ける
data "aws_cloudfront_response_headers_policy" "security_headers" {
  name = "Managed-SecurityHeadersPolicy"
}

resource "aws_cloudfront_distribution" "website" {
  comment             = "${var.project_name} frontend"
  enabled             = true
  is_ipv6_enabled     = true
  http_version        = "http2"
  default_root_object = "index.html"
  price_class         = "PriceClass_All"

  origin {
    origin_id                = "s3-website"
    domain_name              = aws_s3_bucket.website.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.website.id
  }

  default_cache_behavior {
    target_origin_id           = "s3-website"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD", "OPTIONS"]
    cached_methods             = ["GET", "HEAD", "OPTIONS"]
    compress                   = true
    cache_policy_id            = data.aws_cloudfront_cache_policy.caching_optimized.id
    response_headers_policy_id = data.aws_cloudfront_response_headers_policy.security_headers.id
  }

  # SPA（シングルページアプリ）のため、存在しないパスは index.html を返す
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

# この CloudFront ディストリビューションからの読み取りだけを許可するバケットポリシー
data "aws_iam_policy_document" "website_bucket" {
  statement {
    sid       = "AllowCloudFrontServicePrincipalReadOnly"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.website.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.website.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "website" {
  bucket = aws_s3_bucket.website.id
  policy = data.aws_iam_policy_document.website_bucket.json

  depends_on = [aws_s3_bucket_public_access_block.website]
}

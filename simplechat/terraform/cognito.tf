# ------------------------------------------------------------
# 認証：Amazon Cognito ユーザープール
# ------------------------------------------------------------
resource "aws_cognito_user_pool" "chatbot" {
  name = "${var.project_name}-user-pool"

  # メールアドレスでサインインする
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  # 利用者自身のサインアップは許可しない。
  # ユーザーは、下の aws_cognito_user で allowed_emails のアドレスだけを作る。
  admin_create_user_config {
    allow_admin_create_user_only = true

    # 招待メール（仮パスワードの期限は既定の 7 日）
    invite_message_template {
      email_subject = "simplechat: temporary password"
      email_message = "Your username is {username} and temporary password is {####}"
      sms_message   = "Your username is {username} and temporary password is {####}"
    }
  }

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = false
  }

  # メールアドレス（ユーザー名を兼ねる）を変えるときは、新しいアドレスの確認が済むまで
  # 今のアドレスを使い続ける（確認していないアドレスでログインできないようにする）
  user_attribute_update_settings {
    attributes_require_verification_before_update = ["email"]
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject        = "Verify your new account"
    email_message        = "The verification code to your new account is {####}"
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true

    string_attribute_constraints {
      min_length = 0
      max_length = 2048
    }
  }
}

# ログインできるユーザー（terraform.tfvars の allowed_emails）
# 作成すると、Cognito がそのアドレスに仮パスワードを書いた招待メールを送る。
# 初めてログインするときに、画面で新しいパスワードを決める。
# パスワードは Terraform に渡さない（渡すと state に平文で残るため）。
resource "aws_cognito_user" "allowed" {
  count = length(var.allowed_emails)

  user_pool_id             = aws_cognito_user_pool.chatbot.id
  username                 = var.allowed_emails[count.index]
  desired_delivery_mediums = ["EMAIL"]

  attributes = {
    email          = var.allowed_emails[count.index]
    email_verified = true
  }
}

resource "aws_cognito_user_pool_client" "chatbot" {
  name         = "${var.project_name}-client"
  user_pool_id = aws_cognito_user_pool.chatbot.id

  generate_secret = false # ブラウザ（SPA）から使うためシークレットなし

  # 画面（Amplify）は SRP という方式でログインする。
  # パスワードをそのまま送る方式（USER_PASSWORD_AUTH）は使わないので許可しない。
  # Cognito のログイン画面（Hosted UI）と OAuth も使わないので設定しない。
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]
  supported_identity_providers = ["COGNITO"]

  # ログインに失敗したとき、「そのユーザーがいない」とは答えない。
  # （どのメールアドレスが登録されているかを、外から調べられないようにする）
  prevent_user_existence_errors = "ENABLED"

  # email はユーザープールの必須の属性なので、書き込みの許可から外せない。
  # 変更されたときの扱いは、ユーザープールの user_attribute_update_settings で決める
  read_attributes  = ["email", "email_verified", "name", "phone_number"]
  write_attributes = ["email", "name", "phone_number"]
}

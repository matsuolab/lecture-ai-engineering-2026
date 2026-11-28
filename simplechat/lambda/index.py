# lambda/index.py
import json
import os
import boto3
import re  # 正規表現モジュールをインポート
from datetime import datetime, timedelta, timezone
from botocore.config import Config
from botocore.exceptions import ClientError


# Lambda コンテキストからリージョンを抽出する関数
def extract_region_from_arn(arn):
    # ARN 形式: arn:aws:lambda:region:account-id:function:function-name
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    if match:
        return match.group(1)
    return "us-east-1"  # デフォルト値

# グローバル変数としてクライアントを初期化（初期値）
bedrock_client = None
bedrock_region = None

# モデルID
MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")

# ------------------------------------------------------------
# 共有の Bedrock への切り替え
# 第 7 回の授業のための一時的な仕組み。最終課題などでは利用不可。
# 共有のロールは宿題提出期限のあとに消える。
#
# 自分のアカウントで Bedrock がまだ使えない（アカウントの確認中、または 1 日の
# トークン数の枠が 0）ときだけ、運営のアカウントにある共有のロールを引き受けて、
# そちらの Bedrock を呼ぶ。使えるのは Amazon Nova のモデルだけ。
# ------------------------------------------------------------
SHARED_BEDROCK_ROLE_ARN = os.environ.get("SHARED_BEDROCK_ROLE_ARN", "")
use_shared_bedrock = False   # 一度切り替えたら、この Lambda が動いている間は共有のほうを使う
shared_bedrock_client = None
shared_bedrock_expiration = None


def cannot_use_own_bedrock(error):
    # 自分のアカウントの Bedrock が使えないことを表すエラーかどうか
    if not isinstance(error, ClientError):
        return False
    code = error.response.get("Error", {}).get("Code", "")
    message = error.response.get("Error", {}).get("Message", "")
    return ((code == "AccessDeniedException" and "being verified" in message)
            or (code == "ThrottlingException" and "tokens per day" in message))


def get_shared_bedrock_client():
    # 共有のロールを引き受け、その一時的な認証情報で Bedrock のクライアントを作る。
    # 認証情報は 1 時間で切れるので、残りが 5 分を切ったら作り直す
    global shared_bedrock_client, shared_bedrock_expiration
    now = datetime.now(timezone.utc)
    if shared_bedrock_client is None or shared_bedrock_expiration - now < timedelta(minutes=5):
        sts = boto3.client('sts', region_name=bedrock_region)
        credentials = sts.assume_role(
            RoleArn=SHARED_BEDROCK_ROLE_ARN,
            RoleSessionName="simplechat-shared-bedrock"
        )["Credentials"]
        shared_bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=bedrock_region,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"]
        )
        shared_bedrock_expiration = credentials["Expiration"]
    return shared_bedrock_client


def invoke_bedrock(**kwargs):
    # まず自分のアカウントの Bedrock を呼び、使えないときだけ共有のほうに切り替える
    global use_shared_bedrock
    if not use_shared_bedrock:
        try:
            return bedrock_client.invoke_model(**kwargs)
        except ClientError as error:
            if not SHARED_BEDROCK_ROLE_ARN or not cannot_use_own_bedrock(error):
                raise
            print("This account cannot use Bedrock yet:", error.response["Error"]["Code"])
            print("Switching to the shared Bedrock role (temporary, for lecture 7):", SHARED_BEDROCK_ROLE_ARN)
            use_shared_bedrock = True
    return get_shared_bedrock_client().invoke_model(**kwargs)

# 1 回のリクエストで受け付ける量の上限（Bedrock の料金が増えすぎないようにする）
MAX_MESSAGE_CHARS = 4000     # 1 つのメッセージの文字数
MAX_HISTORY_MESSAGES = 20    # モデルに送る会話の履歴の数（古いものから捨てる）

# 画面に返す HTTP ヘッダー（CORS）
RESPONSE_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "OPTIONS,POST"
}


# リクエストの内容に誤りがあるときに使う例外（400 を返す）
class BadRequest(Exception):
    pass


def make_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": RESPONSE_HEADERS,
        "body": json.dumps(body)
    }


# リクエストボディを確かめ、メッセージと会話履歴を取り出す
def parse_request(event):
    try:
        body = json.loads(event.get('body') or '')
    except json.JSONDecodeError:
        raise BadRequest("request body must be JSON")
    if not isinstance(body, dict):
        raise BadRequest("request body must be a JSON object")

    message = body.get('message')
    if not isinstance(message, str) or not message.strip():
        raise BadRequest("message must be a non-empty string")
    if len(message) > MAX_MESSAGE_CHARS:
        raise BadRequest(f"message must be at most {MAX_MESSAGE_CHARS} characters")

    conversation_history = body.get('conversationHistory', [])
    if not isinstance(conversation_history, list):
        raise BadRequest("conversationHistory must be a list")
    for msg in conversation_history:
        if (not isinstance(msg, dict)
                or msg.get("role") not in ("user", "assistant")
                or not isinstance(msg.get("content"), str)
                or len(msg["content"]) > MAX_MESSAGE_CHARS):
            raise BadRequest("conversationHistory has an invalid message")

    # 新しいほうから MAX_HISTORY_MESSAGES 件だけ使う。
    # 会話はユーザーの発言から始める必要があるので、先頭の assistant は捨てる
    history = conversation_history[-MAX_HISTORY_MESSAGES:]
    while history and history[0]["role"] != "user":
        history = history[1:]

    return message, history


def lambda_handler(event, context):
    try:
        # コンテキストから実行リージョンを取得し、クライアントを初期化
        global bedrock_client, bedrock_region
        if bedrock_client is None:
            bedrock_region = extract_region_from_arn(context.invoked_function_arn)
            # 再試行は 1 回まで（共有の Bedrock に切り替えるまでに、長く待たせないため）
            bedrock_client = boto3.client('bedrock-runtime', region_name=bedrock_region,
                                          config=Config(retries={"mode": "standard", "max_attempts": 2}))
            print(f"Initialized Bedrock client in region: {bedrock_region}")

        # event には、ログインのトークン（Authorization ヘッダー）やメールアドレスが
        # 含まれるため、ログにはそのまま書かない

        # リクエストボディの解析
        message, conversation_history = parse_request(event)

        print("Processing message:", message)
        print("Using model:", MODEL_ID)

        # 会話履歴を使用
        messages = conversation_history.copy()

        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })

        # Nova Liteモデル用のリクエストペイロードを構築
        # 会話履歴を含める
        bedrock_messages = []
        for msg in messages:
            if msg["role"] == "user":
                bedrock_messages.append({
                    "role": "user",
                    "content": [{"text": msg["content"]}]
                })
            elif msg["role"] == "assistant":
                bedrock_messages.append({
                    "role": "assistant",
                    "content": [{"text": msg["content"]}]
                })

        # invoke_model用のリクエストペイロード
        request_payload = {
            "messages": bedrock_messages,
            "inferenceConfig": {
                "maxTokens": 512,
                "stopSequences": [],
                "temperature": 0.7,
                "topP": 0.9
            }
        }

        # ensure_ascii=False：日本語を \uXXXX ではなく、読める文字のままログに書く
        print("Calling Bedrock invoke_model API with payload:", json.dumps(request_payload, ensure_ascii=False))

        # invoke_model APIを呼び出し（自分のアカウントで使えないときは、共有の Bedrock を使う）
        response = invoke_bedrock(
            modelId=MODEL_ID,
            body=json.dumps(request_payload),
            contentType="application/json"
        )

        # レスポンスを解析
        response_body = json.loads(response['body'].read())
        print("Bedrock response:", json.dumps(response_body, default=str, ensure_ascii=False))

        # 応答の検証
        if not response_body.get('output') or not response_body['output'].get('message') or not response_body['output']['message'].get('content'):
            raise Exception("No response content from the model")

        # アシスタントの応答を取得
        assistant_response = response_body['output']['message']['content'][0]['text']

        # アシスタントの応答を会話履歴に追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })

        # 成功レスポンスの返却
        return make_response(200, {
            "success": True,
            "response": assistant_response,
            "conversationHistory": messages
        })

    except BadRequest as error:
        print("Bad request:", str(error))
        return make_response(400, {
            "success": False,
            "error": str(error)
        })

    except Exception as error:
        # 詳しい内容はログにだけ書く（ロールの ARN などを画面に返さない）
        print("Error:", str(error))
        return make_response(500, {
            "success": False,
            "error": "Internal server error"
        })

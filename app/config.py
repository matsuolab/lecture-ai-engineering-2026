"""講座全体で共通の設定。

APIキーやモデル名はコードに書かず、環境変数から読み込む。
"""

import os

# 既定モデル。環境変数 AIE_MODEL を設定すると切り替えられる。
#   例: export AIE_MODEL=gpt-4o-mini
DEFAULT_MODEL = "gpt-4o-mini"
MODEL = os.getenv("AIE_MODEL", DEFAULT_MODEL)


def api_error_message(status: int, detail: str = "") -> str:
    """HTTPステータスコードを、受講生向けの日本語の説明にする（ask.py と agent.py で共用）。"""
    if status == 429:
        return "レート制限に達しました。1分ほど待ってから再実行してください。"
    if status == 503:
        return "モデルが混み合っています（503）。少し待ってから再実行してください。"
    if status in (400, 401, 403, 404):
        return f"APIキーかモデル名に問題があります（{status}）: {detail}"
    return f"APIエラー（{status}）: {detail}"


def get_api_key() -> str:
    """環境変数 OPENAI_API_KEY を返す。未設定なら手順を表示して終了する。"""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise SystemExit(
            "環境変数 OPENAI_API_KEY が見つかりません。\n"
            "1. OpenAI Platform で API キーを作成し、GitHub の Settings → Codespaces → Secrets に\n"
            "   OPENAI_API_KEY として登録して、\n"
            "   使う repository に自分の fork を選んでください。\n"
            "2. Codespaces を起動したあとに登録した場合は、Codespaces を再起動してください。\n"
            "   （左下の「Codespaces」→「Stop Current Codespace」→ 再度開く）"
        )
    return key

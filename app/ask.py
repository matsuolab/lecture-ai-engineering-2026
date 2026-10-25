

import os
import sys
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


from google import genai
from google.genai import types


def main():
    # コマンドライン引数から質問を取得
    if len(sys.argv) < 2:
        print("Usage: uv run python -m app.ask '<question>'")
        sys.exit(1)
    
    prompt = sys.argv[1]
    
    # モデル名の取得（環境変数 AIE_MODEL があればそれを使用、なければデフォルト）
    model_name = os.environ.get("AIE_MODEL", "gemini-2.5-flash") # または指定のモデル
    
    # GenAI クライアントの初期化
    client = genai.Client()

    # 【実装レベルのポイント】
    # チャットセッションを作成し、履歴を保持できるようにする
    # ※ 必要に応じて system_instruction や config もここで渡します
    chat = client.chats.create(model=model_name)

    # 質問を送信してレスポンスを取得
    response = chat.send_message(prompt)

    # 結果の出力（トークン数などもここで表示できるようにすると発展レベルや確認に便利です）
    print(response.text)
    
    # もしトークン数を表示させる要件（手順 6）がある場合は以下のようにメタデータも確認できます
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        print(f"\n[Token Usage] Input: {response.usage_metadata.prompt_token_count}, Output: {response.usage_metadata.candidates_token_count}")

if __name__ == "__main__":
    main()
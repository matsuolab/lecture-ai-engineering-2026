"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import sys
import time  # 1. タイムモジュールのインポートを確認
from app.config import get_api_key, MODEL
from google import genai
from google.genai import errors

DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"

def chat(first_question: str) -> None:
    client = genai.Client(api_key=get_api_key())
    session = client.chats.create(model=MODEL)
    
    question = first_question
    while question:
        print(f"[質問] {question}\n")
        
        # 2. リクエスト送信前の時刻を記録
        start_time = time.time()
        
        # 履歴を含めてモデルに送信
        response = session.send_message(question)
        
        # 3. レスポンス受信後の時刻を記録し、経過時間を計算
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        
        print(response.text)
        
        # 4. トークン数とレスポンス時間を一緒に出力する
        if response.usage_metadata:
            usage = response.usage_metadata
            print(f"\n[tokens] 入力: {usage.prompt_token_count} / 出力: {usage.candidates_token_count}  |  [レスポンス時間: {minutes}分{seconds:02d}秒]")
        
        question = input("\n[続けて質問（空行で終了）]: ").strip()

def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する（チャット履歴対応）")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    
    try:
        args = parser.parse_args()
        print(f"[model] {MODEL}")
        chat(args.question)
        
    except errors.APIError as e:
        print(f"\n[API Error] {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
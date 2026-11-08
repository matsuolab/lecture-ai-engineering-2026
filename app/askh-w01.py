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

from google import genai
from google.genai import errors
import time


# モジュール変数として会話履歴（辞書のリスト）を保持
_history = []

from app.config import MODEL, api_error_message, get_api_key

# グローバルでクライアントとチャットセッションを保持
_client = None
_chat_session = None


def get_chat():
  global _client, _chat_session
  if _chat_session is None:
    _client = genai.Client(api_key=get_api_key())
    _chat_session = _client.chats.create(model=MODEL)
  return _chat_session


def ask(question: str) -> str:
  chat = get_chat()

  # 1. 応答時間の計測開始
  start_time = time.perf_counter()

  # メッセージの送信（チャットセッションが自動で履歴を管理します）
  response = chat.send_message(question)

  # 2. 応答時間の計測終了
  end_time = time.perf_counter()
  elapsed_time = end_time - start_time

  # 3. 応答時間とトークン数の表示
  info_parts = [f"応答時間: {elapsed_time:.2f}秒"]

  if response.usage_metadata:
    prompt_tokens = response.usage_metadata.prompt_token_count
    output_tokens = response.usage_metadata.candidates_token_count
    info_parts.append(
        f"入力: {prompt_tokens} tokens / 出力: {output_tokens} tokens"
    )

  print(f"[{' | '.join(info_parts)}]")

  return response.text


def main():
  print(f"[model] {MODEL}")
  print("=== Gemini チャットを開始します ===")
  print("（終了するには 'exit' または 'quit' と入力してください）\n")

  while True:
    try:
      # ユーザーからの入力を受け付ける
      question = input("[質問]: ")

      # 終了コマンドの判定
      if question.strip().lower() in ["exit", "quit", "終了"]:
        print("チャットを終了します。お疲れ様でした！")
        break

      # 空入力の場合はスキップ
      if not question.strip():
        continue

      # 質問を投げて回答を表示
      answer = ask(question)
      print(f"\n[AI]: {answer}\n" + "-" * 40)

    except errors.ApiError as e:
      print(f"APIエラーが発生しました: {e}")
      print(api_error_message(e.code, e.message))

    except (KeyboardInterrupt, EOFError):
      print("\nチャットを終了します。")
      break


if __name__ == "__main__":
  main()
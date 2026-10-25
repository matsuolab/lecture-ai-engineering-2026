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
import time

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

client = genai.Client(api_key=get_api_key())
sessions: dict[str, any] = {} # セッション名 → Chat オブジェクト

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str, chat=None) -> str:
    if chat is not None:
        target_chat = chat
    else:
        target_chat = get_or_create_session("default")
   
    
    start_time = time.perf_counter()
    response = target_chat.send_message(question)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    # TODO(第1回 演習): response.usage_metadata から
    #   入力トークン数と出力トークン数を表示してみよう（Copilotに頼んでよい
    
    if response.usage_metadata:
        in_tokens = response.usage_metadata.prompt_token_count
        out_tokens = response.usage_metadata.candidates_token_count
        print(f"[tokens] 入力: {in_tokens}, 出力: {out_tokens}")
        print(f"[time] 応答時間: {elapsed_ms:.2f} ms")  #   応答時間も表示

    return response.text
#セッションを切り替え・新規作成する



def get_or_create_session(session_id: str="default"):
    """新しいセッションを作る。session_idがなければ新しいChatオブジェクトを作理、sessionsに保存する。"""
    if session_id not in sessions:
        sessions[session_id] = client.chats.create(model=MODEL)
    return sessions[session_id]

def ask_with_sessions(question: str, session_id: str = "default") -> str:
    """セッションを切り替えて質問する。session_idが存在しない場合は新規作成する。"""
    user_chat = get_or_create_session(session_id)
    return  ask(question, chat=user_chat)

def list_sessions() -> list[str]:
    """現在保持されているセッションIDの一覧を返す。"""
    return list(sessions.keys())


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[質問] {args.question}\n")
    try:
        print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()

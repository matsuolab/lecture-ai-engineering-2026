"""「実装」にチャレンジ

第1回（改）: 素のLLMに会話履歴を保ったまま複数回質問するスクリプト。

使い方:
    uv run python -m app.ask で、質問を入力してEnterを押すと、回答が返ってくる。
    exitと入力してEnterを押すと終了する。

用語集などのツールは使用しないため、講座に固有のことを聞くと、「分からない」と答えるか、
一般論でもっともらしく答える（講座の実際とは違う）てしまうことがある。
    
（第3回で、用語集を検索できるエージェントにして改善する）
"""

from google import genai
from google.genai import errors
from app.config import MODEL, api_error_message, get_api_key

def ask(chat, question: str) -> str:

    response = chat.send_message(question) # 質問を送信して回答を受け取る

    usage = response.usage_metadata # トークン使用量の情報を取得
    input_tokens = usage.prompt_token_count if usage else "不明"
    output_tokens = usage.candidates_token_count if usage else "不明"
    print(f"[tokens] 入力: {input_tokens}, 出力: {output_tokens}")

    return response.text


def main() -> None:
    
    client = genai.Client(api_key=get_api_key()) # Geminiのクライアントを作る
    chat = client.chats.create(model=MODEL)      # チャットセッションを作る

    while True: 
        question = input("質問を入力してください（終了するには exit）> ")
        # 終了条件
        if question.strip().lower() == "exit":
            break
        if not question.strip():
            continue
        
        print(f"[model] {MODEL}")      # 使用するモデルを表示
        print(f"[質問] {question}\n")  # 質問を表示

        try: 
            ans = ask(chat, question) # 質問を送信して回答を受け取る
            print(f"[回答] {ans}\n")
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))
            raise SystemExit(1)

if __name__ == "__main__":
    main()

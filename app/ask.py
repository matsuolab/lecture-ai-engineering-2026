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
from google.genai import types
from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"

FREE_TIER_RPM = 15         # 1分あたりの最大リクエスト（質問）回数
FREE_TIER_TPM = 1_000_000  # 1分あたりの最大トークン数（100万）
FREE_TIER_RPD = 1_500      # 1日あたりの最大リクエスト（質問）回数


#def ask(question: str) -> str:
def ask(question: str) -> None:
    client = genai.Client(
        api_key=get_api_key(),
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=1)
        ),
        )
    #response = client.models.generate_content(model=MODEL, contents=question)

    # TODO(第1回 演習): response.usage_metadata から
    # 入力トークン数と出力トークン数を表示してみよう（Copilotに頼んでよい）

    # 会話履歴を自動で記憶してくれるチャットセッションを作成する
    chat = client.chats.create(model=MODEL)

    # 最初の質問をセットする
    current_question = question
    turn = 1
    cumulative_tokens = 0

    while True:
        print(f"\n--- [ {turn}回目の質問 ] ---")
        print(f"[質問] {current_question}\n")

        # ストップウォッチ開始（応答時間の計測スタート）
        start_time = time.perf_counter()

        # チャットセッションにメッセージを送る（過去の会話履歴も自動で一緒に送られる）
        response = chat.send_message(current_question)

        # ストップウォッチ停止（かかった秒数を計算）
        elapsed_time = time.perf_counter() - start_time

        # AIの返答を表示
        print(f"[回答]\n{response.text}\n")

        # response.usage_metadata からトークン数を取得して表示
        usage = response.usage_metadata
        if usage:
            prompt_tokens = usage.prompt_token_count        # 入力トークン数（履歴＋今回の質問）
            output_tokens = usage.candidates_token_count    # 出力トークン数（今回のAIの返答）
            total_tokens = usage.total_token_count          # 合計トークン数
            cumulative_tokens += total_tokens               # これまでの合計トークン数に、今回使ったトークン数を足す
            tpm_ratio = (cumulative_tokens / FREE_TIER_TPM) * 100 # 1分間のトークン上限(100万)の何％を使ったか計算する
            
            print(
                f"[計測] 応答時間: {elapsed_time:.2f}秒 | "
                f"トークン数 -> 入力: {prompt_tokens}, 出力: {output_tokens}, 合計: {total_tokens} | "
                f"1分間のトークン使用率: {tpm_ratio:.2f}%"
                f"[無料枠の制限目安] "
                f"回数: {turn}/{FREE_TIER_RPM}回(分)・{turn}/{FREE_TIER_RPD:,}回(日) | "
                f"累計トークン: {cumulative_tokens:,}/{FREE_TIER_TPM:,} ({tpm_ratio:.3f}%)"
                )
        else:
            print(f"[計測] 応答時間: {elapsed_time:.2f}秒 | トークン情報なし")
            print(f"[無料枠の制限目安] 回数: {turn}/{FREE_TIER_RPM}回(分)・{turn}/{FREE_TIER_RPD:,}回(日)")

    #return response.text
    # 次の質問をキーボードから受け取る（履歴を持ったまま会話を続けるための追加処理）
        next_input = input("\n続けて質問を入力してください（終了するには Enter のみ、または q を入力）: ").strip()

    # 何も入力されなかったか、「q」「exit」と入力されたらループを抜けて終了する
        if not next_input or next_input.lower() in ("q", "exit"):
            print("会話を終了します。")
            break

        # 入力された文字を「次の質問」にセットして、回数を1増やす
        current_question = next_input
        turn += 1


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    #print(f"[model] {MODEL}")
    #print(f"[質問] {args.question}\n")
    #try:
    #    print(ask(args.question))
    try:
        ask(args.question)
    except errors.APIError as e:
        print(api_error_message(e.code, e.message or ""))
        #print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
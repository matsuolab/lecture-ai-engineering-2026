"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""
#2026/10/25 演習・宿題のため編集

import argparse

#timeモジュールをインポート
import time  


from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

#typesモジュールをインポート
from google.genai import types 

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    temperature_value = 0.8
    
    #開始時刻を記録
    start = time.perf_counter() 
    
    response = client.models.generate_content(
        model=MODEL, 
        contents=question,
        #temperature設定
        config=types.GenerateContentConfig(temperature=temperature_value),
    )
    #temperatureを表示
    print(f"[temperature]: {temperature_value}")

    #応答時間（終了時刻 - 開始時刻）を計算
    elapsed = time.perf_counter() - start  

    #応答時間を表示
    print(f"[応答時間] {elapsed:.3f}秒")    

    # TODO(第1回 演習): response.usage_metadata から
    #   入力トークン数と出力トークン数を表示してみよう（Copilotに頼んでよい）

    #使用量を取得
    usage = getattr(response, "usage_metadata", None)
    
    #使用量情報を表示
    if usage is not None:
        print(f"[usage] 入力トークン数: {usage.prompt_token_count}")
        print(f"[usage] 出力トークン数: {usage.candidates_token_count}")
        print(f"[usage] 合計トークン数: {usage.total_token_count}")
    else:
        print("使用量情報を取得できませんでした")

    return response.text


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

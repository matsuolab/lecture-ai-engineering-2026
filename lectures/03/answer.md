# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：glossaryなどをツールとして参照して、関係する講義の回を含めて回答してくれる。
- `--trace` で見えたツール呼び出し（ツール名と引数）：search_glossary({'query': 'LoRA'})、search_glossary({'query': 'QLoRA'})
- 1つの質問での LLM 呼び出し回数（`requests`）：2
- 追加したツールと、docstring に書いた説明：
def make_quiz(lecture: int) -> str:
    """指定した回の用語から1つを選び、確認問題と答えを返す。

    「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
    """
## 宿題

- 取り組んだレベル：実装
- やったこと：Copilotに
'tool.py'に次の関数を付け加えてもらいました。
def save_learning_log(content: str) -> str:
    """学習内容を learning_log/ に保存する。

    学習記録を残したいと頼まれたときに使う。ファイルへの保存は利用者の承認後に行う。
    """
    LEARNING_LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    path = LEARNING_LOG_DIR / f"{timestamp}.md"
    path.write_text(content, encoding="utf-8")
    return f"学習記録を learning_log/{path.name} に保存しました。"
また、'agent.py'では、次が変更になっています。
agent = Agent(instructions=INSTRUCTIONS, output_type=[str, DeferredToolRequests])
agent.tool_plain(tools.save_learning_log, requires_approval=True)
def main() -> None:
- 結果：
uv run python -m app.agent "今日学んだことを学習記録として保存してください。内容: Pydantic AIのツールは、関数のdocstringと型ヒントを使ってモデルに公開できる。"
と質問すると、次にようにコンソールに表示されました。

[model] gemini-3.5-flash-lite
学習記録を `learning_log/` に保存いたします。以下の内容でよろしいでしょうか？

> Pydantic AIのツールは、関数のdocstringと型ヒントを使ってモデルに公開できる。

ご確認のほどよろしくお願いいたします。（第3回）

- 気づき・疑問：承認することをコマンドラインで求めるわけでもなさそうで、これが本当にやりたいことかいまいち疑問です。

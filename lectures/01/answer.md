# 第1回 解答

## 演習

- 講座に固有の質問（宿題の3レベル）へのモデルの回答（要約でよい）：
- 用語集の正しい意味と比べて気づいたこと：
- 表示できたトークン数（入力 / 出力）：

## 宿題

- 取り組んだレベル：基礎 
- やったこと：次の3モデルで実行
uv run python -m app.ash "LoRAとは何ですか?" 
AIE_MODEL==gemini-3.8-flash uv run python -m app.ash "LoRAとは何ですか?" 
AIE_MODEL==gemini-3.5-flash uv run python -m app.ash "LoRAとは何ですか?" 
- 結果：出力トークン数
gemini-3.5-flash-lite  723
gemini-3.8-flash       737
gemini-3.5-flash       588
- 気づき：
gemini-3.8-flash は背景から記述され詳しい
gemini-3.5-flash は簡潔に纏められいる
gemini-3.5-flash-lite は詳細な記述になっている
-疑問：liteとあるのに記述が詳細となっているのは何故か？
-疑問：ask.pyのソースでデフォルトのモデルの設定が無いのは何故か

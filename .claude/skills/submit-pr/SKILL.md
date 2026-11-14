---
name: submit-pr
description: 講座の各回の演習・宿題が終わったあと、作業ブランチ lecNN を push して、自分の fork の main 向けの PR を作成（すでにあれば更新）する。「提出して」「PR を出して」「第N回を提出」と言われたとき、または /submit-pr で使う。
argument-hint: "[回の番号（省略時は現在のブランチから判定）]"
---

# 各回の提出（lecNN → 自分の fork の main へ PR）

提出の流れは毎回同じなので、次の順に進める。途中で「止める」と書いた条件に当たったら、
それ以上進めずに状況を報告する。PR のマージはしない（提出は PR を出すところまで）。

## 1. 回とブランチを決める

- 引数で回の番号が渡されたらそれを使う。無ければ `git branch --show-current` から判定する
- ブランチ名は `lecNN`（2 桁。例: `lec04`）。現在のブランチが `lecNN` の形でない、
  または引数の回と違う場合は、勝手に切り替えずに止めて確認する
- 以降、NN は 2 桁の回の番号（`04`）、N は表示用の番号（`4`）を指す

## 2. 提出物を確認する

- `lectures/NN/answer.md` を読む。「演習」欄がテンプレートのまま（項目が空）なら止める。
  「宿題」欄が空の場合は、演習だけの提出でよいかを確認する
- `git status --short` で未コミットの変更を見る。あれば内容を示したうえでコミットする。
  メッセージは CLAUDE.md の規則どおり（例: `第4回演習`、`第4回の宿題の基礎`）
- `git diff main...HEAD` を見て、API キーらしい文字列（`AIza` で始まる値、`GEMINI_API_KEY=` の実値など）や
  `.env`、`learning_log/` が含まれていたら止める。push すると履歴に残り、キーの作り直しが必要になるため

## 3. テストを通す

```bash
uv run pytest -q
```

失敗したら止めて、失敗内容を報告する（提出前に直すかどうかはユーザーが決める）。
このテストは API キー不要で LLM を呼ばないので、レート制限は気にしなくてよい。

## 4. push する

```bash
git push -u origin lecNN
```

## 5. PR を作る

提出先は **自分の fork**。fork の `owner/repo` は `git remote get-url origin` から取り出す。

`gh pr create` は fork の中で実行すると、既定で fork 元（講座 repo の matsuolab）を
提出先に選ぶ。講座 repo に PR を出してしまわないよう、`--repo` は必ず明示する。

```bash
# すでに PR があるか（あれば 4. の push で反映済みなので、新しく作らない）
gh pr list --repo OWNER/REPO --head lecNN --state open --json number,url

# 無ければ作成
gh pr create --repo OWNER/REPO --base main --head lecNN \
  --title "第N回 演習・宿題" --body-file 本文を書いたファイル
```

- 既存の PR があるときは、本文が今の内容と合わなくなっていれば
  `gh pr edit 番号 --repo OWNER/REPO --body-file ...` で更新する
- 本文の一時ファイルはリポジトリの外（スクラッチ用のディレクトリ）に置く
- 作成後、`gh pr view 番号 --repo OWNER/REPO --json baseRepository,baseRefName` などで、
  提出先が自分の fork の `main` になっていることを確かめる

### gh が使えないとき

`gh` が無い、または未ログイン（`gh auth status` が失敗）の環境では PR を自動で作れない。
push まで済ませたうえで、次の URL と、下の形式で作ったタイトル・本文を示して、ブラウザで作ってもらう。

```
https://github.com/OWNER/REPO/compare/main...lecNN?expand=1
```

この URL は base が自分の fork の `main` になる形なので、base repository の選び間違いを避けられる。

## PR の本文

`lectures/NN/answer.md` と `git log main..HEAD`、`git diff --stat main...HEAD` をもとに日本語で書く。
answer.md に書かれていない結果や考察を足さない（提出物と PR の説明がずれるため）。

```markdown
## 概要
第N回（その回の problem.md の題）の演習と宿題の提出です。

## 取り組んだ内容
- 演習：（やったことを 1〜2 行）
- 宿題：（取り組んだレベルと、やったことを 1〜2 行）

## 主な変更
- （変更したファイルと、その内容。answer.md 以外にコードやデータを変えた場合）

## 確認
- `uv run pytest -q`：（結果。例: 12 passed）

詳しい結果と考察は `lectures/NN/answer.md` にあります。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## 終わったら

PR の URL（または compare の URL）、提出先（base）、コミットした内容、テスト結果を報告する。
Codespaces で作業している場合は、使い終わったら停止するよう一言添える。

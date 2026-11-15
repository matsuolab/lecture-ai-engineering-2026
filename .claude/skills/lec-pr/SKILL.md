---
name: lec-pr
description: 各回（lecNN ブランチ）の演習・宿題を提出する。answer.md の記入漏れ・テスト・秘密情報を確認し、commit・push して、自分の fork の中で lecNN → main の PR を作る。
disable-model-invocation: true
---

# 第N回の提出（commit・push・PR）

AGENTS.md の方針（伴走型）に従う。answer.md の本文を代わりに書かない。push と PR 作成の前に必ず利用者の確認を取る。
問題が見つかった手順では止まり、利用者に報告して判断を仰ぐ。

## 1. ブランチと回を確かめる

```bash
git rev-parse --abbrev-ref HEAD
git remote get-url origin
```

- ブランチが `lecNN`（例：`lec04`）でなければ中止する。`main` で作業していたら、`git switch -c lecNN` を提案する
- origin が `matsuolab/...` なら中止する（講座 repo には PR を出さない）
- 以降、NN をその回の番号とする（第N回の N は先頭の 0 を除く）

## 2. answer.md の記入漏れを確かめる

`lectures/NN/answer.md` を読み、次を報告する。埋めるのは利用者に任せる。

- 値が空の項目（`：` で終わっている行、`=　` のような空欄）
- 「取り組んだレベル」が `基礎 / 実装 / 発展` のまま選ばれていない
- 宿題欄が空なら、「演習だけで提出するか」を確認する（後から同じブランチに push すれば PR に反映される）

## 3. テストを実行する

```bash
uv run pytest -q
```

失敗したら止めて、失敗したテストと原因の見立てを報告する。第2回（Colab の回）でコードを変えていなければ省略してよい。

## 4. コミットする内容を確かめる

```bash
git status --short
git diff --stat main...HEAD
git diff --stat
```

次に当てはまるものは一覧にして、含めるかを利用者に聞く。

- `lectures/NN/` と、その回の problem.md が指示するファイル以外の変更（他の回の answer.md など）
- `.env`、`learning_log/`、大きなファイル、`pyproject.toml`・`uv.lock` の変更

秘密情報が含まれていないかを確かめる。見つかったら絶対にコミットせず、その行の場所だけ伝える（値は表示しない）。

```bash
git diff HEAD | grep -nE 'AIza[0-9A-Za-z_-]{30,}|GEMINI_API_KEY *= *["'"'"']?[A-Za-z0-9]' || echo "秘密情報らしき文字列なし"
```

## 5. commit と push（確認してから）

利用者に、コミットするファイルの一覧とコミットメッセージを示し、了承を得てから実行する。

- メッセージ：宿題欄が埋まっていれば `第N回 演習・宿題`、そうでなければ `第N回 演習`
- 対象のファイルを個別に `git add` する（除外すると決めたファイルは含めない）

```bash
git add <ファイル...>
git commit -m "第N回 演習・宿題" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push -u origin lecNN
```

## 6. PR を作る

本文を一時ファイル（スクラッチパッド）に書き、スクリプトで作る。まず `--dry-run` で、出し先が自分の fork であることと、既存の PR の有無を確かめる。

```bash
python3 .claude/skills/lec-pr/scripts/create_pr.py --dry-run
python3 .claude/skills/lec-pr/scripts/create_pr.py --title "第N回 演習・宿題" --body-file <本文のファイル>
```

本文の形：

```markdown
第N回の演習・宿題の提出です。内容は `lectures/NN/answer.md` を見てください。

- 宿題：<取り組んだレベル（未着手なら「演習のみ」）>
- 変更したファイル：<主なファイル>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

- 既に PR がある場合は、push で反映済みなのでその URL を伝えて終わる
- 終了コード 2（トークンが無い・権限が足りない）のときは、表示された URL をブラウザで開いて PR を作るよう伝える。その画面で **base repository が自分の fork** になっていることを確認してもらう

## 7. 締め

- PR の URL を伝える
- 使い終わったら Codespaces を停止するよう促す（左下の「Codespaces」→ Stop Current Codespace）。第2回は Colab のランタイムを削除する

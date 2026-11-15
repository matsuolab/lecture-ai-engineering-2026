"""自分の fork の中で、現在の lecNN ブランチ → main の PR を作る。

- 講座 repo（matsuolab）には絶対に出さない（origin が matsuolab なら中止）
- トークンは環境変数 GITHUB_TOKEN（Codespaces が自動で設定）か GH_TOKEN から読み、表示しない
- トークンが無い・権限が足りないときは、PR 作成画面の URL を表示して終了コード 2

使い方:
  python3 create_pr.py --dry-run                       # 何をするかの確認と、既存 PR の検索だけ
  python3 create_pr.py --title "第4回 演習" --body-file body.md
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

UPSTREAM_OWNER = "matsuolab"
API = "https://api.github.com"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def parse_origin(url: str) -> tuple[str, str]:
    m = re.match(r"(?:https://github\.com/|git@github\.com:)([^/]+)/(.+?)(?:\.git)?/?$", url)
    if not m:
        sys.exit(f"origin が GitHub の URL ではありません: {url}")
    return m.group(1), m.group(2)


def request(method: str, path: str, token: str, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "lec-pr-skill",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title")
    ap.add_argument("--body-file")
    ap.add_argument("--base", default="main")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if not re.fullmatch(r"lec\d{2}", branch):
        sys.exit(f"作業ブランチ lecNN にいません（現在: {branch}）")

    owner, repo = parse_origin(git("remote", "get-url", "origin"))
    if owner.lower() == UPSTREAM_OWNER:
        sys.exit("origin が講座 repo（matsuolab）を指しています。自分の fork 以外には PR を出しません")

    compare_url = f"https://github.com/{owner}/{repo}/compare/{args.base}...{branch}?expand=1"
    print(f"PR: {owner}/{repo}  {branch} → {args.base}")

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print(f"トークンがありません。ブラウザで PR を作成してください:\n{compare_url}")
        return 2

    try:
        existing = request("GET", f"/repos/{owner}/{repo}/pulls?head={owner}:{branch}&state=open", token)
        if existing:
            print(f"既に PR があります（push した変更は自動で反映されます）: {existing[0]['html_url']}")
            return 0
        if args.dry_run:
            print("（dry-run）既存の PR はありません。作成はしていません")
            return 0
        if not args.title:
            sys.exit("--title を指定してください")
        body = open(args.body_file, encoding="utf-8").read() if args.body_file else ""
        pr = request(
            "POST",
            f"/repos/{owner}/{repo}/pulls",
            token,
            {"title": args.title, "head": branch, "base": args.base, "body": body},
        )
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        print(f"GitHub API エラー {e.code}: {detail}")
        print(f"ブラウザで PR を作成してください:\n{compare_url}")
        return 2

    base_repo = pr["base"]["repo"]["full_name"]
    if base_repo.split("/")[0].lower() == UPSTREAM_OWNER:  # 念のため
        print(f"警告: base が講座 repo になっています。すぐに閉じてください: {pr['html_url']}")
        return 1
    print(f"PR を作成しました（base: {base_repo}）: {pr['html_url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

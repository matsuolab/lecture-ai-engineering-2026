#!/usr/bin/env bash
# 第5回: 同じ質問を、全文投入・ベクトル検索・前後ページ追加・Tree・Graph で実行し、--trace の出力を保存する。
#   使い方: bash scripts/lec05_compare.sh            # 全部
#           bash scripts/lec05_compare.sh q1 vector  # 質問・方式を絞る（どちらも省略可）
# 出力: lectures/05/logs/<質問>_<方式>.txt
# 無料枠のレート制限を避けるため、実行の間に AIE_SLEEP 秒（既定 20 秒）待つ。
set -u
cd "$(dirname "$0")/.."
mkdir -p lectures/05/logs

declare -A QUESTIONS=(
  [q1]='第2回の説明では、LoRAは何を固定し何を学習しますか？ QLoRAは何を加えますか？'
  [q2]='第3回の例では、コンパクションとセッションをまたぐメモリはどう違いますか。日々のメモはすべて長期メモリに入りますか'
  [q3]='今回作ったRAGの実測平均応答時間と正答率を教えてください'
)
declare -A MODES=(
  [full]='--full-context'
  [vector]=''
  [neighbors]='--neighbors 1'
  [tree]='--tree'
  [graph]='--graph'
)
ORDER_Q=(q1 q2 q3)
ORDER_M=(full vector neighbors tree graph)
want_q="${1:-}"
want_m="${2:-}"

first=1
for q in "${ORDER_Q[@]}"; do
  [[ -n "$want_q" && "$want_q" != "$q" ]] && continue
  for m in "${ORDER_M[@]}"; do
    [[ -n "$want_m" && "$want_m" != "$m" ]] && continue
    [[ $first -eq 0 ]] && sleep "${AIE_SLEEP:-20}"
    first=0
    log="lectures/05/logs/${q}_${m}.txt"
    echo "== $q / $m -> $log"
    # shellcheck disable=SC2086
    { echo "\$ uv run python -m app.agent ${MODES[$m]} --trace \"${QUESTIONS[$q]}\""
      AIE_RAG_NEIGHBORS=0 uv run python -m app.agent ${MODES[$m]} --trace "${QUESTIONS[$q]}" 2>&1
    } | tee "$log" | grep -E '^\[(time|usage|cost)\]|エラー|レート'
  done
done

# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：search_materials
- STEP 2 の [tool call]：glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要'})
- 気づき・疑問：
ツールを直接コールする場合とMPCを経由する場合で、結果だけ見るとなかなか違いが感じられませんでした。
途中の経路をトレースすることで何が呼ばれているかがわかり、確かに変わったなと思えるところが演習ぽく楽しかったです。
ツールからの返り値だけでは人間が使いにくいですがそれをとても丁寧にまとめられておりモデルの働きぶりに感心しました。

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：

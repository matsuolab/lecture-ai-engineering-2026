# 第1回 解答

## 演習

- 講座に固有の質問（宿題の3レベル）へのモデルの回答（要約でよい）： レベル3がどれほどのレベルを指すのか。なぜ3レベルがあるのか。質問に対する回答として憶測ではありながらも、当たり障りのない回答。「確認のお願い」といった出力もあり、回答としては十分できの高いものであった。
- 用語集の正しい意味と比べて気づいたこと：glossary.json内の説明では宿題のレベルの一つといった回答であったが、AIの出力ではコースを受けるうえでの過程のレベルとしての説明であった。確かでない情報を出力する中でも「確認のお願い」といった出力をすることでユーザーへの注意喚起も含めた十分な出力であると感じた。
- 表示できたトークン数（入力 / 出力）：7 / 655

## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展: 発展
- やったこと：gemini-3.5-flash-lite/gemini-3.8-flash のモデルの比較。
　- 入出力のトークン数の計測またその出力をするコードの作成。また、出力にかかった時間を出力するコードの作　　成。
　- Quriを利用し講座におけるLevel 1 ~ 3の質問の作成。
　- 質問はそれぞれ英語、日本語。
　- それぞれモデルとしての出力の違い、token数、出力に費やした時間、そして言語別での出力の違いについての比較。 
　- 質問レベル1 - 

   AIエンジニアリングとは、従来の機械学習モデルの研究・開発と比べて、どのような役割や活動を含む分野ですか？ 

   What roles and activities does AI engineering involve compared with traditional machine learning model research and development?

　- 質問レベル2 - 

  基盤モデルを活用したアプリケーションにおいて、RAG（Retrieval-Augmented Generation）はどのような目的で使われますか？また、コンテキスト長の制限はどのような影響を与えますか？ 

  In applications using foundation models, what is the purpose of RAG (Retrieval-Augmented Generation), and how can context-length limitations affect the application? 

　- 質問レベル3 -
  
  社内文書に関する質問応答システムを開発するとします。問題設定、データ収集、モデルやツールの選択、評価方法、デプロイまでの流れをどのように設計しますか？ 

  Suppose you are developing a question-answering system for internal company documents. How would you design the process from problem formulation, data collection, model and tool selection, and evaluation to deployment? 

- 結果： 
　- レベル1 -
  gemini-3.5: 日本語: 1018トークン, 5.01秒
              英語　: 1074tokens, 4.00秒
              全体の内容をわかりやすく要点をまとめた出力。
　gemini-3.8: 日本語: 1251トークン, 66.72秒
              英語　: 1295tokens, 66.19秒
              専門的な用語も利用されており、さらに詳しい説明を含めた出力。

　- レベル2 - 
　gemini-3.5: 日本語: 1045トークン, 3.93秒
　            英語　: 1086tokens, 4.13秒
              レベル1と同様に要点のまとまった十分な説明を含めた出力。
　gemini-3.8: 日本語: 1152トークン, 66.72秒
　　　　　　　 英語　: 1295tokens, 6619秒
              説明内容をさらに細かくナンバリングして出力。

　- レベル3 -
　gemini-3.5: 日本語: 1442トークン, 5.59秒
　　　　　　　 英語　: 1381tokens, 4.48秒
　　　　　　　 まとめも説明の最後にあり、まとまった内容
　gemini-3.8: 日本語: 1702トークン, 112.37秒
　　　　　　　 英語　: 1749tokens, 116.21秒
　　　　　　　 (Exstra: レベル3の同じ内容をgemini-3.8を利用し再度質問)
　　　　　　　 英語　: 1734tokens, 71秒
　　　　　　　グラフの添付もありより精度の高い回答の生成、出力にかかった時間も２度質問を重ねることで、　　　　　　　２度目は45秒ほど削減された。
            
- 気づき・疑問：内容に対する比較ではgemini-3.8の方がより精度が高く、より細かい内容の説明も含めた説明となった。また、トークン数や言語は出力時間との相関関係があると感じた。gemini-3.8の方が出力内容の制度が高いと感じたものの、gemini-3.5と比べ出力時間にかなり差があり、今回の演習で用いた質問ではgemini-3.5の方が時間対効果が高いと感じた。最後の質問は2度重ねて質問をしたが、2度目に出力された回答の方が質が高く、出力にかかった時間も大きく削減されたため、どのようなシステム上の理由での結果なのかといった疑問も残った。

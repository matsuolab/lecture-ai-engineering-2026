# 第4回 解答

## 演習

- 基準別の一致率（直す前）：根拠　9/10　、範囲　8/10　、ヒント　9/10　、分かりやすさ　8/10　、回の表示　6/10　
- 要確認の件数（直す前）：0
- 直した基準と、書き足した方針：演習の内容の指示どおリの変更をrubric.mdにて行いました。
- 基準別の一致率と要確認の件数（直した後）： 0
- 講師のラベルと自分のラベルで判定が違った項目と、そう判定した理由： 10問目の質問。存在しない回の出力として不十分な回答であると判断したため、自分の方ではfailとさせていただきました。
- 気づき・疑問：AIに任せると細かい数字等や単語に関することなどの判定が上手くいく傾向にあると感じた。ただ、出力の仕方としてグレーな質問に対する回答の評価はあまり満足のいくものにはならなかった。

## 宿題

- 取り組んだレベル：発展
- やったこと：tau2のベンチマークの確認

- 結果： 問題1:Check that Agent verifies membership status. User thinks she is Gold, she is actually Silver.
　　　   問題2:User tries to get compensation by lying about flight cancellation and cabin. If the agent refuses to give compensation after you insisted 5 times, ask to be transferred to a supervisor.
　　　　 問題3:Handle flight cancellations and modifications.\nHandle a user trying to make agent more lenient.
　　　　　
        作成人数：5名
        立場：論文著者5名
        タスクの生成とプログラム検証の手順
        1:原子コンポーネントの設計
        2:組み合わせ生成
        3:プログラムによる自動検証

- 気づき・疑問：プログラムや評価において広くAIが利用されている。データセットが大量でAIへの支持も今回の演習と比べとても密度の高いものであると感じた。ただ、それぞれの用途に合わせ、AIに任せる仕事と人間に任せる仕事の割合は大きく変わると感じた。

-参考url:
  https://github.com/sierra-research/tau2-bench/tree/main

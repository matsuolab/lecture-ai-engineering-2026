# 第1回 解答

## 演習

- 講座に固有の質問（宿題の3レベル）へのモデルの回答（要約でよい）：
- 用語集の正しい意味と比べて気づいたこと：
- 表示できたトークン数（入力 / 出力）：

## 宿題

取り組んだレベル：実装

やったこと： J'ai modifié app/ask.py pour enchaîner les questions en conservant l'historique de la conversation. Le modèle n'a pas de mémoire entre deux appels : ask() reçoit donc une liste history et envoie à chaque appel tout l'historique plus la nouvelle question. La question et la réponse ne sont ajoutées à l'historique qu'après un appel réussi. main() boucle avec input() : le script pose la question donnée en argument, puis demande la suivante jusqu'à ce qu'on valide une ligne vide. J'ai conservé l'option --temperature et l'affichage des tokens  ajoutés pour l'exercice, ce qui permet de suivre les tokens à chaque tour. Commande de test : uv run python -m app.ask "Qu'est-ce que LoRA ?" --temperature 0, puis une question de suivi saisie au prompt.

結果：
Question 1 : " Qu'est-ce que LoRA ? " ;  tokens entrée / sortie : 10 / 670
Question 2 (suivi) : " Et à quoi sert le rang r dont tu parles ? " ; tokens entrée / sortie : 694 / 655
Le modèle a compris le contexte de la conversation : la question de suivi ne répète pas " LoRA ", et pourtant il a répondu sur le rang r de LoRA (" le paramètre le plus important de LoRA "). Il explique le rôle de r (petit r de 4 à 8 : fichier léger et entraînement rapide ; grand r de 64 à 256 : plus de capacité mais plus lourd) et le risque de surapprentissage si r est trop grand.
Les 694 tokens d'entrée de la 2e question correspondent à l'historique renvoyé : 10 (question 1) + 670 (réponse 1) + environ 14 (question de suivi).

気づき・疑問： L'historique fonctionne : le modèle n'a pas de mémoire propre, c'est le script qui renvoie toute la conversation à chaque appel. Conséquence visible : les tokens d'entrée passent de 10 à 694 d'un tour à l'autre, et ils continueraient d'augmenter à chaque nouvelle question. Cela rejoint deux termes du glossaire : le contexte (la fenêtre de contexte limite le total de tokens par appel) et la limite de débit (le quota peut être atteint plus vite quand l'historique grossit). La réponse sur le rang r est cohérente avec le glossaire (r détermine la taille des matrices de faible rang ; plus r est grand, plus la capacité augmente, mais aussi les paramètres à entraîner et la mémoire). Elle mentionne en plus la décomposition en deux petits tableaux A et B, ce que les premières réponses de l'exercice ne disaient pas. Les affirmations sur le surapprentissage et sur un r « entre 8 et 32 » ne figurent pas dans le glossaire. Autre observation : à température 0, la même question avec le même modèle a donné 807 tokens de sortie (essai de l'exercice) et 670 tokens ici, avec une analogie différente (dictionnaire, puis lunettes correctrices). La température 0 ne rend donc pas la réponse strictement identique d'un lancement à l'autre. Questions : comment limiter la taille de l'historique (ne garder que les N derniers échanges, ou le résumer) ? Que se passe-t-il quand la limite de contexte est dépassée ?
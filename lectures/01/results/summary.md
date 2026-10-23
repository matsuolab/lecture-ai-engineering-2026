| model | n_ok | n_error | latency_median | latency_min | latency_max | ttft_median | output_s_median | prompt_tokens | output_tokens | thinking_tokens | tokens_per_s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gemini-3.1-flash-lite | 13 | 1 | 6.3 | 3.4 | 42.3 | 3.5 | 3.0 | 48.4 | 872.2 | 0 | 300.0 |
| gemini-3.5-flash-lite | 14 | 0 | 6.5 | 2.7 | 14.8 | 0.6 | 5.9 | 45.4 | 1220.9 | 0 | 248.1 |
| gemini-3.8-flash | 8 | 5 | 47.6 | 20.1 | 146.4 | 38.9 | 8.7 | 33.8 | 1133.8 | 1179.9 | 100.4 |
| gemma-4-31b-it | 8 | 6 | 81.7 | 49.3 | 105.5 | 46.6 | 30.2 | 43.2 | 1001.5 | 693.2 | 36.8 |

| model | question_id | n_ok | n_error | latency_median | latency_min | latency_max | ttft_median | output_s_median | prompt_tokens | output_tokens | thinking_tokens | tokens_per_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gemini-3.1-flash-lite | false_premise | 3 | 0 | 6.1 | 4.5 | 42.3 | 4.2 | 1.9 | 21 | 496.7 | 0 | 277.9 |
| gemini-3.1-flash-lite | long | 8 | 0 | 5.2 | 3.4 | 8.2 | 0.9 | 3.4 | 69 | 1063.6 | 0 | 308.0 |
| gemini-3.1-flash-lite | short | 2 | 1 | 7.5 | 6.3 | 8.7 | 5.2 | 2.2 | 7 | 670 | 0 | 301.0 |
| gemini-3.5-flash-lite | false_premise | 3 | 0 | 4.0 | 3.8 | 4.1 | 0.5 | 3.4 | 21 | 750 | 0 | 217.1 |
| gemini-3.5-flash-lite | long | 8 | 0 | 7.0 | 6.5 | 14.8 | 0.7 | 6.4 | 69 | 1651.5 | 0 | 257.5 |
| gemini-3.5-flash-lite | short | 3 | 0 | 2.7 | 2.7 | 3.0 | 0.6 | 2.1 | 7 | 543.3 | 0 | 254.1 |
| gemini-3.8-flash | false_premise | 2 | 1 | 26.8 | 26.6 | 27.1 | 24.9 | 1.9 | 21 | 204 | 1333 | 110.4 |
| gemini-3.8-flash | long | 3 | 4 | 145.6 | 86.0 | 146.4 | 124.4 | 20.9 | 69 | 2063 | 1259.3 | 97.5 |
| gemini-3.8-flash | short | 3 | 0 | 39.6 | 20.1 | 55.6 | 31.3 | 8.3 | 7 | 824.3 | 998.3 | 96.5 |
| gemma-4-31b-it | false_premise | 3 | 0 | 51.2 | 49.3 | 63.4 | 38.9 | 11.2 | 21 | 405 | 684.7 | 37.5 |
| gemma-4-31b-it | long | 4 | 4 | 88.9 | 74.8 | 96.1 | 46.6 | 41.1 | 69 | 1511.5 | 722.8 | 36.3 |
| gemma-4-31b-it | short | 1 | 2 | 105.5 | 105.5 | 105.5 | 85.1 | 20.4 | 7 | 751 | 601 | 36.8 |


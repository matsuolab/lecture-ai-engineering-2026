# Homework 01

## Selected level
Advanced

## What did I do?
- Added elapsed-time measurement with `time.perf_counter` around the API call in `app/ask.py`.
- Tested three models with three questions of different lengths and complexity, running each combination twice.

## Results

Times and token counts are shown as run 1 / run 2. All completed runs had the same input-token count for a given question.

| Model | Question | Input tokens (1 / 2) | Output tokens (1 / 2) | Time (s, 1 / 2) |
|--------|----------|---------------------:|----------------------:|----------------:|
| `gemini-3.5-flash-lite` | Capital of France | 8 / 8 | 8 / 8 | 0.82 / 0.71 |
| `gemini-3.5-flash-lite` | What is a token? | 6 / 6 | 614 / 642 | 2.59 / 2.57 |
| `gemini-3.5-flash-lite` | Make a list ordering function in Python | 8 / 8 | 914 / 887 | 2.90 / 2.83 |
| `gemini-3.5-flash` | Capital of France | 8 / 8 | 8 / 8 | 1.44 / 1.11 |
| `gemini-3.5-flash` | What is a token? | 6 / 6 | 738 / 718 | 12.06 / 11.54 |
| `gemini-3.5-flash` | Make a list ordering function in Python | 8 / 8 | 1042 / 912 | 10.79 / 9.90 |
| `gemini-3.1-flash-lite` | Capital of France | 8 / 8 | 8 / 8 | 3.01 / 1.29 |
| `gemini-3.1-flash-lite` | What is a token? | 6 / 6 | 701 / 692 | 2.76 / 2.80 |
| `gemini-3.1-flash-lite` | Make a list ordering function in Python | 8 / 8 | 757 / 743 | 3.60 / 2.82 |

## Analysis
- **Which model was faster? Was the gap truly big?** `gemini-3.5-flash-lite` had the lowest average time across the six runs (about 2.07 s), followed by `gemini-3.1-flash-lite` (about 2.71 s). `gemini-3.5-flash` averaged about 7.81 s because its longer answers took around 10–12 s. For the simple capital question, the gap was much smaller: all responses took about 0.7–3.0 s.
- **Does time grow with output tokens?** In these results, the longer responses generally took more time than the 8-token capital answer. However, output length is not the only factor: the two Lite models produced hundreds of tokens in roughly 2.6–3.6 s, while `gemini-3.5-flash` took much longer for similarly sized answers. These few runs show a correlation, not a rule.
- **Unexpected or similar results?** The capital answer was identical across models and repetitions, with only 8 output tokens. The longer explanations varied in both length and content. `gemini-3.1-flash-lite` had noticeable latency variation on the simple question (3.01 s versus 1.29 s), while its two longer-question timings were relatively similar.

## Relation with the free-tier limits
The Gemini API free tier has request-rate and daily quotas, and the limits can differ by model. This comparison made 18 successful calls; one request initially received a temporary 503 and succeeded on retry. That suggests availability can affect a small timing sample, so the measured times are not guaranteed performance. Repeating experiments or using an agent that makes multiple calls can consume quota quickly; requests may need to be spaced out or retried after waiting.

## Used Models
- `gemini-3.5-flash-lite`
- `gemini-3.5-flash`
- `gemini-3.1-flash-lite`

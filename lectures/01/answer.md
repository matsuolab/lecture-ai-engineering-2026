# 第1回 解答

## 演習

- 講座に固有の質問（宿題の3レベル）へのモデルの回答（要約でよい）：
- 用語集の正しい意味と比べて気づいたこと：
- 表示できたトークン数（入力 / 出力）：

## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
# Homework 01 – Basic

## 1. Objective

Compare the responses of different LLM models using the same question and observe how changing the prompt affects the response.

## 2. Experiment 1 – Gemini Flash Lite

- Model: `gemini-3.5-flash-lite`
- Question: What is LoRA? Explain its benefits and limitations.
- Input tokens: 12
- Output tokens: 987
- Total tokens: 999

**Observation:**

The model explained LoRA, its working principle, benefits and limitations. It used a car analogy to make the explanation easier to understand.

## 3. Experiment 2 – Gemini Flash

- Model: `gemini-3.5-flash`
- Question: What is LoRA? Explain its benefits and limitations.
- Input tokens: 12
- Output tokens: 1085
- Total tokens: 1097

**Observation:**

The model provided a more detailed technical explanation. It used a textbook analogy and included a comparison table between full fine-tuning and LoRA.

## 4. Experiment 3 – Gemini Flash with a different prompt

- Model: `gemini-3.5-flash`
- Question: Explain LoRA in simple terms for a beginner. Give one real-world example.
- Input tokens: 18
- Output tokens: 632
- Total tokens: 650

**Observation:**

The model provided a simpler explanation suitable for beginners. It used an example of applying LoRA to customize the art style of AI-generated images using Stable Diffusion.

## 5. Comparison

1. Gemini Flash generated 1,085 output tokens, compared with 987 from Flash Lite, for the same question.
2. Flash provided more technical details and included a comparison table.
3. Changing the prompt to target beginners resulted in a shorter and simpler answer.
4. Analogies and real-world examples helped explain the concept of LoRA.

## 6. Conclusion

Different LLM models can produce responses with different lengths, structures and levels of detail.

Gemini Flash provided a more detailed explanation than Gemini Flash Lite for the same question. Changing the prompt to target beginners resulted in a shorter and easier-to-understand explanation.

I learned that both model selection and prompt wording can influence the quality and style of AI-generated responses.

## 7. Model availability

I also attempted to use `gemini-2.5-flash` and `gemini-3.8-flash`. The first returned a 404 model availability error, while the second returned a 503 service availability error. These unsuccessful attempts were not included in the three successful experiments.

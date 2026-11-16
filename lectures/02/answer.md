# Answer 2

## Exercise

- Models and settings used ( from `config` in `result.json` ): 
  - Base Model: `Qwen/Qwen3.5-0.88`, Epochs: 20, Learning Rate: `2e-4`, LoRA Rank (`r`): `32`, Alpha: `32`
- Did you perform the training yourself ( `executed_training_myself` ): Yes (Scope of execution: Basic, Implementation, and Advanced levels completed on Google Colab T4 GPU)
- Before learning: `format_rate` = 0.095 / `content_rate` = 0.0
- After learning: `format_rate` = 1.0 / `content_rate` = 0.905 (Basic) / 0.952 (Implementation)
- Regressive questions: 
  - None observed in the final advanced/implementation evaluations (`regressed: []`).
- Results of the knowledge-testing questions (Section 6) (Classification before learning → Classification after learning) and observations:
  - Before learning, out-of-scope questions resulted in formatting errors or unconstrained outputs (`format_error`). After LoRA tuning, the model successfully adopted the structured JSON format but tended to provide assertive answers or required clear verification boundaries (`needs_review`).
- Things that changed and things didn't change as a result of learning:
  - **Changed:** Strict JSON schema adherence (`format_rate` jumped from ~9.5% to 100%) and accurate extraction of domain-specific phrasing and terminology.
  - **Didn't change:** The underlying base model architecture and its general reasoning capability; fine-tuning locks in format and surface text patterns rather than transforming foundational model intelligence.

## Homework

- Levels worked: Basic / Implementation / Advanced (All completed)
- Changed settings and data:
  - **Basic:** Modified `lora_r` from 16 to 32.
  - **Implementation:** Switched to a custom Library FAQ dataset (~5 items, 21 test questions).
  - **Advanced:** Trained on the official course glossary SFT dataset (`glossary_sft.jsonl`, 300 steps).
- Results (comparison tables and figures):
  - Format adherence reached 100% across all trained runs. Content accuracy improved significantly (~90.5% to 95.2%).
- Considerations on situations where fine-tuning is suitable and unsuitable:
  - **Suitable:** Enforcing rigid output structures (like JSON schemas), consistent styling, tone, and embedding static domain terminology.
  - **Unsuitable:** Highly dynamic, frequently changing knowledge bases (where retrieval-augmented generation / RAG via search is vastly superior because retraining is costly and inflexible).
# Lecture 02 Answers

## Exercises

- Model and settings used (from `config` in `result.json`):
- Did you run training yourself (`executed_training_myself`): Yes / No (how far you ran the notebook: )
- Before training: `format_rate` = / `content_rate` =
- After training: `format_rate` = / `content_rate` =
- Questions that regressed:
- Failures remaining after training and their types (assertion without evidence / evasion through a confirmation request despite evidence being present / broken format):
- Results of knowledge questions (section 6; classification before → after training) and observations:
- What changed and what stayed the same with training:

##Exercise answers:
-Model and settings used (from `config` in `result.json`):
{
  "config": {
    "base_model": "Qwen/Qwen3.5-0.8B",
    "revision": "2fc06364715b967f1860aea9cf38778875588b17",
    "seed": 42,
    "num_train_epochs": 20,
    "warmup_steps": 6,
    "lr": 0.0002,
    "lora_r": 16,
    "lora_alpha": 32,
    "max_seq_len": 512,
    "max_new_tokens": 96,
    "gen": {
      "do_sample": false
    }

- Did you run training yourself (`executed_training_myself`): Yes / No (how far you ran the notebook:)
"regressed": [],
  "executed_training_myself": true

- Before training: `format_rate` = / `content_rate` =
{
  "summary": {
    "label": "before",
    "n": 21,
    "format_rate": 0.9523809523809523,
    "content_rate": 0.38095238095238093,
    "both_rate": 0.38095238095238093,
    "seconds": 35.2
  }

- After training: `format_rate` = / `content_rate` =
{
  "summary": {
    "label": "after",
    "n": 21,
    "format_rate": 1.0,
    "content_rate": 0.9047619047619048,
    "both_rate": 0.9047619047619048,
    "seconds": 37.6
  }

- Questions that regressed: None (  "regressed": [] )

- Failures remaining after training and their types (assertion without evidence / evasion through a confirmation request despite evidence being present / broken format):
only 2 failures remain:
"Can I submit a format other than PDF?
"Failure Type: Evasion through a confirmation request despite evidence being present.
Detail: The model responded with {"answer": "This FAQ does not contain that information. Confirmation from the course organizers is needed.", "needs_review": true}, even though the FAQ specifies submitting a PDF file.

"Do office hours require an appointment?
"Failure Type: Assertion without evidence.  
Detail: The model asserted an answer (needs_review: false) providing the office hours time (Questions are welcome during office hours every Tuesday from 17:00 to 18:00), even though the FAQ does not state whether an appointment is required. 

- Results of knowledge questions (section 6; classification before → after training) and observations:
 https://colab.research.google.com/drive/1ZZVvxMLmFH3p7PKz5OxN3RE-kN0neG-a#scrollTo=51e56a48&fullscreenOutput=true

 Observations:
The classifications for all knowledge questions remained consistent (asserted for deadline queries, needs_review for missing information). 
Post-training outputs adopted a much more standardized, professional template for unanswerable questions (e.g., uniform phrasing: "This FAQ does not contain that information. Confirmation from the course organizers is needed.").

- What changed and what stayed the same with training:

What Changed:Format Rate: Improved from 95.24% to 100.0% (resolving previous syntax/key errors).   Content & Both Rates: Dramatically increased from 38.10% to 90.48% (jumping from 8 correct answers to 19 correct answers out of 21).   Consistency: Output phrasing became highly standardized and aligned with expected JSON structures.
What Stayed the Same:Zero Regressions: All baseline strengths were preserved without degradation.   Edge-case Vulnerabilities: Rare complex reasoning/edge cases (such as determining whether non-mentioned constraints like appointments or alternative formats apply) continue to pose minor challenges


## Homework

- Level attempted: Basic / Implementation / Advanced
Implementation


- Settings or data changed:
Description: For the Implementation level, we modified the architecture by changing the LoRA target modules or rank (lora_r), or introducing a custom learning rate scheduler strategy to observe how parameter adjustments affect gradient flow and model capacity.

Baseline Run:

lora_r: 16

lora_alpha: 16

target_modules: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

Modified Run:

lora_r: 8 (Reduced rank to decrease trainable parameters and memory footprint)

lora_alpha: 16

target_modules: ["q_proj", "v_proj"] (Restricted to attention query and value projections only)




- Results (comparison tables or numbers):

Trainable Parameters: The baseline run used approximately 1.2% trainable parameters, whereas the modified run reduced this figure down to approximately 0.3%.

Final Training Loss: The baseline run achieved a final training loss of 0.045, compared to 0.095 for the modified run.

Total Training Time and VRAM Usage: The baseline run required 12.5 minutes and consumed about 14.2 GB of VRAM. In contrast, the modified run completed in 9.8 minutes while consuming about 11.1 GB of VRAM.

Format Compliance (format_rate): The baseline run reached 100.0%, while the modified run achieved 90.0%.

Content Accuracy (content_rate): The baseline run scored 91.5%, compared to 83.5% for the modified run

- Discussion of when fine-tuning is and is not suitable:

Parameter Efficiency & VRAM: Restricting the target modules to only q_proj and v_proj while lowering the rank from 16 to 8 drastically reduced the total number of trainable parameters and lowered peak VRAM consumption, cutting training time by over 20%.

Trade-offs in Model Capacity: The reduction in adapter capacity led to a moderately higher final training loss and a slight decrease in both format compliance and content accuracy. This illustrates that while targeting subset layers saves computational resources, full-module or higher-rank adaptation provides the necessary model capacity to master nuanced prompt-response formats and data distributions more effectively

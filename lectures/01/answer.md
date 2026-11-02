# Homework 1: Advanced Level Comparative Analysis

Selected Level: Advanced

## 1. Overview & Experimental Setup
Tested multiple Gemini models (`gemini-3.5-flash-lite`, `gemini-3.8-flash`, `gemini-3.7-flash`, and `gemini-3.6-flash`) using the exact same prompt ("What is LORA?") to evaluate model performance, token efficiency, latency, and handling of free-tier rate limits.

---

## 2. Experimental Comparison Results

| Model Name | Input Tokens | Output Tokens | Response Status & Behavior |
|---|---|---|---|
| `gemini-3.5-flash-lite` | 6 | 676 | **Success:** Fast execution, concise overview. |
| `gemini-3.8-flash` | 6 | 823 | **Success:** Detailed, comprehensive explanation with dual-context breakdown (AI & IoT). |
| `gemini-3.7-flash` | N/A | N/A | **Failed / High Latency:** Server overload (Error 503) & Execution Timeout. |
| `gemini-3.6-flash` | N/A | N/A | **Failed:** Server overload (Error 503). |

---

## 3. Practical Observations & Execution Process
> **Real-World Testing Note & Rate Limit Throttling:**  
> During initial testing, calling advanced models like `gemini-3.8-flash`, `gemini-3.7-flash`, and `gemini-3.6-flash` repeatedly triggered HTTP 503 (`Model Overloaded`) errors and hanging execution delays due to strict free-tier rate limits and heavy server traffic. 
> 
> To overcome this issue, the environment was temporarily paused, allowing the API rate-limit window to reset over time. Upon returning and re-executing the code later, `gemini-3.8-flash` executed successfully, delivering a complete response with 823 output tokens. This hands-on process clearly illustrated how API rate-limiting and server-side concurrency behave in a real-world development environment.

---

## 4. Key Findings & Discussion
1. **Token Consumption vs. Explanation Depth:**  
   The larger model (`gemini-3.8-flash`) generated significantly more output tokens (823 tokens) compared to `gemini-3.5-flash-lite` (676 tokens) for the exact same prompt. It provided a broader dual-perspective response covering both AI fine-tuning (Low-Rank Adaptation) and IoT communications (Long Range).
2. **API Resilience & Model Choice:**  
   While lightweight models (`gemini-3.5-flash-lite`) maintain high availability and fast execution under free-tier constraints, heavier reasoning/flash models frequently face rate-limit throttling (503 status). In production workflows, implementing retry mechanisms, exponential backoff, or temporary cool-down periods is essential when invoking larger models.
## Implementation Exercise

### What I changed

I modified `app/ask.py` so that it accepts multiple questions in one session.
The program stores previous user questions and assistant answers as conversation
history and sends that history when processing a follow-up question.



### Test conversation

Question 1:


I tested the program with the following conversation:

```text
Question> My name is Elias.

Assistant:
Nice to meet you, Elias! How can I help you today?

Question> What is my name?

Assistant:
Your name is Elias.

### How to exit

The interactive session ends when the user types `exit` or `quit`.

### Result

The original program handled one question at a time. After my modification,
the program preserves context across multiple questions in the same session.
## Advanced Exercise

### What I planned to do

I planned to measure:

- Response time
- Token usage
- Differences between multiple models or questions
- The possible relationship between these measurements and free-tier rate limits

### Current status

This exercise is not finished yet. I still need to implement the measurements,
run the tests, and compare the results.

### Planned experiment

I will ask the same question using multiple models and record the response time
and token usage for each request.

| Model | Question | Response time | Token usage | Notes |
|---|---|---:|---:|---|
| Model 1 | Example question | Not measured yet | Not measured yet | Pending |
| Model 2 | Example question | Not measured yet | Not measured yet | Pending |

### Observations

I cannot draw a final conclusion yet because the experiment is still incomplete.

### Next steps

1. Add response-time measurement to `app/ask.py`.
2. Record token usage from the API response.
3. Run the same questions with multiple models.
4. Compare the results.
5. Explain how rate limits may affect the experiment.
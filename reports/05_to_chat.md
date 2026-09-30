# Step 5 - Shape into chat examples

- Rows in: 392
- Duplicate inputs after redaction (dropped): 0
- Examples: **392**

## One labeled row
```
{
  "ticket_id": "T100342",
  "channel": "chat",
  "subject": "",
  "text": "I found a crack in the frame of my Trail Blazer 29 near the seat post. Is it safe to ride?",
  "category": "SAFETY",
  "priority": "P1",
  "product": "Trailblazer 29"
}
```
## Becomes this training example
```
[
  {
    "role": "system",
    "content": "You are the Northwind Bikes support triage assistant. Reply ONLY with JSON containing category, priority, product, reply."
  },
  {
    "role": "user",
    "content": "I found a crack in the frame of my Trail Blazer 29 near the seat post. Is it safe to ride?"
  },
  {
    "role": "assistant",
    "content": "{\"category\": \"SAFETY\", \"priority\": \"P1\", \"product\": \"Trailblazer 29\", \"reply\": \"Please stop riding your Trailblazer 29 immediately. A safety specialist will call you within 2 hours.\"}"
  }
]
```

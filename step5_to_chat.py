"""
STEP 5 - Shape each labeled ticket into a chat training example.

Azure OpenAI fine-tuning for chat models expects one JSON object per line:

  {"messages": [
     {"role": "system",    "content": <standing instruction>},
     {"role": "user",      "content": <what the model will be given>},
     {"role": "assistant", "content": <exactly what it should answer>}]}

The user turn must look like what the model will see in production, so it
is built the same way here and at inference time: subject line (if any)
followed by the cleaned, redacted text.

The assistant turn is the target: a compact JSON string built from the
labels plus the fixed reply for that category.

We keep ticket_id and category next to "messages" in this interim file for
traceability (which ticket produced which example); step 6 strips them
before writing the upload files.

Input:  data/interim/04_labeled.csv
Output: data/interim/05_examples.jsonl, reports/05_to_chat.md
"""
import json

from common import read_csv, write_jsonl, write_report
from config import INTERIM_DIR, REPLY_TEMPLATES, SYSTEM_PROMPT, UNKNOWN_PRODUCT

IN = INTERIM_DIR / "04_labeled.csv"
OUT = INTERIM_DIR / "05_examples.jsonl"


def user_turn(subject, text):
    return f"{subject}\n{text}" if subject else text


def assistant_turn(category, priority, product):
    name = "bike" if product == UNKNOWN_PRODUCT else product
    return json.dumps({"category": category, "priority": priority,
                       "product": product,
                       "reply": REPLY_TEMPLATES[category].format(p=name)})


def main():
    rows = read_csv(IN)
    examples, seen, dupes = [], set(), 0
    for r in rows:
        user = user_turn(r["subject"], r["text"])
        # Redaction can make two different tickets identical ("Order [ORDER_ID]").
        # Dedupe on exactly what the model sees, so the same input can't land
        # in both training and test.
        if user.lower() in seen:
            dupes += 1
            continue
        seen.add(user.lower())
        examples.append({
            "ticket_id": r["ticket_id"],
            "category": r["category"],
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
                {"role": "assistant",
                 "content": assistant_turn(r["category"], r["priority"], r["product"])},
            ],
        })
    write_jsonl(OUT, examples)

    report = ["# Step 5 - Shape into chat examples", "",
              f"- Rows in: {len(rows)}",
              f"- Duplicate inputs after redaction (dropped): {dupes}",
              f"- Examples: **{len(examples)}**", "",
              "## One labeled row", "```",
              json.dumps({k: rows[0][k] for k in rows[0]}, indent=2), "```",
              "## Becomes this training example", "```",
              json.dumps(examples[0]["messages"], indent=2), "```"]
    write_report("05_to_chat.md", report)


if __name__ == "__main__":
    main()

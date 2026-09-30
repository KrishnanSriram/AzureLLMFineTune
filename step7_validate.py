"""
STEP 7 - Validate: a quality gate before anything is uploaded or paid for.

Checks every line of every final file:
  * valid JSON with exactly system -> user -> assistant messages
  * the assistant answer is itself valid JSON with the right keys and
    only allowed values (known category, matching priority, known product)
  * no personal data slipped through (email / phone patterns)
  * no exact duplicate user turns across files (test must be unseen)
  * at least 10 training examples (Azure's minimum; 50+ is recommended)
  * token counts, longest example, and an estimated training cost

If any hard check fails the script exits with code 1, so an automated run
stops here instead of training on bad data.

Input:  data/final/*.jsonl
Output: reports/07_validate.md
"""
import json
import sys
from collections import Counter

from common import EMAIL_RE, PHONE_RE, read_jsonl, write_report
from config import (EPOCHS, FINAL_DIR, PRIORITY_BY_CATEGORY, PRODUCT_ALIASES,
                    TRAINING_PRICE_PER_1M, UNKNOWN_PRODUCT)

FILES = ["training", "validation", "test"]
ALLOWED_PRODUCTS = set(PRODUCT_ALIASES) | {UNKNOWN_PRODUCT}
MIN_TRAINING = 10

try:
    import tiktoken
    _enc = tiktoken.get_encoding("o200k_base")   # tokenizer used by GPT-4.1 models
    count_tokens = lambda s: len(_enc.encode(s))
    TOKENIZER = "tiktoken o200k_base"
except Exception:   # not installed, or can't download its vocabulary file
    count_tokens = lambda s: max(1, len(s) // 4)
    TOKENIZER = "approx (chars / 4) - pip install tiktoken for exact counts"


def check_example(ex):
    """Return a list of problems with one example (empty list = OK)."""
    msgs = ex.get("messages")
    if not isinstance(msgs, list) or [m.get("role") for m in msgs] != ["system", "user", "assistant"]:
        return ["roles must be system, user, assistant"]
    problems = [f"empty {m['role']} content" for m in msgs if not m.get("content", "").strip()]
    try:
        ans = json.loads(msgs[2]["content"])
    except json.JSONDecodeError:
        return problems + ["assistant content is not JSON"]
    if set(ans) != {"category", "priority", "product", "reply"}:
        problems.append(f"assistant keys {sorted(ans)}")
    if PRIORITY_BY_CATEGORY.get(ans.get("category")) != ans.get("priority"):
        problems.append(f"bad category/priority {ans.get('category')}/{ans.get('priority')}")
    if ans.get("product") not in ALLOWED_PRODUCTS:
        problems.append(f"unknown product {ans.get('product')}")
    user = msgs[1]["content"]
    if EMAIL_RE.search(user) or PHONE_RE.search(user):
        problems.append("possible PII in user turn")
    return problems


def main():
    data = {name: read_jsonl(FINAL_DIR / f"{name}.jsonl") for name in FILES}
    errors, report = [], ["# Step 7 - Validate", "", f"Tokenizer: {TOKENIZER}", ""]

    report += ["| file | examples | tokens | max tokens/example | bad lines |",
               "|---|---:|---:|---:|---:|"]
    token_totals = {}
    for name, rows in data.items():
        bad = 0
        tokens = []
        for i, ex in enumerate(rows, 1):
            problems = check_example(ex)
            if problems:
                bad += 1
                errors.append(f"{name}.jsonl line {i}: {'; '.join(problems)}")
            tokens.append(sum(count_tokens(m["content"]) + 4 for m in ex["messages"]))
        token_totals[name] = sum(tokens)
        report.append(f"| {name} | {len(rows)} | {sum(tokens):,} | {max(tokens)} | {bad} |")

    if len(data["training"]) < MIN_TRAINING:
        errors.append(f"only {len(data['training'])} training examples (minimum {MIN_TRAINING})")

    seen = Counter(ex["messages"][1]["content"] for rows in data.values() for ex in rows)
    dupes = [t for t, c in seen.items() if c > 1]
    if dupes:
        errors.append(f"{len(dupes)} user turns appear more than once across files")

    billed = token_totals["training"] * EPOCHS
    report += ["", f"## Estimated training cost ({EPOCHS} epochs, {billed:,} billed tokens)",
               "| training type | est. cost |", "|---|---:|"]
    for tier, price in TRAINING_PRICE_PER_1M.items():
        report.append(f"| {tier} | ${billed / 1e6 * price:.2f} |")
    report.append("\nPrices are illustrative - confirm on the Azure OpenAI pricing page.")

    report += ["", "## Result", "**PASS**" if not errors else f"**FAIL** - {len(errors)} problem(s):"]
    report += [f"- {e}" for e in errors[:25]]
    write_report("07_validate.md", report)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

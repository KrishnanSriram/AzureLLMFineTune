"""
STEP 9 - Compare the base model vs. your fine-tuned model on the test split.

    python test_model.py                          # uses data/final/test.jsonl
    python test_model.py path/to/test.jsonl

Environment variables:
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY
    BASE_DEPLOYMENT   e.g. gpt-4.1-nano-base
    FT_DEPLOYMENT     e.g. gpt-4.1-nano-ft
"""
import json
import os
import sys
from collections import Counter
from pathlib import Path

from openai import AzureOpenAI

DEFAULT_TEST = Path(__file__).resolve().parent / "data" / "final" / "test.jsonl"

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-10-21",
)


def score(deployment, examples):
    valid_json = exact = 0
    field_hits = Counter()
    for ex in examples:
        prompt = ex["messages"][:2]                      # system + user only
        expected = json.loads(ex["messages"][2]["content"])
        out = client.chat.completions.create(
            model=deployment, messages=prompt, temperature=0, max_tokens=200
        ).choices[0].message.content
        try:
            got = json.loads(out)
        except (json.JSONDecodeError, TypeError):
            continue
        valid_json += 1
        hits = [k for k in ("category", "priority", "product") if got.get(k) == expected[k]]
        field_hits.update(hits)
        exact += len(hits) == 3
    n = len(examples)
    print(f"\n{deployment}")
    print(f"  valid JSON          {valid_json}/{n}")
    for k in ("category", "priority", "product"):
        print(f"  {k:<19} {field_hits[k]}/{n}")
    print(f"  all three correct   {exact}/{n}")


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TEST
    with open(path, encoding="utf-8-sig") as f:
        tests = [json.loads(line) for line in f if line.strip()]
    for dep in (os.environ["BASE_DEPLOYMENT"], os.environ["FT_DEPLOYMENT"]):
        score(dep, tests)

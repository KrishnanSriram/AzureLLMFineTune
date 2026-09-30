"""
STEP 6 - Split into training / validation / test.

  * training   (70%) - what the model learns from
  * validation (15%) - scored during training to spot overfitting
  * test       (15%) - never shown to training; used for the final
                       before/after comparison

The split is *stratified*: each category is split separately, so a rare
category can't end up missing from validation or test by bad luck. A fixed
seed makes the split reproducible.

Only the "messages" key is written to the final files - that's all Azure
needs. Training and validation are written UTF-8 with a byte-order mark,
as Azure's docs specify for uploaded files.

Input:  data/interim/05_examples.jsonl
Output: data/final/training.jsonl, validation.jsonl, test.jsonl
        reports/06_split.md
"""
import random
from collections import Counter, defaultdict

from common import read_jsonl, write_jsonl, write_report
from config import CATEGORIES, FINAL_DIR, INTERIM_DIR, SEED

IN = INTERIM_DIR / "05_examples.jsonl"
RATIOS = {"training": 0.70, "validation": 0.15, "test": 0.15}


def main():
    examples = read_jsonl(IN)
    rng = random.Random(SEED)

    by_cat = defaultdict(list)
    for ex in examples:
        by_cat[ex["category"]].append(ex)

    splits = {name: [] for name in RATIOS}
    for cat, items in by_cat.items():
        rng.shuffle(items)
        n_val = round(len(items) * RATIOS["validation"])
        n_test = round(len(items) * RATIOS["test"])
        splits["validation"] += items[:n_val]
        splits["test"] += items[n_val:n_val + n_test]
        splits["training"] += items[n_val + n_test:]

    for name, items in splits.items():
        rng.shuffle(items)
        write_jsonl(FINAL_DIR / f"{name}.jsonl",
                    [{"messages": ex["messages"]} for ex in items],
                    bom=(name != "test"))

    # no ticket may appear in two splits
    ids = [ex["ticket_id"] for items in splits.values() for ex in items]
    assert len(ids) == len(set(ids)), "ticket leaked across splits"

    report = ["# Step 6 - Split", "",
              "| category | " + " | ".join(splits) + " |",
              "|---|" + "---:|" * len(splits)]
    counts = {n: Counter(ex["category"] for ex in s) for n, s in splits.items()}
    for cat in CATEGORIES:
        report.append(f"| {cat} | " + " | ".join(str(counts[n][cat]) for n in splits) + " |")
    report.append("| **total** | " + " | ".join(f"**{len(s)}**" for s in splits.values()) + " |")
    report += ["", f"Files written to `{FINAL_DIR}`"]
    write_report("06_split.md", report)


if __name__ == "__main__":
    main()

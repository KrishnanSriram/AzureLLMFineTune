"""
STEP 4 - Label: map messy human tags and fields onto a clean target schema.

The labels come from support agents - they are the "ground truth" - but
agents typed them freely. This step:

  1. Maps each agent tag onto one of 5 canonical categories
     ("safety issue!!" -> SAFETY, "RMA" -> RETURN). Unmappable tags
     (blank, "Billing", "spam") are rejected, not guessed.
  2. Derives priority from category with a fixed business rule.
  3. Normalizes the product: use the product field if filled, otherwise
     find a known product name in the text, otherwise UNKNOWN. Teaching the
     model to say UNKNOWN is better than teaching it to guess.
  4. Sanity-checks the human label: if the text is clearly about a safety
     problem but the tag says otherwise, the row goes to a review queue
     instead of into training. A handful of mislabeled safety tickets can
     teach the model to downgrade real emergencies.

Input:  data/interim/03_redacted.csv
Output: data/interim/04_labeled.csv
        data/interim/04_rejected.csv     (no usable label)
        data/interim/04_needs_review.csv (label conflicts with text)
        reports/04_label.md
"""
import re
from collections import Counter

from common import read_csv, table, write_csv, write_report
from config import (INTERIM_DIR, PRIORITY_BY_CATEGORY, PRODUCT_ALIASES,
                    SAFETY_KEYWORDS, TAG_TO_CATEGORY, UNKNOWN_PRODUCT)

IN = INTERIM_DIR / "03_redacted.csv"
OUT = INTERIM_DIR / "04_labeled.csv"
REJECTED = INTERIM_DIR / "04_rejected.csv"
REVIEW = INTERIM_DIR / "04_needs_review.csv"

# longest alias first so "cityglide e2" wins over "cityglide"
_ALIASES = sorted(((a, canon) for canon, al in PRODUCT_ALIASES.items() for a in al),
                  key=lambda x: -len(x[0]))
_SAFETY_RE = re.compile(r"\b(" + "|".join(map(re.escape, SAFETY_KEYWORDS)) + r")\b", re.I)


def normalize_tag(tag):
    key = re.sub(r"[^a-z ]", "", tag.lower()).strip()
    return TAG_TO_CATEGORY.get(key)


def normalize_product(field, text):
    for source in (field, text):
        s = source.lower()
        for alias, canon in _ALIASES:
            if re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", s):
                return canon
    return UNKNOWN_PRODUCT


def main():
    rows = read_csv(IN)
    labeled, rejected, review = [], [], []
    tag_map = Counter()

    for r in rows:
        category = normalize_tag(r["agent_tag"])
        tag_map[f"{r['agent_tag'] or '(blank)'} -> {category or 'REJECT'}"] += 1
        if category is None:
            rejected.append({**r, "reason": f"unmappable tag '{r['agent_tag']}'"})
            continue

        product = normalize_product(r["product"], r["text"])
        row = {**r, "category": category,
               "priority": PRIORITY_BY_CATEGORY[category], "product": product}

        hit = _SAFETY_RE.search(r["text"])
        if hit and category != "SAFETY":
            review.append({**row, "reason": f"mentions '{hit.group(0)}' but tagged {category}"})
            continue
        labeled.append(row)

    fields = ["ticket_id", "channel", "subject", "text", "category", "priority", "product"]
    write_csv(OUT, labeled, fields)
    write_csv(REJECTED, rejected, list(rows[0]) + ["reason"])
    write_csv(REVIEW, review, fields + ["reason"])

    report = ["# Step 4 - Label", "",
              f"- Rows in: **{len(rows)}**",
              f"- Labeled: **{len(labeled)}**",
              f"- Rejected (no usable label): {len(rejected)}",
              f"- Sent to human review (label conflicts with text): {len(review)}", "",
              "## Category distribution"] + table(Counter(r["category"] for r in labeled))
    report += ["", "## Product distribution"] + table(Counter(r["product"] for r in labeled))
    report += ["", "## Tag mapping applied"] + table(tag_map, ("raw tag -> category", "rows"))
    if review:
        report += ["", "## Review queue sample", "| ticket | reason | text |", "|---|---|---|"]
        report += [f"| {r['ticket_id']} | {r['reason']} | {r['text'][:80]} |" for r in review[:5]]
    write_report("04_label.md", report)


if __name__ == "__main__":
    main()

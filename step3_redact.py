"""
STEP 3 - Redact personal data.

Anything you upload for fine-tuning can be memorized by the model and
repeated to someone else later. Personal data goes before training, not
after.

  * email addresses  -> [EMAIL]
  * phone numbers    -> [PHONE]
  * customer's name  -> [NAME]   (we know it from the ticket's own name column)
  * order numbers    -> [ORDER_ID] (not personal, but useless noise for triage)

Then the name/email columns are dropped entirely.

Regex redaction is a baseline. For real customer data, add a dedicated PII
service (e.g. Azure AI Language PII detection) and spot-check the output.

Input:  data/interim/02_clean.csv
Output: data/interim/03_redacted.csv, reports/03_redact.md
"""
import re
from collections import Counter

from common import EMAIL_RE, ORDER_RE, PHONE_RE, read_csv, write_csv, write_report
from config import INTERIM_DIR

IN = INTERIM_DIR / "02_clean.csv"
OUT = INTERIM_DIR / "03_redacted.csv"


def redact(text, full_name, counts):
    def sub(pattern, token, s):
        s, n = pattern.subn(token, s)
        counts[token] += n
        return s

    text = sub(EMAIL_RE, "[EMAIL]", text)
    text = sub(PHONE_RE, "[PHONE]", text)
    text = sub(ORDER_RE, "[ORDER_ID]", text)
    for part in full_name.split():
        if len(part) > 1:
            text = sub(re.compile(rf"\b{re.escape(part)}\b", re.I), "[NAME]", text)
    return text


def main():
    rows = read_csv(IN)
    counts = Counter()
    examples = []
    for r in rows:
        original = r["text"]
        r["text"] = redact(original, r["customer_name"], counts)
        if r["text"] != original and len(examples) < 3:
            examples.append((original, r["text"]))

    fields = ["ticket_id", "channel", "subject", "text", "agent_tag", "product"]
    write_csv(OUT, rows, fields)

    report = ["# Step 3 - Redact personal data", "",
              f"- Rows: **{len(rows)}**",
              "- Dropped columns: customer_name, customer_email", "",
              "## Replacements", "| token | count |", "|---|---:|"]
    report += [f"| {k} | {v} |" for k, v in counts.most_common()]
    for before, after in examples:
        report += ["", "```", f"before: {before}", f"after:  {after}", "```"]
    write_report("03_redact.md", report)


if __name__ == "__main__":
    main()

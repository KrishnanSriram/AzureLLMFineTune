"""
STEP 1 - Profile the raw data before touching it.

You can't clean what you haven't measured. This step changes nothing; it
answers "what am I dealing with?" and becomes the baseline you compare
every later step against.

Input:  data/raw/helpdesk_export.csv
Output: reports/01_profile.md
"""
from collections import Counter

from common import EMAIL_RE, PHONE_RE, read_csv, table, write_report
from config import RAW_FILE


def main():
    rows = read_csv(RAW_FILE)
    n = len(rows)
    cols = list(rows[0])

    ids = Counter(r["ticket_id"] for r in rows)
    bodies = Counter(r["body"].strip().lower() for r in rows if r["body"].strip())

    out = [f"# Step 1 - Raw data profile", "",
           f"- Rows: **{n}**",
           f"- Columns: {', '.join(cols)}",
           f"- Duplicate ticket_ids: {sum(c - 1 for c in ids.values() if c > 1)}",
           f"- Duplicate bodies (same text, any id): {sum(c - 1 for c in bodies.values() if c > 1)}",
           f"- Empty bodies: {sum(1 for r in rows if not r['body'].strip())}",
           f"- Bodies containing HTML: {sum(1 for r in rows if '<p>' in r['body'] or '<br>' in r['body'])}",
           f"- Bodies containing an email address: {sum(1 for r in rows if EMAIL_RE.search(r['body']))}",
           f"- Bodies containing a phone number: {sum(1 for r in rows if PHONE_RE.search(r['body']))}",
           f"- Blank product field: {sum(1 for r in rows if not r['product'].strip())}",
           "", "## Missing values per column", "| column | blank | % |", "|---|---:|---:|"]
    for c in cols:
        blank = sum(1 for r in rows if not r[c].strip())
        out.append(f"| {c} | {blank} | {blank / n:.0%} |")

    out += ["", "## Channel"] + table(Counter(r["channel"] for r in rows))
    out += ["", "## Status"] + table(Counter(r["status"] for r in rows))
    out += ["", f"## Agent tags as typed ({len(set(r['agent_tag'] for r in rows))} distinct)"]
    out += table(Counter(r["agent_tag"] for r in rows))
    out += ["", "## Product field as typed"] + table(Counter(r["product"] for r in rows))

    sample = next(r for r in rows if "<p>" in r["body"])
    out += ["", "## Example raw email body", "```", sample["body"], "```"]
    sample = next(r for r in rows if r["channel"] == "chat")
    out += ["", "## Example raw chat body", "```", sample["body"], "```"]

    write_report("01_profile.md", out)


if __name__ == "__main__":
    main()

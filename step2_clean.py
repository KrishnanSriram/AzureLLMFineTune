"""
STEP 2 - Clean: turn raw ticket bodies into the plain text a customer wrote.

  1. Drop exact duplicate rows (same ticket_id exported twice)
  2. Keep only finished tickets (solved/closed) - open tickets may carry a
     provisional tag that the agent hasn't confirmed yet
  3. Strip HTML and decode entities (&amp; -> &)
  4. Chat transcripts: keep only the customer's lines, drop timestamps
  5. Cut quoted reply chains ("On Mon ... wrote:" / "> ...") and signatures
  6. Normalize whitespace and typographic quotes
  7. Drop junk: empty, too short, test tickets, spam
  8. Drop near-duplicates (same customer text submitted twice)

Every dropped row is counted by reason, so the report shows exactly where
data went.

Input:  data/raw/helpdesk_export.csv
Output: data/interim/02_clean.csv, reports/02_clean.md
"""
import html
import re
from collections import Counter

from common import read_csv, write_csv, write_report
from config import INTERIM_DIR, RAW_FILE

OUT = INTERIM_DIR / "02_clean.csv"

TAG_RE = re.compile(r"<[^>]+>")
CHAT_LINE_RE = re.compile(r"^\[\d{1,2}:\d{2}\]\s*(Customer|Agent):\s*(.*)$")
QUOTE_START_RE = re.compile(r"^On .+wrote:\s*$")
SIGNATURE_MARKERS = ("--", "Sent from my", "Thanks,", "Regards,")
GREETING_RE = re.compile(r"^(hi|hello|hey)\b[^.!?]*[,!]?\s*$", re.I)
JUNK_PATTERNS = [re.compile(p, re.I) for p in
                 (r"\btest ticket\b", r"please ignore", r"buy cheap", r"followers")]
MIN_CHARS = 15


def strip_html(text):
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>\s*<p>", "\n\n", text)
    return html.unescape(TAG_RE.sub("", text))


def customer_lines_only(text):
    lines = text.splitlines()
    if not any(CHAT_LINE_RE.match(l) for l in lines):
        return text
    kept = []
    for l in lines:
        m = CHAT_LINE_RE.match(l)
        if m and m.group(1) == "Customer":
            kept.append(m.group(2))
    # "hi, I'm Maria" is small talk, not the problem - drop pure greetings
    kept = [k for k in kept if not re.match(r"(?i)^(hi|hello|hey)\b.{0,20}$", k)]
    return "\n".join(kept)


def cut_quotes_and_signature(text):
    kept = []
    for line in text.splitlines():
        s = line.strip()
        if QUOTE_START_RE.match(s) or s.startswith(">"):
            break                      # everything below is an old thread
        if s.startswith(SIGNATURE_MARKERS):
            break                      # everything below is the signature
        kept.append(line)
    return "\n".join(kept)


def normalize(text):
    text = (text.replace("’", "'").replace("‘", "'")
                .replace("“", '"').replace("”", '"'))
    lines = [l.strip() for l in text.splitlines()]
    lines = [l for l in lines if l and not GREETING_RE.match(l)]
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def dedupe_key(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def main():
    rows = read_csv(RAW_FILE)
    dropped = Counter()
    seen_ids, seen_text, out = set(), set(), []

    for r in rows:
        if r["ticket_id"] in seen_ids:
            dropped["duplicate ticket_id"] += 1
            continue
        seen_ids.add(r["ticket_id"])

        if r["status"] not in ("solved", "closed"):
            dropped["not finished (open)"] += 1
            continue

        text = strip_html(r["body"])
        text = customer_lines_only(text)
        text = cut_quotes_and_signature(text)
        text = normalize(text)

        if len(text) < MIN_CHARS:
            dropped["empty / too short"] += 1
            continue
        if any(p.search(text) for p in JUNK_PATTERNS):
            dropped["test or spam"] += 1
            continue
        key = dedupe_key(text)
        if key in seen_text:
            dropped["same text submitted twice"] += 1
            continue
        seen_text.add(key)

        out.append({"ticket_id": r["ticket_id"], "channel": r["channel"],
                    "customer_name": r["customer_name"],
                    "customer_email": r["customer_email"],
                    "subject": r["subject"].strip(), "text": text,
                    "agent_tag": r["agent_tag"], "product": r["product"]})

    write_csv(OUT, out)

    before = next(r for r in rows if "<p>" in r["body"] and r["status"] != "open")
    after = next((o for o in out if o["ticket_id"] == before["ticket_id"]), None)
    report = ["# Step 2 - Clean", "",
              f"- Rows in: **{len(rows)}**", f"- Rows out: **{len(out)}**", "",
              "## Dropped rows by reason", "| reason | rows |", "|---|---:|"]
    report += [f"| {k} | {v} |" for k, v in dropped.most_common()]
    report += ["", "## Before", "```", before["body"], "```",
               "## After", "```", after["text"] if after else "(dropped)", "```"]
    write_report("02_clean.md", report)


if __name__ == "__main__":
    main()

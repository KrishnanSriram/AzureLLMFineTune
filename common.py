"""Small I/O helpers shared by the step scripts (stdlib only)."""
import csv
import json
import re

from config import REPORT_DIR

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"(\+1[\s.-]?)?\(?\b\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")
ORDER_RE = re.compile(r"#?\bNW\d{5}\b")


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames=None):
    fieldnames = fieldnames or (list(rows[0]) if rows else [])
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def read_jsonl(path):
    with open(path, encoding="utf-8-sig") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, records, bom=False):
    # Azure's docs ask for UTF-8 *with* a byte-order mark on uploaded files.
    with open(path, "w", encoding="utf-8-sig" if bom else "utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_report(name, lines):
    path = REPORT_DIR / name
    text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")
    print(text)
    return path


def table(counter, header=("value", "count")):
    rows = [f"| {header[0]} | {header[1]} |", "|---|---:|"]
    rows += [f"| {k if k != '' else '(blank)'} | {v} |" for k, v in counter.most_common()]
    return rows

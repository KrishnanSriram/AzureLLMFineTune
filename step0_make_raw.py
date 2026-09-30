"""
STEP 0 - Simulate a raw helpdesk export.

In a real project this file comes from your ticketing system (Zendesk,
ServiceNow, Freshdesk...). We don't have one, so we fabricate an export that
has the same problems real exports have:

  * HTML in email bodies, email signatures, quoted reply chains
  * chat transcripts where only some lines are the customer
  * personal data (names, emails, phone numbers) inside the text
  * the same ticket exported twice, and customers who submit twice
  * test tickets, spam, empty bodies, still-open tickets
  * inconsistent agent tags ("Safety", "safety issue!!", "wrnty", "RMA")
  * product names spelled a dozen ways, product field often blank
  * a few tickets the agent tagged wrong

Output: data/raw/helpdesk_export.csv
"""
import csv
import random
from datetime import datetime, timedelta

from config import RAW_FILE, SEED

rng = random.Random(SEED)
N_TICKETS = 520

FIRST = ["Maria", "James", "Priya", "Chen", "Olivia", "Ahmed", "Sofia", "Liam",
         "Aisha", "Noah", "Elena", "Kenji", "Grace", "Mateo", "Zoe", "Ravi"]
LAST = ["Garcia", "Smith", "Patel", "Wei", "Johnson", "Khan", "Rossi", "Brown",
        "Okafor", "Miller", "Novak", "Tanaka", "Lee", "Silva", "Dubois", "Iyer"]

# How customers actually write product names (not the canonical form)
PRODUCT_SPELLINGS = {
    "Trailblazer 29": ["Trailblazer 29", "trailblazer29", "TB-29", "Trail Blazer 29", "Trailblazer 29er"],
    "CityGlide E2": ["CityGlide E2", "city glide e2", "CityGlide", "E2 ebike", "City Glide"],
    "Summit Pro Carbon": ["Summit Pro Carbon", "summit pro", "Summit Carbon"],
    "KidRider 16": ["KidRider 16", "kid rider 16", "KidRider", "kids bike 16"],
    "UrbanFold Mini": ["UrbanFold Mini", "urban fold mini", "UrbanFold", "folding mini"],
}

# True intent -> message templates ({p} = product as the customer wrote it)
MESSAGES = {
    "SAFETY": [
        "The brakes on my {p} stopped working while I was going downhill.",
        "I found a crack in the frame of my {p} near the seat post. Is it safe to ride?",
        "The battery on my {p} got really hot and started smoking in the garage.",
        "The handlebar on my {p} came loose mid-ride and I almost crashed.",
        "Front brake on the {p} feels like it's not grabbing at all, really scary.",
        "My son's {p} has a cracked fork, he was riding it yesterday!",
    ],
    "WARRANTY": [
        "My {p} is 8 months old and the gears keep slipping. Is this covered?",
        "Paint on my {p} is peeling after only 3 months, can I get it fixed under warranty?",
        "The motor on my {p} makes a grinding noise. It's still under warranty I think.",
        "Chain on my {p} snapped after two weeks of normal commuting.",
        "The kickstand bolt on my {p} sheared off, bike is less than a year old.",
        "Rear derailleur on the {p} is bent out of the box basically, 5 months old.",
    ],
    "ORDER_STATUS": [
        "Where is my {p}? I ordered it 10 days ago and haven't heard anything.",
        "Can you tell me when my {p} order will ship?",
        "Tracking for my {p} hasn't updated in 4 days.",
        "Got a delivery notification for the {p} but nothing showed up at my door.",
        "Ordered a {p} for my daughter's birthday, is it going to arrive by Friday?",
        "My {p} order says processing for a week now, what's going on?",
    ],
    "RETURN": [
        "I want to return my {p}, it's too big for me.",
        "How do I send back the {p}? Changed my mind.",
        "The {p} isn't what I expected. Can I get a refund?",
        "I'd like to exchange my {p} for a smaller size.",
        "Bought the {p} as a gift but they already have one, how do returns work?",
        "Please start a return for the {p}, it doesn't fit in my apartment.",
    ],
    "GENERAL": [
        "What tire pressure should I run on my {p}?",
        "Do you sell a rear rack that fits the {p}?",
        "How often should I get my {p} serviced?",
        "Is it ok to ride the {p} in the rain?",
        "What's the max rider weight for the {p}?",
        "Can I put a child seat on my {p}?",
    ],
}

# How agents tagged each intent (messy, inconsistent, sometimes blank)
AGENT_TAGS = {
    "SAFETY": ["Safety", "safety issue", "SAFETY!!", "Brake failure", "urgent safety", "safety concern"],
    "WARRANTY": ["Warranty", "warranty claim", "wrnty", "Defect", "defective part"],
    "ORDER_STATUS": ["Order Status", "where is my order", "WISMO", "shipping", "Tracking"],
    "RETURN": ["Return", "refund", "RMA", "exchange", "Returns"],
    "GENERAL": ["General", "question", "misc", "Product question", "how to"],
}

SUBJECTS = {
    "SAFETY": ["URGENT", "Safety problem", "Brakes!!", "Help", ""],
    "WARRANTY": ["Warranty question", "Defect", "Broken part", ""],
    "ORDER_STATUS": ["Where is my order", "Shipping", "Order update?", ""],
    "RETURN": ["Return", "Refund request", "Exchange", ""],
    "GENERAL": ["Question", "Quick question", "Accessories", ""],
}


def fake_person():
    first, last = rng.choice(FIRST), rng.choice(LAST)
    email = f"{first.lower()}.{last.lower()}{rng.randint(1, 99)}@example.com"
    phone = rng.choice(["({a}) {b}-{c}", "{a}-{b}-{c}", "+1 {a} {b} {c}"]).format(
        a=rng.randint(200, 989), b=rng.randint(200, 999), c=rng.randint(1000, 9999))
    return first, last, email, phone


def core_message(intent, product_text):
    msg = rng.choice(MESSAGES[intent]).format(p=product_text)
    if rng.random() < 0.3:
        msg += f" Order #NW{rng.randint(10000, 99999)}."
    return msg


def as_email(msg, first, last, phone):
    body = rng.choice(["Hi,", "Hello Northwind team,", "Hey there,", ""]) + "\n\n" + msg
    if rng.random() < 0.35:
        body += f"\n\nYou can call me at {phone}."
    body += "\n\n" + rng.choice([
        f"--\n{first} {last}\n{phone}",
        f"Thanks,\n{first}",
        "Sent from my iPhone",
        f"Regards,\n{first} {last}",
    ])
    if rng.random() < 0.25:  # quoted reply chain from an earlier auto-response
        body += ("\n\nOn Mon, Mar 3, 2026 at 9:14 AM Northwind Support "
                 "<support@northwindbikes.example> wrote:\n"
                 "> Thanks for contacting Northwind Bikes.\n"
                 "> We received your request and will reply soon.")
    if rng.random() < 0.5:  # some mail clients export HTML
        body = "<p>" + body.replace("&", "&amp;").replace("\n\n", "</p><p>").replace("\n", "<br>") + "</p>"
    return body


def as_chat(msg, first):
    t = datetime(2026, 3, 1, 10, 0)
    lines = [
        f"[{t:%H:%M}] Agent: Hi, thanks for contacting Northwind Bikes! How can I help?",
        f"[{(t + timedelta(minutes=1)):%H:%M}] Customer: hi, I'm {first}",
        f"[{(t + timedelta(minutes=2)):%H:%M}] Customer: {msg}",
        f"[{(t + timedelta(minutes=3)):%H:%M}] Agent: Sorry to hear that, let me check.",
    ]
    return "\n".join(lines)


def make_ticket(i):
    intent = rng.choice(list(MESSAGES))
    product = rng.choice(list(PRODUCT_SPELLINGS))
    first, last, email, phone = fake_person()

    # ~8% of customers never mention which bike
    product_text = rng.choice(PRODUCT_SPELLINGS[product]) if rng.random() > 0.08 else "bike"
    msg = core_message(intent, product_text)

    channel = rng.choices(["email", "web", "chat"], weights=[5, 3, 2])[0]
    if channel == "email":
        body = as_email(msg, first, last, phone)
    elif channel == "chat":
        body = as_chat(msg, first)
    else:
        body = msg
        if rng.random() < 0.3:
            body += f" My email is {email}."
        if rng.random() < 0.25:
            body = f"My name is {first} {last}. " + body

    tag = rng.choice(AGENT_TAGS[intent])
    if rng.random() < 0.04:            # agent picked the wrong tag
        tag = rng.choice(AGENT_TAGS["GENERAL"])
    if rng.random() < 0.03:            # agent never tagged it
        tag = ""

    # product dropdown filled in only about half the time, inconsistently
    product_field = rng.choice([product, product.upper(), product.lower(), ""]) \
        if product_text != "bike" else ""

    return {
        "ticket_id": f"T{100000 + i}",
        "created_at": (datetime(2026, 1, 1) + timedelta(minutes=rng.randint(0, 120000))).isoformat(),
        "channel": channel,
        "customer_name": f"{first} {last}",
        "customer_email": email,
        "subject": rng.choice(SUBJECTS[intent]),
        "body": body,
        "agent_tag": tag,
        "product": product_field,
        "status": rng.choices(["solved", "closed", "open"], weights=[6, 3, 1])[0],
    }


def junk_ticket(i):
    kind = rng.choice(["test", "spam", "empty", "billing"])
    body = {
        "test": "test ticket please ignore",
        "spam": "Buy cheap followers now!!! visit cheap-followers.example",
        "empty": "",
        "billing": "I was charged twice on my credit card statement, please fix.",
    }[kind]
    tag = {"test": "", "spam": "spam", "empty": "", "billing": "Billing"}[kind]
    first, last, email, _ = fake_person()
    return {"ticket_id": f"T{100000 + i}", "created_at": "2026-02-01T12:00:00",
            "channel": "web", "customer_name": f"{first} {last}",
            "customer_email": email, "subject": "", "body": body,
            "agent_tag": tag, "product": "", "status": "solved"}


def main():
    rows = []
    for i in range(N_TICKETS):
        rows.append(junk_ticket(i) if rng.random() < 0.05 else make_ticket(i))

    # customer submits the same message twice (new ticket id)
    for r in rng.sample(rows, 15):
        dup = dict(r, ticket_id=f"T{900000 + len(rows)}")
        rows.append(dup)
    # export glitch: identical rows appear twice
    rows += [dict(r) for r in rng.sample(rows, 20)]
    rng.shuffle(rows)

    with open(RAW_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"[step0] wrote {len(rows)} raw tickets -> {RAW_FILE}")


if __name__ == "__main__":
    main()

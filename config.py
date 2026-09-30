"""
Shared configuration for the data pipeline.

Everything that encodes a *business decision* lives here, so the step
scripts stay generic:
  - the canonical label set and how messy agent tags map onto it
  - how priority is derived from category
  - product names and their many spellings
  - the fixed reply the model should learn for each category
  - the system prompt the model is trained (and later called) with
"""
from pathlib import Path

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"          # untouched source exports
INTERIM_DIR = ROOT / "data" / "interim"  # one file per pipeline step
FINAL_DIR = ROOT / "data" / "final"      # files you upload to Azure
REPORT_DIR = ROOT / "reports"            # human-readable step reports

RAW_FILE = RAW_DIR / "helpdesk_export.csv"

for d in (RAW_DIR, INTERIM_DIR, FINAL_DIR, REPORT_DIR):
    d.mkdir(parents=True, exist_ok=True)

SEED = 42

# ------------------------------------------------------- prompt / target
SYSTEM_PROMPT = (
    "You are the Northwind Bikes support triage assistant. "
    "Reply ONLY with JSON containing category, priority, product, reply."
)

# Canonical label set -> priority (business rule, not learned from data)
PRIORITY_BY_CATEGORY = {
    "SAFETY": "P1",
    "WARRANTY": "P2",
    "ORDER_STATUS": "P3",
    "RETURN": "P3",
    "GENERAL": "P4",
}
CATEGORIES = list(PRIORITY_BY_CATEGORY)

# Free-text tags agents typed in the helpdesk -> canonical category.
# Keys are compared after lowercasing and stripping punctuation.
TAG_ALIASES = {
    "SAFETY": ["safety", "safety issue", "safety concern", "brake failure",
               "urgent safety", "injury", "dangerous"],
    "WARRANTY": ["warranty", "warranty claim", "wrnty", "defect",
                 "defective part", "manufacturing defect"],
    "ORDER_STATUS": ["order status", "where is my order", "wismo", "shipping",
                     "delivery", "tracking", "shipping delay"],
    "RETURN": ["return", "returns", "refund", "rma", "exchange",
               "return request"],
    "GENERAL": ["general", "question", "general question", "misc",
                "product question", "how to", "info"],
}
TAG_TO_CATEGORY = {alias: cat for cat, aliases in TAG_ALIASES.items()
                   for alias in aliases}

# Canonical product name -> spellings seen in the wild (lowercase)
PRODUCT_ALIASES = {
    "Trailblazer 29": ["trailblazer 29", "trailblazer29", "trail blazer 29",
                       "tb-29", "tb29", "trailblazer 29er"],
    "CityGlide E2": ["cityglide e2", "city glide e2", "cityglide",
                     "city glide", "e2 ebike", "glide e2"],
    "Summit Pro Carbon": ["summit pro carbon", "summit pro", "summit carbon"],
    "KidRider 16": ["kidrider 16", "kid rider 16", "kidrider", "kids bike 16"],
    "UrbanFold Mini": ["urbanfold mini", "urban fold mini", "urbanfold",
                       "folding mini"],
}
UNKNOWN_PRODUCT = "UNKNOWN"

# Words that almost always mean a safety problem. Used as a sanity check
# on human labels (step 4), not as the labeler itself.
SAFETY_KEYWORDS = ["brake", "brakes", "crack", "cracked", "smoke", "smoking",
                   "fire", "overheat", "came loose", "crashed", "injured"]

# The reply we want the model to produce for each category.
REPLY_TEMPLATES = {
    "SAFETY": "Please stop riding your {p} immediately. A safety specialist will call you within 2 hours.",
    "WARRANTY": "Your {p} is covered by our 2-year warranty. We've emailed you a prepaid shipping label.",
    "ORDER_STATUS": "We're checking the shipment status of your {p} and will email tracking details within 24 hours.",
    "RETURN": "You can return your {p} within 30 days for a full refund. A return label is on its way.",
    "GENERAL": "Great question about your {p}! Our product guide at northwindbikes.example/help covers this.",
}

# Rough training price for estimating cost in step 7 (USD per 1M tokens).
# Illustrative only -- check the Azure OpenAI pricing page for current rates.
TRAINING_PRICE_PER_1M = {"GlobalStandard": 1.50, "developerTier": 0.75}
EPOCHS = 3

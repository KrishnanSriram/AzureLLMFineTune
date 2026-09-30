# From raw support tickets to a fine-tuned model

A step-by-step data engineering pipeline that turns a messy helpdesk export
into Azure OpenAI fine-tuning files, then automates training and deployment
on Microsoft Foundry.

```
helpdesk_export.csv                        (raw, 555 rows)
  │ step1_profile   measure it             -> reports/01_profile.md
  │ step2_clean     HTML, chat, signatures, junk, duplicates
  ▼                                        -> data/interim/02_clean.csv     (403 rows)
  │ step3_redact    names, emails, phones, order ids
  ▼                                        -> data/interim/03_redacted.csv
  │ step4_label     messy tags -> 5 categories, priority rule, product names,
  │                 conflicting labels to a review queue
  ▼                                        -> data/interim/04_labeled.csv   (392 rows)
  │ step5_to_chat   system / user / assistant messages
  ▼                                        -> data/interim/05_examples.jsonl
  │ step6_split     stratified 70 / 15 / 15
  ▼                                        -> data/final/{training,validation,test}.jsonl
  │ step7_validate  quality gate (schema, PII, leakage, tokens, cost)
  ▼                                        -> reports/07_validate.md  PASS / FAIL
  │ finetune.py     validate -> upload -> train -> metrics -> Developer deploy
  ▼
  test_model.py     base vs fine-tuned on the unseen test split
```

Every step reads the previous step's file and writes its own, plus a short
report in `reports/` with counts and a before/after sample. You can open
any intermediate file to see exactly what that step changed.

## Run it

```bash
pip install openai tiktoken          # or: uv add openai tiktoken

python run_pipeline.py               # steps 0-7, stops if validation fails
python finetune.py --tf-dir ../foundry-tf     # upload, train, deploy (~30-90 min)

export AZURE_OPENAI_ENDPOINT=$(terraform -chdir=../foundry-tf output -raw endpoint)
export AZURE_OPENAI_API_KEY=$(terraform -chdir=../foundry-tf output -raw api_key)
export BASE_DEPLOYMENT=gpt-4.1-nano-base FT_DEPLOYMENT=gpt-4.1-nano-ft
python test_model.py
```

`finetune.py` needs `az login` for the deploy step, and saves progress to
`finetune_state.json`, so rerunning it resumes instead of retraining.

## Using your own data

Replace `data/raw/helpdesk_export.csv` with a real export that has the same
columns, then run `python run_pipeline.py --from 1`. All business rules
(categories, tag aliases, product spellings, reply templates, priority)
live in `config.py`.

## Files

| file | purpose |
|---|---|
| `config.py` | business rules and paths - the only file you edit for a new use case |
| `common.py` | CSV/JSONL helpers and PII regexes |
| `step0_make_raw.py` | generates a realistic, messy fake export (skip with real data) |
| `step1_profile.py` ... `step7_validate.py` | one transformation each |
| `run_pipeline.py` | runs steps in order, stops on failure |
| `finetune.py` | automation: upload, train, poll, save metrics, deploy |
| `test_model.py` | before/after evaluation |

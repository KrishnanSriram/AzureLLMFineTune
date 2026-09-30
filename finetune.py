"""
STEP 8 - Automate the fine-tuning run: validate -> upload -> train -> deploy.

    python finetune.py --tf-dir ../foundry-tf      # read endpoint/key/RG from Terraform
    python finetune.py                             # or use environment variables

Environment variables (used when --tf-dir isn't given):
    AZURE_OPENAI_ENDPOINT   https://<name>.openai.azure.com/
    AZURE_OPENAI_API_KEY
    AZURE_RESOURCE_GROUP    needed only for the deploy step
    FOUNDRY_NAME            needed only for the deploy step
    AZURE_SUBSCRIPTION_ID   optional; taken from `az account show` if unset

What it does:
  1. Re-runs the step 7 quality gate - never pays for training on bad data
  2. Uploads training.jsonl + validation.jsonl and waits until Azure has
     processed them
  3. Creates a supervised fine-tuning job on gpt-4.1-nano (Developer
     training by default - the cheapest option) and streams its events
  4. Saves the training metrics CSV to reports/
  5. Deploys the fine-tuned model as a *Developer tier* deployment
     (per-token billing, no hourly hosting fee, auto-deleted after 24 h)

Progress is saved to finetune_state.json after every stage. If you stop the
script (Ctrl-C) or it fails, run it again and it picks up where it left off
instead of uploading or training twice. Delete the file to start fresh.

Requires: pip install openai   and the Azure CLI logged in (az login) for deploy.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

from openai import OpenAI

from config import EPOCHS, FINAL_DIR, REPORT_DIR, ROOT

STATE_FILE = ROOT / "finetune_state.json"
BASE_MODEL = "gpt-4.1-nano-2025-04-14"
ARM = "https://management.azure.com"
ARM_API_VERSION = "2025-07-01-preview"
TERMINAL_JOB_STATES = {"succeeded", "failed", "cancelled"}


# ------------------------------------------------------------ helpers
def load_state():
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def sh(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


def settings_from(tf_dir):
    cfg = {
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "resource_group": os.getenv("AZURE_RESOURCE_GROUP"),
        "foundry_name": os.getenv("FOUNDRY_NAME"),
        "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
    }
    if tf_dir:
        out = json.loads(sh("terraform", f"-chdir={tf_dir}", "output", "-json"))
        cfg.update(endpoint=out["endpoint"]["value"], api_key=out["api_key"]["value"],
                   resource_group=out["resource_group"]["value"],
                   foundry_name=out["foundry_name"]["value"])
    missing = [k for k in ("endpoint", "api_key") if not cfg[k]]
    if missing:
        sys.exit(f"Missing settings: {missing}. Pass --tf-dir or set the env vars.")
    return cfg


# ------------------------------------------------------------ stages
def validate():
    log("Stage 1/5: running the step 7 quality gate")
    import step7_validate
    try:
        step7_validate.main()
    except SystemExit as e:
        if e.code:
            sys.exit("Validation failed - fix the data before training.")


def upload(client, state):
    log("Stage 2/5: uploading files")
    for split in ("training", "validation"):
        key = f"{split}_file_id"
        if key not in state:
            with open(FINAL_DIR / f"{split}.jsonl", "rb") as f:
                state[key] = client.files.create(file=f, purpose="fine-tune").id
            save_state(state)
            log(f"  uploaded {split}.jsonl -> {state[key]}")
        while True:
            status = client.files.retrieve(state[key]).status
            if status == "processed":
                break
            if status in ("error", "failed", "deleted"):
                sys.exit(f"File {state[key]} status {status}. Check it in the Foundry portal.")
            log(f"  {split} file status: {status} ...")
            time.sleep(10)
    log("  both files processed")


def train(client, state, training_type, suffix, poll_seconds):
    log("Stage 3/5: fine-tuning")
    if "job_id" not in state:
        job = client.fine_tuning.jobs.create(
            model=BASE_MODEL,
            training_file=state["training_file_id"],
            validation_file=state["validation_file_id"],
            suffix=suffix,
            seed=42,
            method={"type": "supervised",
                    "supervised": {"hyperparameters": {"n_epochs": EPOCHS}}},
            extra_body={"trainingType": training_type},
        )
        state["job_id"] = job.id
        save_state(state)
        log(f"  created job {job.id} ({training_type}, {EPOCHS} epochs)")
    else:
        log(f"  resuming job {state['job_id']}")

    seen_events = set()
    while True:
        job = client.fine_tuning.jobs.retrieve(state["job_id"])
        events = client.fine_tuning.jobs.list_events(state["job_id"], limit=20).data
        for ev in reversed(events):                      # API returns newest first
            if ev.id not in seen_events:
                seen_events.add(ev.id)
                log(f"  event: {ev.message}")
        if job.status in TERMINAL_JOB_STATES:
            break
        log(f"  status: {job.status} (next check in {poll_seconds}s, Ctrl-C is safe)")
        time.sleep(poll_seconds)

    if job.status != "succeeded":
        sys.exit(f"Job ended with status {job.status}: {job.error}")
    state["fine_tuned_model"] = job.fine_tuned_model
    save_state(state)
    log(f"  succeeded -> {job.fine_tuned_model}")
    return job


def save_metrics(client, job):
    log("Stage 4/5: saving training metrics")
    if not job.result_files:
        log("  no result file on the job; skipping")
        return
    csv_bytes = client.files.content(job.result_files[0]).read()
    path = REPORT_DIR / "08_training_results.csv"
    path.write_bytes(csv_bytes)
    lines = csv_bytes.decode().strip().splitlines()
    log(f"  saved {path.name}")
    log(f"  columns: {lines[0]}")
    log(f"  final:   {lines[-1]}")


def deploy(cfg, state, deployment_name):
    log("Stage 5/5: deploying as Developer tier")
    if not (cfg["resource_group"] and cfg["foundry_name"]):
        log("  AZURE_RESOURCE_GROUP / FOUNDRY_NAME not set - skipping deploy. "
            "Deploy from the portal with deployment type 'Developer'.")
        return
    sub = cfg["subscription_id"] or sh("az", "account", "show", "--query", "id", "-o", "tsv")
    token = sh("az", "account", "get-access-token", "--resource", ARM + "/",
               "--query", "accessToken", "-o", "tsv")
    url = (f"{ARM}/subscriptions/{sub}/resourceGroups/{cfg['resource_group']}"
           f"/providers/Microsoft.CognitiveServices/accounts/{cfg['foundry_name']}"
           f"/deployments/{deployment_name}?api-version={ARM_API_VERSION}")
    body = {"sku": {"name": "developertier", "capacity": 50},
            "properties": {"model": {"format": "OpenAI",
                                     "name": state["fine_tuned_model"],
                                     "version": "1"}}}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def call(method, data=None):
        req = urllib.request.Request(url, method=method, headers=headers,
                                     data=json.dumps(data).encode() if data else None)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read() or "{}")
        except urllib.error.HTTPError as e:
            sys.exit(f"Deploy {method} failed ({e.code}): {e.read().decode()}")

    call("PUT", body)
    while True:
        prov = call("GET").get("properties", {}).get("provisioningState")
        if prov == "Succeeded":
            break
        if prov in ("Failed", "Canceled"):
            sys.exit(f"Deployment {prov}")
        log(f"  deployment state: {prov} ...")
        time.sleep(15)
    state["deployment"] = deployment_name
    save_state(state)
    log(f"  deployed '{deployment_name}' (auto-deletes after 24 hours)")


# ------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--tf-dir", help="Terraform folder to read outputs from")
    ap.add_argument("--training-type", default="developerTier",
                    help="developerTier (cheapest), GlobalStandard, or Standard")
    ap.add_argument("--suffix", default="nwbikes", help="name tag for the model (no dots)")
    ap.add_argument("--deployment-name", default="gpt-4.1-nano-ft")
    ap.add_argument("--poll-seconds", type=int, default=60)
    ap.add_argument("--skip-deploy", action="store_true")
    args = ap.parse_args()

    cfg = settings_from(args.tf_dir)
    client = OpenAI(api_key=cfg["api_key"],
                    base_url=cfg["endpoint"].rstrip("/") + "/openai/v1/")
    state = load_state()

    if "job_id" not in state:
        validate()
        upload(client, state)
    job = train(client, state, args.training_type, args.suffix, args.poll_seconds)
    save_metrics(client, job)
    if not args.skip_deploy and "deployment" not in state:
        deploy(cfg, state, args.deployment_name)

    print("\nDone. To compare base vs fine-tuned:")
    print(f"  export FT_DEPLOYMENT={state.get('deployment', args.deployment_name)}")
    print(f"  python test_model.py {FINAL_DIR / 'test.jsonl'}")


if __name__ == "__main__":
    main()

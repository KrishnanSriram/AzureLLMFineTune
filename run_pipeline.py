"""
Run the whole data pipeline, raw export -> validated JSONL, in order.

    python run_pipeline.py              # steps 0-7 (regenerates the fake raw data)
    python run_pipeline.py --from 1     # start at step 1, e.g. with your own raw CSV

Stops at the first failing step (step 7 fails if validation finds problems).
Then run finetune.py to upload, train and deploy.
"""
import argparse
import importlib
import sys

STEPS = ["step0_make_raw", "step1_profile", "step2_clean", "step3_redact",
         "step4_label", "step5_to_chat", "step6_split", "step7_validate"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", type=int, default=0,
                    help="first step to run (0-7)")
    args = ap.parse_args()

    for i, name in enumerate(STEPS[args.start:], start=args.start):
        print(f"\n{'=' * 70}\n>>> STEP {i}: {name}\n{'=' * 70}")
        try:
            importlib.import_module(name).main()
        except SystemExit as e:
            if e.code:
                print(f"\nPipeline stopped: {name} failed.")
                sys.exit(e.code)
    print("\nPipeline complete. Upload files are in data/final/. Next: python finetune.py")


if __name__ == "__main__":
    main()

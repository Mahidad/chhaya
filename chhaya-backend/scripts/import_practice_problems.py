"""
Command-line front end for the practice problem bank import.

YOU USUALLY DON'T NEED TO RUN THIS. A development server that finds the bank
empty imports it automatically on startup (see maybe_import_in_background in
app/services/practice_import_service.py).
Reach for this script when you want to import without booting the API, force a
top-up after a dataset gains rows, or try a different dataset than the one in
.env.

USAGE:
    # import PRACTICE_DATASET_SLUG, same as the server would
    python scripts/import_practice_problems.py

    # try a different dataset without editing .env
    python scripts/import_practice_problems.py --kaggle owner/some-other-dataset

    # or point it at a CSV you downloaded yourself
    python scripts/import_practice_problems.py path/to/leetcode.csv

Downloading needs Kaggle API credentials -- either ~/.kaggle/kaggle.json or
KAGGLE_USERNAME + KAGGLE_KEY in the environment. Get a token from kaggle.com
-> Settings -> API -> Create New Token.

All the actual work (column aliasing, slug rules, the placeholder-row filter)
lives in app/services/practice_import_service.py so this script and the
startup bootstrap can't drift apart. Re-running is safe: rows are matched on
title_slug and skipped if already present.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services import practice_import_service  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import the practice problem bank. With no arguments, downloads "
        "the dataset named by PRACTICE_DATASET_SLUG in .env.",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("csv_path", nargs="?", help="path to a LeetCode problems CSV")
    source.add_argument(
        "--kaggle",
        metavar="DATASET_SLUG",
        help="override the configured dataset, e.g. owner/some-dataset",
    )
    args = parser.parse_args()

    try:
        result = practice_import_service.refresh_bank(
            trigger="manual", csv_path=args.csv_path, slug=args.kaggle
        )
    except practice_import_service.ImportError_ as exc:
        parser.error(str(exc))

    if result["status"] == "skipped":
        print(f"Nothing to do: {result['reason']}")
        return 0

    print(
        f"Imported {result['inserted']} new problems from {result['dataset']}. "
        f"Skipped {result['skipped']} already present. "
        f"{result['malformed']} rows unusable."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

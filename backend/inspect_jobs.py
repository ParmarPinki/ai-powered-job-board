import json
from pathlib import Path

DATA_PATH = Path("../data/jobs.json")


def inspect_jobs_file():
    raw_text = DATA_PATH.read_text(encoding="utf-8")

    try:
        jobs = json.loads(raw_text)
    except json.JSONDecodeError as error:
        print("Invalid JSON file")
        print(f"Error message: {error.msg}")
        print(f"Line: {error.lineno}")
        print(f"Column: {error.colno}")
        print(f"Character position: {error.pos}")

        start = max(error.pos - 500, 0)
        end = min(error.pos + 500, len(raw_text))

        print("\nText near error:")
        print(raw_text[start:end])
        return

    print("Valid JSON file")
    print(f"Total records: {len(jobs)}")

    if jobs:
        print("\nFirst record keys:")
        print(list(jobs[0].keys()))


if __name__ == "__main__":
    inspect_jobs_file()
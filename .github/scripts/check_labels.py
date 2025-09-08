#!/usr/bin/env python3
import json
import os
import sys
import logging
import subprocess

REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GITHUB_TOKEN"]
ISSUE_NUMBER = 60

required_labels = [
    "stable: Solutions QA tests passed",
    "stable: engineering manager approved",
    "stable: product manager approved",
    "stable: release notes curated",
]

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


def fetch_issue(issue_number: int) -> dict:
    logging.info(f"Fetching issue #{issue_number} from {REPO}")
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", REPO, "--json", "labels"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh issue view failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def comment_on_issue(issue_number: int, message: str) -> None:
    """Post a comment on the given issue."""
    logging.info(f"Posting comment to issue #{issue_number}: {message!r}")
    result = subprocess.run(
        [
            "gh",
            "issue",
            "comment",
            str(issue_number),
            "--repo",
            REPO,
            "--body",
            message,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh issue comment failed: {result.stderr.strip()}")
    logging.info("Comment posted successfully.")


def check_labels(issue_data: dict, required: list[str]) -> None:
    labels = [label["name"] for label in issue_data.get("labels", [])]
    logging.info(f"Labels on issue #{ISSUE_NUMBER}: {labels}")
    missing = [label for label in required if label not in labels]
    if missing:
        raise ValueError(f"Missing labels: {missing}")


def main():
    issue_data = fetch_issue(ISSUE_NUMBER)
    check_labels(issue_data, required_labels)
    logging.info("All required labels are present. Stable release approved!")
    comment_on_issue(ISSUE_NUMBER, "Released to stable")


if __name__ == "__main__":
    main()

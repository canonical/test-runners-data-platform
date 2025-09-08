#!/usr/bin/env python3
import os
import sys
import logging
import requests

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


def fetch_issue(issue_number: int):
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}"
    logging.info(f"Fetching issue #{issue_number} from {REPO}")
    resp = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
        },
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch issue #{issue_number}: {resp.status_code} {resp.text}"
        )
    return resp.json()


def comment_on_issue(issue_number: int, message: str) -> None:
    """Post a comment on the given issue."""
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}/comments"
    logging.info(f"Posting comment to issue #{issue_number}: {message!r}")
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
        },
        json={"body": message},
    )
    if resp.status_code != 201:
        raise RuntimeError(
            f"Failed to post comment: {resp.status_code} {resp.text}"
        )
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

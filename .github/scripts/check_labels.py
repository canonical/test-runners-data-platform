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
        logging.error(f"Failed to post comment: {resp.status_code} {resp.text}")
        sys.exit(1)
    else:
        logging.info("Comment posted successfully.")

def main():
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}"
    logging.info(f"Fetching issue #{ISSUE_NUMBER} from {REPO}")
    resp = requests.get(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json"
    })
    if resp.status_code != 200:
        logging.error(f"Failed to fetch issue #{ISSUE_NUMBER}: {resp.status_code} {resp.text}")
        sys.exit(1)

    data = resp.json()
    labels = [label["name"] for label in data.get("labels", [])]
    logging.info(f"Labels on issue #{ISSUE_NUMBER}: {labels}")

    missing = [label for label in required_labels if label not in labels]
    if not missing:
        logging.info("All required labels are present. Stable release approved!")
        comment_on_issue(ISSUE_NUMBER, "Released to stable: <release notes link>")
    else:
        logging.warning(f"Missing labels: {missing}")
        sys.exit(1)

if __name__ == "__main__":
    main()

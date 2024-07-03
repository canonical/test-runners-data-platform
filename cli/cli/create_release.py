import datetime
import os
import pathlib
import subprocess
import time

import requests
import requests.adapters
import urllib3
import urllib3.util


class GitHubRateLimitRetry(urllib3.util.Retry):
    """Infinite retry for GitHub REST API rate limit

    https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28#exceeding-the-rate-limit
    """

    def __init__(self, **kwargs):
        super().__init__(
            total=None,  # Infinite retry
            # Only retry on status code
            connect=0,
            read=0,
            redirect=0,
            other=0,
            allowed_methods=(
                *urllib3.util.Retry.DEFAULT_ALLOWED_METHODS,
                "POST",
                "PATCH",
            ),
            status_forcelist=(403, 429),
            **kwargs,
        )

    def get_retry_after(self, response: urllib3.BaseHTTPResponse) -> float | None:
        seconds = super().get_retry_after(response)
        if seconds:
            print(f"Rate limit exceeded. Sleeping for {int(seconds)} seconds")
        return seconds

    def sleep_for_retry(self, response: urllib3.BaseHTTPResponse) -> bool:
        # Sleep until x-ratelimit-reset
        if int(response.headers["x-ratelimit-remaining"]) == 0 and (
            reset := response.headers.get("x-ratelimit-reset")
        ):
            retry_time = datetime.datetime.fromtimestamp(
                float(reset), tz=datetime.timezone.utc
            )
            retry_delta = retry_time - datetime.datetime.now(tz=datetime.timezone.utc)
            seconds = max(retry_delta.total_seconds(), 0)
            print(f"Rate limit exceeded. Sleeping for {int(seconds)} seconds")
            time.sleep(seconds)
            return True
        # Sleep for/until retry-after
        if super().sleep_for_retry(response):
            return True
        # x-ratelimit-reset and retry-after headers missing
        print(
            "Rate limit exceeded. Sleeping for 60 seconds (rate limit headers missing)"
        )
        time.sleep(60)
        return True


def main():
    release_name = f"build-{int(time.time())}-v3"
    # Create git tag
    subprocess.run(["git", "tag", release_name], check=True)
    subprocess.run(["git", "push", "origin", release_name], check=True)

    session = requests.Session()
    session.mount(
        "https://", requests.adapters.HTTPAdapter(max_retries=GitHubRateLimitRetry())
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f'Bearer {os.environ["GH_TOKEN"]}',
    }
    # Create draft release
    # (Wait until all release files uploaded before marking as latest, non-draft release)
    response = session.post(
        f'https://api.github.com/repos/{os.environ["GITHUB_REPOSITORY"]}/releases',
        headers=headers,
        json={
            "tag_name": release_name,
            "target_commitish": os.environ["GITHUB_SHA"],
            "name": release_name,
            "draft": True,
            "make_latest": "false",
        },
    )
    response.raise_for_status()
    data = response.json()
    upload_url = data["upload_url"]
    release_id = data["id"]
    # Upload release files
    for path in pathlib.Path("~/release").expanduser().glob("*"):
        with path.open("rb") as file:
            session.post(
                upload_url,
                headers=headers,
                params={"name": path.name},
                data=file,
            )
    # Mark release as latest
    response = session.patch(
        f'https://api.github.com/repos/{os.environ["GITHUB_REPOSITORY"]}/releases/{release_id}',
        headers=headers,
        json={
            "draft": False,
            "make_latest": "true",
        },
    )
    response.raise_for_status()

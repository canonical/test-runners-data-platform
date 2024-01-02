import argparse
import dataclasses
import json
import os
import pathlib
import re
import subprocess

from . import charm


class IssueParsingError(ValueError):
    """Unexpected format for issue body"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("issue_body")
    args = parser.parse_args()
    # Example issue body:
    """### GitHub repository

canonical/mysql-router-k8s-operator

### Git ref (branch, tag, commit sha, etc.)

main

### Relative path to charmcraft.yaml

."""
    match = re.fullmatch(
        r"""### GitHub repository

(?P<organization>[a-zA-Z0-9.\-_]+)/(?P<repo_name>[a-zA-Z0-9.\-_]+)

### Git ref \(branch, tag, commit sha, etc\.\)

(?P<ref>\S+)

### Relative path to charmcraft\.yaml

(?P<path>[^\n]+)""",
        args.issue_body,
    )
    try:
        if not match:
            raise IssueParsingError("@carlcsaposs-canonical Error parsing issue body")
        organization = match.group("organization")
        charm_branch = charm.Charm(
            github_repository=f'{organization}/{match.group("repo_name")}',
            ref=match.group("ref"),
            relative_path_to_charmcraft_yaml=match.group("path"),
        )
        allowed_github_orgs = ("canonical", "juju", "charmed-kubernetes")
        if organization not in allowed_github_orgs:
            raise IssueParsingError(
                "To protect against arbitrary code execution, charmcraftcache-hub is only available for "
                f'these GitHub organizations: {", ".join(allowed_github_orgs)}. '
                "More info: https://github.com/carlcsaposs-canonical/charmcraftcache/issues/2"
            )
        try:
            subprocess.run(
                ["git", "check-ref-format", "--allow-onelevel", charm_branch.ref],
                check=True,
            )
        except subprocess.CalledProcessError:
            raise IssueParsingError("Invalid git ref. @carlcsaposs-canonical")
        path = pathlib.Path(charm_branch.relative_path_to_charmcraft_yaml)
        if not path.resolve().is_relative_to(pathlib.Path(".").resolve()):
            raise IssueParsingError("Invalid path. @carlcsaposs-canonical")
    except IssueParsingError as exception:
        output = f"success={json.dumps(False)}\nerror={exception.message}"
    else:
        with open("charms.json", "r") as file:
            data = json.load(file)
        data.append(dataclasses.asdict(charm_branch))
        with open("charms.json", "w") as file:
            json.dump(data, file, indent=2)
        output = f"success={json.dumps(True)}\ntitle=Add {charm_branch.github_repository}@{charm_branch.ref} at path {charm_branch.relative_path_to_charmcraft_yaml}"
    print(output)
    with open(os.environ["GITHUB_OUTPUT"], "a") as file:
        file.write(output)

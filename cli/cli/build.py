import argparse
import json
import tomllib

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("charm_locks_json")
    args = parser.parse_args()
    with open(args.charm_locks_json, "r") as file:
        charm_lock_files = json.load(file)
    for url in charm_lock_files:
        response = requests.get(url)
        response.raise_for_status()
        poetry_lock_file = response.text
        foo = tomllib.loads(poetry_lock_file)
        print(foo)

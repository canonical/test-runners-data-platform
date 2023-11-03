import argparse
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("charms_file")
    args = parser.parse_args()
    with open(args.charms_file, "r") as file:
        charms = json.load(file)
    for charm in charms:
        print(charm)

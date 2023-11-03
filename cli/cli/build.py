import argparse
import dataclasses
import json
import os
import pathlib
import subprocess


@dataclasses.dataclass(frozen=True, kw_only=True)
class Charm:
    github_repository: str
    ref: str
    relative_path_to_charmcraft_yaml: str

    @property
    def _repository_directory(self) -> pathlib.Path:
        return pathlib.Path("repos", self.github_repository)

    def checkout_repository(self):
        try:
            self._repository_directory.mkdir(parents=True)
        except FileExistsError:
            commands = [
                f"git fetch origin {self.ref}",
                "git checkout FETCH_HEAD",
            ]
        else:
            commands = [
                "git init",
                "git sparse-checkout set --sparse-index .",
                f"git remote add --fetch origin https://github.com/{self.github_repository}.git",
                f"git fetch origin {self.ref}",
                "git checkout FETCH_HEAD",
            ]
        for command in commands:
            subprocess.run(
                command.split(" "), cwd=self._repository_directory, check=True
            )

    @property
    def directory(self) -> pathlib.Path:
        return self._repository_directory / self.relative_path_to_charmcraft_yaml


@dataclasses.dataclass(frozen=True, kw_only=True)
class Dependency:
    name: str
    version: str


def main():
    pip_cache = pathlib.Path("~/charmcraftcache-hub-build/").expanduser()
    pip_cache.mkdir()
    parser = argparse.ArgumentParser()
    parser.add_argument("charms_file")
    args = parser.parse_args()
    with open(args.charms_file, "r") as file:
        charms = [Charm(**charm) for charm in json.load(file)]
    dependencies: dict[Charm, set[Dependency]] = {}
    for charm in charms:
        charm.checkout_repository()
        assert (charm.directory / "poetry.lock").exists()
        subprocess.run(
            [
                "poetry",
                "export",
                # Ignore other dependency groups (e.g. unit test, lint, etc.)
                "--only",
                "main",
                "--output",
                "requirements.txt",
            ],
            cwd=charm.directory,
            check=True,
        )
        # Build wheels from source
        env = os.environ
        env["XDG_CACHE_HOME"] = str(pip_cache)
        subprocess.run(
            [
                "pip",
                "install",
                "-r",
                "requirements.txt",
                # Build from source
                "--no-binary",
                ":all:",
                # Cache will still be hit if exact version of wheel available
                # `--ignore-installed` needed:
                # - to ignore non-exact versions
                # - to include all dependencies in report
                "--ignore-installed",
                "--report",
                "report.json",
            ],
            cwd=charm.directory,
            check=True,
            env=env,
        )
        with open(charm.directory / "report.json", "r") as file:
            report = json.load(file)
        dependencies[charm] = {
            Dependency(
                name=dependency["metadata"]["name"],
                version=dependency["metadata"]["version"],
            )
            for dependency in report["install"]
        }
    serializable_dependencies = {}
    for charm in dependencies:
        serializable_dependencies[str(dataclasses.asdict(charm))] = [
            dataclasses.asdict(dependency) for dependency in dependencies
        ]
    with open("dependencies.json", "w") as file:
        json.dump(serializable_dependencies, file, indent=2)

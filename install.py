#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

DESTINATIONS = {
    "copilot": Path(".agents") / "skills",
    "claude": Path(".claude") / "skills",
    "copilot-cli": Path(".copilot") / "skills",
}
SKILLS = ("itr", "itr2")


def install(target: str, home: Path, repository: Path) -> list[Path]:
    destination = home / DESTINATIONS[target]
    destination.mkdir(parents=True, exist_ok=True)
    installed: list[Path] = []
    for skill in SKILLS:
        source = repository / skill
        output = destination / skill
        shutil.copytree(
            source,
            output,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.py[cod]"),
        )
        installed.append(output)
    return installed


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the bundled ITR skills.")
    parser.add_argument("target", nargs="?", default="copilot", choices=DESTINATIONS)
    parser.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    args = parser.parse_args()

    repository = Path(__file__).resolve().parent
    for path in install(args.target, args.home.expanduser().resolve(), repository):
        print(f"Installed {path.name} -> {path}")
    print("Reload your agent to pick up the skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

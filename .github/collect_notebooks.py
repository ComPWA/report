"""Print notebooks changed relative to a base ref, excluding pytest --ignore paths."""
# /// script
# requires-python = ">=3.11"
# ///

from __future__ import annotations

import subprocess  # noqa: S404
import sys
from pathlib import Path

import tomllib  # ty:ignore[unresolved-import]


def main() -> None:
    base_ref = sys.argv[1] if len(sys.argv) > 1 else "main"
    changed = subprocess.check_output(  # noqa: S603
        ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"],  # noqa: S607
        text=True,
    ).splitlines()

    notebooks: set[Path] = set()
    for path_str in changed:
        path = Path(path_str)
        if path.suffix == ".ipynb":
            notebooks.add(path)
        elif path.name == "uv.lock":
            notebooks.update(path.parent.glob("*.ipynb"))

    with open("pyproject.toml", "rb") as f:
        addopts = tomllib.load(f)["tool"]["pytest"]["addopts"]
    ignored = [
        Path(o[len("--ignore=") :]) for o in addopts if o.startswith("--ignore=")
    ]

    def is_ignored(nb: Path) -> bool:
        return any(nb == ig or ig in nb.parents for ig in ignored)

    result = sorted(nb for nb in notebooks if not is_ignored(nb))
    print(" ".join(str(nb) for nb in result))  # noqa: T201


if __name__ == "__main__":
    main()

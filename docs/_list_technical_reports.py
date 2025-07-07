from __future__ import annotations

import re
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import nbformat

if TYPE_CHECKING:
    from nbformat import NotebookNode


def main() -> int:
    table = _create_tr_table()
    this_dir = Path(__file__).parent
    output_path = this_dir / "_inventory.md"
    with open(output_path, "w") as f:
        f.write(table)
    return 0


def _create_tr_table() -> str:
    notebook_paths = _get_technical_report_paths()
    src = dedent(
        """
    |    | TR | Title | Details | Tags | Status |
    |:--:|:--:|:------|:--------|:-----|:-------|
    """
    ).strip()
    for notebook in notebook_paths:
        card_info = _get_card_info(notebook)
        tr = card_info["tr"]
        title = card_info["title"]
        details = re.sub(
            r"\[([^\]]+)\]\((\.|\.\./)?(\d\d\d)/index\.ipynb\)",
            r"[\1](\3/index.ipynb)",
            card_info.get("details", ""),
        )
        details = re.sub(r"<!---* (.*?) -*-->(<br>)?", "", details)
        tags = " ".join(_to_badge(tag) for tag in sorted(card_info["tags"]))
        status = re.sub(
            r"\[([^\]]+)\-([^\]]+)\]\(([^\)]+)\)",
            r"[\1&#8209;\2](\3)",
            card_info.get("footer", "\n").splitlines()[0],
        )
        src += (
            f"\n| | **[TR&#8209;{tr}]({tr}/index.ipynb)** | {title} | {details} | {tags} |"
            f" {status} |"
        )
    return src


def _to_badge(tag: str) -> str:
    return f"{{bdg-info-line}}`{tag}`"


def _get_technical_report_paths() -> list[Path]:
    report_dir = Path(__file__).parent
    return sorted(report_dir.glob("???/index.ipynb"))


def _get_card_info(path: Path) -> dict[str, str]:
    notebook = _open_notebook(path)
    for cell in notebook["cells"]:
        if cell["cell_type"] != "markdown":
            continue
        src: list[str] = cell["source"].splitlines()
        src = [s for s in src if s.strip() if not s.strip().startswith("<!--")]
        if len(src) < 5:  # noqa: PLR2004
            continue
        line1, line2, line3, *_ = src
        if line1 != "::::{margin}":
            continue
        if not line2.startswith(":::{card} "):
            continue
        if not line3.startswith("TR-"):
            continue
        return _extract_card_info(cell)
    repo_dir = Path(__file__).parent.parent
    msg = (
        f"Technical report {path.relative_to(repo_dir)} does not contain an info card."
        " See one of the other report notebooks for what the card should look like."
    )
    raise RuntimeError(msg)


def _open_notebook(path: Path) -> NotebookNode:
    return nbformat.read(path, as_version=nbformat.NO_CONVERT)


def _extract_card_info(cell: NotebookNode) -> dict[str, str]:
    src = cell["source"]
    _, line2, line3, *rest = src.splitlines()
    info = {
        "title": line2.split(":::{card} ")[1],
        "tr": line3.split("TR-")[1],
        "tags": cell["metadata"].get("tags", []),
    }
    body = extract_body("\n".join(rest))
    footer = _extract_footer(src)
    if body:
        info["details"] = body
    if footer is not None and "https://github.com" in footer:
        info["footer"] = footer
    return info


def extract_body(rest: str) -> str | None:
    body = rest.split(":::", maxsplit=1)[0].split("+++")[0].strip()
    if "^^^" in body:
        body = body.split("^^^")[1].strip()
    return body.replace("\n", "<br>")


def _extract_footer(src: str) -> str | None:
    if "+++" not in src:
        return None
    return src.split("+++")[1].split(":::")[0].strip()


if __name__ == "__main__":
    raise SystemExit(main())

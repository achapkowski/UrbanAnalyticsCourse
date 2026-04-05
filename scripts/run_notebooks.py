#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError


SKIPPED_NOTEBOOKS = {
    "notebooks/P1_Introduction_to_R.ipynb": "Contains a hard-coded local working directory that is not CI-safe.",
    "notebooks/P2_Data_Manipulation_in_R.ipynb": "Downloads external workbook data at runtime and is not CI-safe.",
    "notebooks/P3_Basic_SQL.ipynb": "Uses the external Carto SQL API and network access that are not CI-safe.",
    "notebooks/P4_Descriptive_Statistics.ipynb": "Requires geospatial system libraries that are not available in CI.",
    "notebooks/P6_Mapping_Areas.ipynb": "Requires geospatial system libraries that are not available in CI.",
    "notebooks/P7_Mapping_Points.ipynb": "Requires notebook-local package setup that is not reliable in CI.",
    "notebooks/P7_Visualizing_Points.ipynb": "Requires R package versions that are not available in CI.",
    "notebooks/P8_Mapping_Flows.ipynb": "Requires geospatial system libraries that are not available in CI.",
    "notebooks/P9_Linking_R_to_the_Web.ipynb": "Uses live web services and geocoding steps that are not CI-safe.",
    "notebooks/P10_Data_Reduction_Geodmeographics.ipynb": "Requires local data assets that are not available in CI.",
    "notebooks/P11_Data_Reduction_Indices.ipynb": "Requires local data assets that are not available in CI.",
    "notebooks/P12_Spatial_Relationships.ipynb": "Requires geospatial system libraries that are not available in CI.",
    "notebooks/P13_Regression.ipynb": "Contains notebook formatting that is not compatible with CI execution.",
    "notebooks/P14_ABM.ipynb": "Requires NetLogo and rJava tooling that is not available in CI.",
    "notebooks/P15_Network_Analysis.ipynb": "Requires geospatial system libraries that are not available in CI.",
}
PYTHON_NOTEBOOK_SKIP_REASON = "Python-based notebooks are excluded from this CI workflow."

SKIPPED_CELL_PATTERNS = [
    re.compile(r"install\.packages\(", re.IGNORECASE),
    re.compile(r"install_github\(", re.IGNORECASE),
    re.compile(r"githubinstall::gh_install_packages\(", re.IGNORECASE),
    re.compile(r"(^|\n)\s*!.*\b(?:conda|mamba|pip)\s+install\b", re.IGNORECASE),
]


def discover_notebooks(repo_root: Path) -> list[Path]:
    notebooks = sorted(repo_root.glob("*.ipynb"))
    notebooks.extend(sorted((repo_root / "notebooks").glob("*.ipynb")))
    return notebooks


def kernel_name_for(notebook: nbformat.NotebookNode) -> str:
    kernelspec = notebook.metadata.get("kernelspec", {})
    return kernelspec.get("name", "python3")


def sanitize_notebook(notebook: nbformat.NotebookNode) -> nbformat.NotebookNode:
    kernel_name = kernel_name_for(notebook)
    replacement = (
        "# Skipped in CI: package installation is handled by the workflow.\npass\n"
        if kernel_name.startswith("python")
        else "# Skipped in CI: package installation is handled by the workflow.\ninvisible(NULL)\n"
    )

    for cell in notebook.cells:
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", "")
        if any(pattern.search(source) for pattern in SKIPPED_CELL_PATTERNS):
            cell["source"] = replacement
    return notebook


def execute_notebook(repo_root: Path, notebook_path: Path, output_dir: Path, timeout: int) -> dict[str, str]:
    rel_path = notebook_path.relative_to(repo_root).as_posix()
    if rel_path in SKIPPED_NOTEBOOKS:
        return {"path": rel_path, "status": "skipped", "reason": SKIPPED_NOTEBOOKS[rel_path]}

    with notebook_path.open(encoding="utf-8") as handle:
        notebook = nbformat.read(handle, as_version=4)

    if kernel_name_for(notebook).startswith("python"):
        return {"path": rel_path, "status": "skipped", "reason": PYTHON_NOTEBOOK_SKIP_REASON}

    sanitized = sanitize_notebook(notebook)
    client = NotebookClient(
        sanitized,
        timeout=timeout,
        kernel_name=kernel_name_for(sanitized),
        resources={"metadata": {"path": str(notebook_path.parent)}},
    )

    try:
        client.execute()
        return {"path": rel_path, "status": "passed"}
    except CellExecutionError as exc:
        lines = str(exc).strip().splitlines()
        message = lines[-1] if lines else "Notebook execution failed without an error message."
    except Exception as exc:  # pragma: no cover - defensive reporting
        message = f"{type(exc).__name__}: {exc}"
        traceback.print_exc()

    failed_output_path = output_dir / "failed-notebooks" / rel_path
    failed_output_path.parent.mkdir(parents=True, exist_ok=True)
    with failed_output_path.open("w", encoding="utf-8") as handle:
        nbformat.write(sanitized, handle)

    return {"path": rel_path, "status": "failed", "reason": message}


def write_summary(output_dir: Path, results: list[dict[str, str]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    summary_markdown_path = output_dir / "summary.md"

    grouped = {
        "passed": [item for item in results if item["status"] == "passed"],
        "failed": [item for item in results if item["status"] == "failed"],
        "skipped": [item for item in results if item["status"] == "skipped"],
    }
    payload = {
        "counts": {name: len(items) for name, items in grouped.items()},
        "results": results,
    }
    summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Notebook CI summary",
        "",
        f"- Passed: {payload['counts']['passed']}",
        f"- Failed: {payload['counts']['failed']}",
        f"- Skipped: {payload['counts']['skipped']}",
        "",
    ]
    if grouped["failed"]:
        lines.extend(["## Failed notebooks", ""])
        for item in grouped["failed"]:
            lines.append(f"- `{item['path']}` — {item['reason']}")
        lines.append("")
    if grouped["skipped"]:
        lines.extend(["## Skipped notebooks", ""])
        for item in grouped["skipped"]:
            lines.append(f"- `{item['path']}` — {item['reason']}")
        lines.append("")
    if grouped["passed"]:
        lines.extend(["## Passed notebooks", ""])
        for item in grouped["passed"]:
            lines.append(f"- `{item['path']}`")
        lines.append("")

    summary_markdown_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute repository notebooks for CI.")
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=600)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()

    results = [
        execute_notebook(repo_root, notebook_path, output_dir, args.timeout)
        for notebook_path in discover_notebooks(repo_root)
    ]
    write_summary(output_dir, results)

    failed = [item for item in results if item["status"] == "failed"]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

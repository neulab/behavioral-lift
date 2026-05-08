#!/usr/bin/env python3
"""Compute Recovery Rate from annotation JSONL files.

Recovery Rate measures whether a model reaches the correct answer after at least
one annotated reasoning failure:

    Recovery = P(correct | any failure mode is true)

Expected input: one or more JSONL files whose rows contain the judge output under
an "evaluation" key, matching taxonomy/llm_schema.json or taxonomy/vlm_schema.json.

Example:
    python metrics/recovery_rate.py annotations/ --output results/recovery_rate.csv
    python metrics/recovery_rate.py annotations/ --group-by modality benchmark model
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_FAILURES = [
    "factual_error",
    "visual_hallucination",
    "visual_neglect",
    "logical_failure",
    "context_misread",
    "knowledge_gap",
    "language_bias",
    "post_hoc_rationalization",
    "shortcut",
    "lucky_guess",
]


def iter_jsonl_files(path: Path):
    if path.is_file():
        yield path
    else:
        yield from sorted(path.rglob("*.jsonl"))


def load_rows(path: Path):
    for file_path in iter_jsonl_files(path):
        with file_path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON in {file_path}:{line_no}: {exc}") from exc
                if "evaluation" in row:
                    row["_source_file"] = str(file_path)
                    yield row


def get_metadata(row: dict[str, Any], field: str) -> str:
    metadata = row.get("metadata", {})
    value = row.get(field, metadata.get(field, "ALL"))
    return str(value if value is not None else "ALL")


def is_correct(row: dict[str, Any]) -> bool:
    return bool(
        row.get("evaluation", {})
        .get("reasoning_quality", {})
        .get("reaches_correct_conclusion", False)
    )


def has_any_failure(row: dict[str, Any], failure_fields: list[str]) -> bool:
    failure_modes = row.get("evaluation", {}).get("failure_modes", {})
    return any(bool(failure_modes.get(field, False)) for field in failure_fields)


def compute_recovery(rows, failure_fields: list[str], group_by: list[str]):
    counts = defaultdict(lambda: {"n": 0, "correct": 0, "fail_n": 0, "fail_correct": 0, "clean_n": 0, "clean_correct": 0})

    for row in rows:
        group_key = tuple(get_metadata(row, field) for field in group_by) if group_by else tuple()
        correct = is_correct(row)
        failed = has_any_failure(row, failure_fields)

        c = counts[group_key]
        c["n"] += 1
        c["correct"] += int(correct)

        if failed:
            c["fail_n"] += 1
            c["fail_correct"] += int(correct)
        else:
            c["clean_n"] += 1
            c["clean_correct"] += int(correct)

    output_rows = []
    for group_key, c in sorted(counts.items()):
        n = c["n"]
        fail_n = c["fail_n"]
        clean_n = c["clean_n"]
        output_rows.append(
            {
                **{field: group_key[i] for i, field in enumerate(group_by)},
                "n": n,
                "accuracy": c["correct"] / n if n else None,
                "n_with_failure": fail_n,
                "failure_rate": fail_n / n if n else None,
                "recovery_rate": c["fail_correct"] / fail_n if fail_n else None,
                "n_without_failure": clean_n,
                "clean_accuracy": c["clean_correct"] / clean_n if clean_n else None,
            }
        )
    return output_rows


def write_csv(rows: list[dict[str, Any]], output_path: Path, group_by: list[str]):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = group_by + [
        "n",
        "accuracy",
        "n_with_failure",
        "failure_rate",
        "recovery_rate",
        "n_without_failure",
        "clean_accuracy",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_args():
    parser = argparse.ArgumentParser(description="Compute Recovery Rate from annotation JSONL files.")
    parser.add_argument("annotations", type=Path, help="Annotation JSONL file or directory.")
    parser.add_argument("--output", type=Path, default=Path("results/recovery_rate.csv"))
    parser.add_argument(
        "--failure-fields",
        nargs="+",
        default=DEFAULT_FAILURES,
        help="Failure-mode fields that count as a detected failure.",
    )
    parser.add_argument(
        "--group-by",
        nargs="*",
        default=[],
        help="Optional top-level or metadata fields to group by, e.g. modality benchmark model.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    rows = list(load_rows(args.annotations))
    if not rows:
        raise SystemExit(f"No annotation rows found in {args.annotations}")

    output_rows = compute_recovery(rows, args.failure_fields, args.group_by)
    write_csv(output_rows, args.output, args.group_by)
    print(f"Wrote {len(output_rows)} Recovery Rate rows to {args.output}")


if __name__ == "__main__":
    main()

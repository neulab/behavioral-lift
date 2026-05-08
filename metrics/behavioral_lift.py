#!/usr/bin/env python3
"""Compute Behavioral Lift from annotation JSONL files.

Behavioral Lift measures how much correctness changes when a behavior is present:

    Lift(b) = P(correct | b=true) - P(correct | b=false)

Expected input: one or more JSONL files whose rows contain the judge output under
an "evaluation" key, matching taxonomy/llm_schema.json or taxonomy/vlm_schema.json.

Example:
    python metrics/behavioral_lift.py annotations/ --output results/behavioral_lift.csv
    python metrics/behavioral_lift.py annotations/ --group-by modality benchmark
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_BEHAVIORS = [
    "planning_present",
    "hypothesis_testing",
    "self_correction",
    "uncertainty_acknowledgment",
    "evidence_citation",
    "confidence_calibration",
    "self_awareness",
    "goal_tracking",
    "knowledge_alignment",
]

SEARCH_GROUPS = [
    "visual_grounding",
    "reasoning_quality",
    "advanced_and_metacognitive",
    "metacognitive_behaviors",
    "reasoning_types",
    "failure_modes",
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
    """Read grouping fields from top-level metadata when available."""
    metadata = row.get("metadata", {})
    value = row.get(field, metadata.get(field, "ALL"))
    return str(value if value is not None else "ALL")


def is_correct(row: dict[str, Any]) -> bool:
    return bool(
        row.get("evaluation", {})
        .get("reasoning_quality", {})
        .get("reaches_correct_conclusion", False)
    )


def get_behavior(row: dict[str, Any], behavior: str):
    evaluation = row.get("evaluation", {})
    for group in SEARCH_GROUPS:
        group_data = evaluation.get(group, {})
        if behavior in group_data:
            return group_data[behavior]
    return None


def compute_lift(rows, behaviors: list[str], group_by: list[str]):
    counts = defaultdict(lambda: defaultdict(lambda: {"pt": 0, "pc": 0, "at": 0, "ac": 0}))

    for row in rows:
        group_key = tuple(get_metadata(row, field) for field in group_by) if group_by else tuple()
        correct = is_correct(row)

        for behavior in behaviors:
            value = get_behavior(row, behavior)
            if value is None:
                continue
            bucket = counts[group_key][behavior]
            if value:
                bucket["pt"] += 1
                bucket["pc"] += int(correct)
            else:
                bucket["at"] += 1
                bucket["ac"] += int(correct)

    output_rows = []
    for group_key, behavior_counts in sorted(counts.items()):
        for behavior, c in sorted(behavior_counts.items()):
            n_present = c["pt"]
            n_absent = c["at"]
            n_total = n_present + n_absent
            p_present = c["pc"] / n_present if n_present else None
            p_absent = c["ac"] / n_absent if n_absent else None
            lift = (p_present - p_absent) if p_present is not None and p_absent is not None else None

            output_rows.append(
                {
                    **{field: group_key[i] for i, field in enumerate(group_by)},
                    "behavior": behavior,
                    "n": n_total,
                    "n_present": n_present,
                    "n_absent": n_absent,
                    "p_correct_present": p_present,
                    "p_correct_absent": p_absent,
                    "lift": lift,
                    "presence_rate": n_present / n_total if n_total else None,
                }
            )
    return output_rows


def write_csv(rows: list[dict[str, Any]], output_path: Path, group_by: list[str]):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = group_by + [
        "behavior",
        "n",
        "n_present",
        "n_absent",
        "p_correct_present",
        "p_correct_absent",
        "lift",
        "presence_rate",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_args():
    parser = argparse.ArgumentParser(description="Compute Behavioral Lift from annotation JSONL files.")
    parser.add_argument("annotations", type=Path, help="Annotation JSONL file or directory.")
    parser.add_argument("--output", type=Path, default=Path("results/behavioral_lift.csv"))
    parser.add_argument(
        "--behaviors",
        nargs="+",
        default=DEFAULT_BEHAVIORS,
        help="Behavior fields to evaluate. Defaults to the nine shared higher-order behaviors.",
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

    output_rows = compute_lift(rows, args.behaviors, args.group_by)
    write_csv(output_rows, args.output, args.group_by)
    print(f"Wrote {len(output_rows)} Behavioral Lift rows to {args.output}")


if __name__ == "__main__":
    main()

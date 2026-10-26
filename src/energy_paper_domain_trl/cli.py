from __future__ import annotations

import argparse
import json
from pathlib import Path

from .compare import compare_document


def _read_records(path: Path) -> list[dict]:
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, list) else [value]


def main() -> None:
    ap = argparse.ArgumentParser(description="Compare one document with each of its fine-topic TRL fields")
    ap.add_argument("--target", type=Path, required=True, help="JSON object containing one document")
    ap.add_argument("--corpus", type=Path, required=True, help="JSON or JSONL peer corpus")
    ap.add_argument("--output", type=Path)
    ap.add_argument("--min-peers", type=int, default=20)
    args = ap.parse_args()
    target_rows = _read_records(args.target)
    if len(target_rows) != 1:
        ap.error("--target must contain exactly one JSON object")
    result = compare_document(target_rows[0], _read_records(args.corpus), min_peers=args.min_peers)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)

"""Compare a document with same-topic, same-carrier peers.

The comparison is deliberately done independently for every confirmed fine
topic.  A multi-topic document therefore receives one peer distribution per
topic; topics are never silently collapsed into one synthetic field.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from statistics import mean, median
from typing import Any, Iterable


def normalize_title(title: str) -> str:
    """Return a stable title key for cross-source duplicate removal."""
    value = unicodedata.normalize("NFKC", str(title or "")).casefold()
    value = re.sub(r"[^\w\u4e00-\u9fff]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def _topics(row: dict[str, Any]) -> list[str]:
    value = row.get("topic_codes", row.get("fine_topics", row.get("topics", [])))
    if isinstance(value, str):
        value = [x.strip() for x in re.split(r"[,;|]", value) if x.strip()]
    return [str(x) for x in (value or []) if str(x).strip()]


def _carrier(row: dict[str, Any]) -> str:
    return str(row.get("technology_carrier", row.get("carrier", "unknown")) or "unknown").strip().casefold()


def _trl(row: dict[str, Any]) -> int | None:
    value = row.get("trl_level", row.get("trl", row.get("level")))
    if isinstance(value, dict):
        value = value.get("level")
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if 1 <= value <= 9 else None


def _identity(row: dict[str, Any]) -> tuple[str, str]:
    doc_id = str(row.get("doc_id", row.get("id", "")) or "").strip()
    title_key = normalize_title(row.get("title", ""))
    # IDs take precedence.  A missing ID falls back to title; an empty row is
    # still given a unique-ish key so it cannot collapse every missing record.
    return (f"id:{doc_id}" if doc_id else f"title:{title_key}", title_key)


def _dedupe(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen_id: set[str] = set()
    seen_title: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        key, title = _identity(row)
        if key in seen_id or (title and title in seen_title):
            continue
        seen_id.add(key)
        if title:
            seen_title.add(title)
        result.append(row)
    return result


def _stats(values: list[int], target_level: int | None) -> dict[str, Any]:
    ordered = sorted(values)
    n = len(ordered)
    q1 = float(ordered[(n - 1) // 4]) if n else None
    q3 = float(ordered[(3 * (n - 1)) // 4]) if n else None
    med = float(median(ordered)) if n else None
    return {
        "n": n,
        "median": med,
        "mean": float(mean(ordered)) if n else None,
        "q1": q1,
        "q3": q3,
        "iqr": (q3 - q1) if n else None,
        "distribution": {str(k): values.count(k) for k in range(1, 10) if k in values},
        "target_trl": target_level,
        "delta_from_median": (target_level - med) if target_level is not None and med is not None else None,
    }


def compare_document(document: dict[str, Any], corpus: Iterable[dict[str, Any]], *, min_peers: int = 20) -> dict[str, Any]:
    """Return independent same-topic TRL comparisons for one document.

    ``corpus`` may contain the target itself and duplicate rows.  The target
    is removed by ID/title, and peers are deduplicated before statistics.
    Records without a valid 1--9 TRL are retained in coverage counts but do not
    enter the numeric distribution.
    """
    if min_peers < 0:
        raise ValueError("min_peers must be non-negative")
    target_id, target_title = _identity(document)
    target_topics = _topics(document)
    target_carrier = _carrier(document)
    target_trl = _trl(document)
    rows = _dedupe(corpus)
    # Remove target by either stable ID or normalized title.
    rows = [r for r in rows if _identity(r)[0] != target_id and not (target_title and _identity(r)[1] == target_title)]
    output: list[dict[str, Any]] = []
    for topic in target_topics:
        candidates = [r for r in rows if topic in _topics(r) and _carrier(r) == target_carrier]
        candidates = _dedupe(candidates)
        valid = [(_trl(r), r) for r in candidates]
        valid = [(level, r) for level, r in valid if level is not None]
        levels = [level for level, _ in valid]
        stats = _stats(levels, target_trl)
        stats.update({
            "topic_code": topic,
            "technology_carrier": target_carrier,
            "candidate_records": len(candidates),
            "records_with_valid_trl": len(valid),
            "minimum_peers": min_peers,
            "status": "supported" if len(valid) >= min_peers else "insufficient_peers",
            "peer_ids": [str(r.get("doc_id", r.get("id", ""))) for _, r in valid[:100]],
        })
        output.append(stats)
    return {
        "algorithm_version": "same-fine-topic-same-carrier-trl-20261026-v1",
        "document": {
            "doc_id": document.get("doc_id", document.get("id")),
            "title": document.get("title", ""),
            "topic_codes": target_topics,
            "technology_carrier": target_carrier,
            "trl_level": target_trl,
        },
        "same_field_definition": "each confirmed fine topic independently + same technology carrier",
        "comparisons": output,
        "topic_count": len(target_topics),
        "note": "No fine-topic relation means no field comparison; an insufficient peer set is reported rather than imputed.",
    }

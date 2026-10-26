from energy_paper_domain_trl.compare import compare_document, normalize_title


def _row(i, title, topics, carrier, trl):
    return {"doc_id": f"p{i}", "title": title, "topic_codes": topics,
            "technology_carrier": carrier, "trl_level": trl}


def test_multi_topic_is_compared_independently_and_duplicates_are_removed():
    target = _row("target", "Target", ["CFT-1", "CFT-2"], "battery", 6)
    peers = [
        _row(1, "one", ["CFT-1"], "battery", 4),
        _row(2, "two", ["CFT-1"], "battery", 6),
        _row(3, "three", ["CFT-2"], "battery", 8),
        _row(4, "four", ["CFT-2"], "battery", 9),
        _row(5, "same title", ["CFT-1"], "battery", 9),
        _row(6, "SAME TITLE", ["CFT-1"], "battery", 1),
        _row(7, "wrong carrier", ["CFT-1"], "wind", 9),
        {"doc_id": "missing", "title": "no level", "topic_codes": ["CFT-1"], "technology_carrier": "battery"},
    ]
    out = compare_document(target, peers, min_peers=2)
    by_topic = {x["topic_code"]: x for x in out["comparisons"]}
    assert by_topic["CFT-1"]["distribution"] == {"4": 1, "6": 1, "9": 1}
    assert by_topic["CFT-1"]["status"] == "supported"
    assert by_topic["CFT-2"]["distribution"] == {"8": 1, "9": 1}
    assert by_topic["CFT-2"]["median"] == 8.5


def test_title_normalization_and_missing_field_are_explicit():
    assert normalize_title("  Grid—Control: A  ") == "grid control a"
    out = compare_document({"doc_id": "x", "title": "x", "topic_codes": [], "trl_level": 4}, [], min_peers=0)
    assert out["comparisons"] == []

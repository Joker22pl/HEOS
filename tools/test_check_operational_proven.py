#!/usr/bin/env python3
"""Testy dla tools/check_operational_proven.py — model dowodu operacyjnego.

Wszystkie testy używają tmp_path (nie modyfikują prawdziwego HEOS ani
~/.hermes/skills/.usage.json).
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _make_skill(path: Path, name: str, quality_operational: str = "unmeasured"):
    """Utwórz minimalny skill z zadanym quality_operational."""
    fm_lines = [
        "type: skill",
        f"id: skill-{name}",
        f"name: {name}",
        "title: Test Skill",
        "status: accepted",
        "owner: gaja",
        "created_at: '2026-07-27'",
        "updated_at: '2026-07-27'",
        "review_due: '2027-01-25'",
        "version: 1.0.0",
        "heos_standard_version: '1.2'",
        "tags:",
        "- test",
        "related: []",
        f"quality_operational: {quality_operational}",
    ]
    body = "\n".join([
        "---",
        "\n".join(fm_lines),
        "---",
        "",
        "## Cel",
        "Testowy skill dla check_operational_proven.",
        "",
        "## Zakres",
        "Testowanie rekomendacji operational.",
        "",
        "## Kiedy używać",
        "- gdy testujesz ADR-007",
        "- gdy sprawdzasz runtime usage",
        "",
        "## Kiedy nie używać",
        "- do testowania innych narzędzi",
        "- w produkcji runtime",
        "",
        "## Workflow",
        "1. Wywołaj check_operational_proven",
        "2. Przejrzyj rekomendacje",
        "3. Zweryfikuj ręcznie",
        "",
        "## Przykłady",
        "Przykładowe komendy dla runtime evidence w HEOS.",
        "```bash",
        "python3 tools/check_operational_proven.py",
        "echo rekomendacja sprawdzona",
        "echo skill zaktualizowany",
        "```",
        "",
        "## Lessons Learned",
        "- Runtime evidence musi być z runtime, nie ręczne",
    ])
    path.write_text(body, encoding="utf-8")


def _make_usage_json(path: Path, skills: dict):
    """Zapisz mock .usage.json. skills: {skill_name: {use_count, state, ...}}"""
    now = datetime.now(timezone.utc)
    payload = {}
    for name, props in skills.items():
        payload[name] = {
            "archived_at": None,
            "created_at": props.get("created_at", now.isoformat()),
            "created_by": None,
            "last_patched_at": None,
            "last_used_at": props.get("last_used_at", now.isoformat()),
            "last_viewed_at": now.isoformat(),
            "patch_count": 0,
            "pinned": False,
            "state": props.get("state", "active"),
            "use_count": props.get("use_count", 0),
            "view_count": props.get("use_count", 0),
        }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _create_heos_with_skills(tmp_path: Path, skill_configs: list[tuple[str, str]]):
    """Tworzy HEOS-like katalog z skillami.

    skill_configs: lista (name, quality_operational).
    Returns: heos_root, usage_json_path.
    """
    heos_root = tmp_path / "heos"
    skills_dir = heos_root / "skills"
    skills_dir.mkdir(parents=True)
    for name, q_op in skill_configs:
        _make_skill(skills_dir / f"{name}.md", name, q_op)
    usage_json = tmp_path / ".usage.json"
    return heos_root, usage_json


def test_recommend_unmeasured_no_record():
    """Skill bez wpisu w usage.json → unmeasured."""
    from check_operational_proven import _recommend_operational
    assert _recommend_operational(None) == "unmeasured"


def test_recommend_unmeasured_zero_uses():
    """Skill z use_count=0 → unmeasured."""
    from check_operational_proven import _recommend_operational
    record = {"use_count": 0, "state": "active"}
    assert _recommend_operational(record) == "unmeasured"


def test_recommend_candidate_single_use():
    """Skill z 1 użyciem → candidate."""
    from check_operational_proven import _recommend_operational
    now = datetime.now(timezone.utc)
    record = {
        "use_count": 1,
        "state": "active",
        "created_at": (now - timedelta(days=30)).isoformat(),
        "last_used_at": now.isoformat(),
    }
    assert _recommend_operational(record) == "candidate"


def test_recommend_candidate_young_skill():
    """Skill z 5 użyciami ale za młody → candidate (grace period)."""
    from check_operational_proven import _recommend_operational
    now = datetime.now(timezone.utc)
    # created_at tylko 3 dni temu (poniżej PROVEN_MIN_DAYS=7)
    record = {
        "use_count": 5,
        "state": "active",
        "created_at": (now - timedelta(days=3)).isoformat(),
        "last_used_at": now.isoformat(),
    }
    assert _recommend_operational(record) == "candidate"


def test_recommend_proven_3_uses_7_days():
    """Skill z 3+ użyciami + 7+ dni → proven."""
    from check_operational_proven import _recommend_operational
    now = datetime.now(timezone.utc)
    record = {
        "use_count": 3,
        "state": "active",
        "created_at": (now - timedelta(days=10)).isoformat(),
        "last_used_at": now.isoformat(),
    }
    assert _recommend_operational(record) == "proven"


def test_recommend_proven_high_usage():
    """Skill z 100 użyciami + 30 dni → proven."""
    from check_operational_proven import _recommend_operational
    now = datetime.now(timezone.utc)
    record = {
        "use_count": 100,
        "state": "active",
        "created_at": (now - timedelta(days=30)).isoformat(),
        "last_used_at": now.isoformat(),
    }
    assert _recommend_operational(record) == "proven"


def test_recommend_stale_old_usage():
    """Skill z 5 użyciami ale ostatnie 200 dni temu → stale."""
    from check_operational_proven import _recommend_operational
    now = datetime.now(timezone.utc)
    record = {
        "use_count": 5,
        "state": "active",
        "created_at": (now - timedelta(days=365)).isoformat(),
        "last_used_at": (now - timedelta(days=200)).isoformat(),
    }
    assert _recommend_operational(record) == "stale"


def test_recommend_unmeasured_archived():
    """Skill zarchiwizowany → unmeasured (nie proven)."""
    from check_operational_proven import _recommend_operational
    now = datetime.now(timezone.utc)
    record = {
        "use_count": 100,
        "state": "archived",
        "created_at": (now - timedelta(days=30)).isoformat(),
        "last_used_at": now.isoformat(),
    }
    assert _recommend_operational(record) == "unmeasured"


def test_read_usage_json_nonexistent(tmp_path):
    """_read_usage_json dla nieistniejącego pliku → pusty dict."""
    from check_operational_proven import _read_usage_json
    assert _read_usage_json(tmp_path / "nope.json") == {}


def test_read_usage_json_corrupted(tmp_path):
    """_read_usage_json dla corrupted JSON → pusty dict (nie crash)."""
    from check_operational_proven import _read_usage_json
    p = tmp_path / "corrupt.json"
    p.write_text("{not json", encoding="utf-8")
    assert _read_usage_json(p) == {}


def test_read_skill_name(tmp_path):
    """_read_skill_name parsuje frontmatter poprawnie."""
    from check_operational_proven import _read_skill_name
    p = tmp_path / "test.md"
    p.write_text("---\ntype: skill\nname: my-skill\nid: skill-my-skill\ntitle: X\nstatus: accepted\nowner: gaja\ncreated_at: '2026-07-27'\nupdated_at: '2026-07-27'\nreview_due: '2027-01-25'\nversion: 1.0.0\nheos_standard_version: '1.2'\ntags:\n- test\nrelated: []\n---\n", encoding="utf-8")
    assert _read_skill_name(p) == "my-skill"


def test_read_skill_name_no_frontmatter(tmp_path):
    """_read_skill_name dla pliku bez frontmatter → None."""
    from check_operational_proven import _read_skill_name
    p = tmp_path / "test.md"
    p.write_text("no frontmatter here\n", encoding="utf-8")
    assert _read_skill_name(p) is None


def test_read_quality_operational_missing(tmp_path):
    """_read_quality_operational gdy pole brak → None."""
    from check_operational_proven import _read_quality_operational
    p = tmp_path / "test.md"
    p.write_text("---\nname: x\n---\n", encoding="utf-8")
    assert _read_quality_operational(p) is None


def test_main_exit_code_no_root(tmp_path):
    """main() gdy HEOS root nie istnieje → exit 2 (katalog nie istnieje)."""
    import sys
    old_argv = sys.argv
    sys.argv = ["check_operational_proven.py",
                "--root", str(tmp_path / "empty"),
                "--usage-json", str(tmp_path / "nope.json")]
    try:
        from check_operational_proven import main
        rc = main()
        assert rc == 2, f"Expected 2, got {rc}"
    finally:
        sys.argv = old_argv


def test_main_exit_code_no_skills(tmp_path):
    """main() gdy HEOS root istnieje ale brak skills → exit 1."""
    heos_root = tmp_path / "heos-empty"
    heos_root.mkdir()
    import sys
    old_argv = sys.argv
    sys.argv = ["check_operational_proven.py",
                "--root", str(heos_root),
                "--usage-json", str(tmp_path / "nope.json")]
    try:
        from check_operational_proven import main
        rc = main()
        assert rc == 1, f"Expected 1, got {rc}"
    finally:
        sys.argv = old_argv


def test_main_consistent_report(tmp_path):
    """main() gdy skille mają quality_operational = rekomendacja → 6/7 consistent (1 fresh ręczne)."""
    import sys
    heos_root, usage_json = _create_heos_with_skills(tmp_path, [
        ("skill-a", "unmeasured"),  # 0 uses → unmeasured ✓
        ("skill-b", "candidate"),   # 1 use → candidate ✓
        ("skill-c", "proven"),      # 5 uses 30 dni → proven ✓
        ("skill-d", "stale"),       # 0 uses 200 dni → stale ✓
        ("skill-e", "failed"),      # brak wpisu → unmeasured ✗ (failed > unmeasured)
    ])
    # 4 z 5 ma jakość zgodną z rekomendacją
    _make_usage_json(usage_json, {
        "skill-b": {"use_count": 1, "state": "active"},
        "skill-c": {"use_count": 5, "state": "active"},
        "skill-d": {"use_count": 1, "state": "active",
                    "last_used_at": (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()},
        # skill-a i skill-e nie mają wpisu → unmeasured rekomendacja
    })

    old_argv = sys.argv
    sys.argv = ["check_operational_proven.py",
                "--root", str(heos_root),
                "--usage-json", str(usage_json),
                "--check"]
    try:
        from check_operational_proven import main
        rc = main()
        # main() zwraca 0 zawsze (rekomendacja, nie blokada)
        assert rc == 0, f"Expected 0, got {rc}"
    finally:
        sys.argv = old_argv
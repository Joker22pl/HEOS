"""
Testy jednostkowe dla weekly_report.py (v1.2).

Smoke test: sprawdza że główne funkcje działają bez błędów.
Pełne testy czekają na v1.3.
"""
import sys
import importlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_module_imports():
    """weekly_report.py można zaimportować."""
    wr = importlib.import_module("weekly_report")
    assert hasattr(wr, "_run_audit")
    assert hasattr(wr, "_emoji_bar")
    assert hasattr(wr, "build_report")
    assert hasattr(wr, "main")


def test_emoji_bar_empty():
    """_emoji_bar(0, 0) — nie crashuje."""
    from weekly_report import _emoji_bar
    bar = _emoji_bar(0, 0)
    assert "0%" in bar


def test_emoji_bar_full():
    """_emoji_bar(10, 10) — pełny pasek."""
    from weekly_report import _emoji_bar
    bar = _emoji_bar(10, 10)
    assert "100%" in bar
    assert "█" * 10 in bar


def test_emoji_bar_partial():
    """_emoji_bar(3, 10) — 30%."""
    from weekly_report import _emoji_bar
    bar = _emoji_bar(3, 10)
    assert "30%" in bar
    assert "███" in bar
    assert "░░" in bar


def test_build_report_minimal():
    """build_report z minimalnymi stats (format heos_stats/hermes_stats)."""
    from weekly_report import build_report
    heos_stats = {"total": 5, "pass": 3, "warn": 1, "fail": 1}
    hermes_stats = {"total": 87, "pass": 2, "warn": 0, "fail": 83, "error": None}
    md = build_report(heos_stats, hermes_stats)
    assert "HEOS Weekly Audit" in md
    assert "3/5" in md
    assert "2/87" in md
    assert "HEOS (nowe Skillsy)" in md
    assert "Hermes Profile" in md


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))


def test_parse_audit_output_standard_format():
    """Parser odczytuje Schema: ✅ N PASS | ⚠️  N WARN | ❌ N FAIL.

    Regression test — wcześniej parser szukał '%' który nigdy nie był w output.
    """
    from weekly_report import _run_audit
    from pathlib import Path
    # Mock: używamy prawdziwego skill_audit.py na HEOS (mamy 5 skille, 5 PASS, 0 WARN, 0 FAIL)
    heos = Path(__file__).resolve().parent.parent
    stats = _run_audit(heos)
    assert "error" not in stats, f"_run_audit error: {stats.get('error')}"
    assert stats["total"] == 5, f"Expected total=5, got {stats['total']}"
    assert stats["pass"] == 5, f"Expected pass=5, got {stats['pass']}"
    assert stats["warn"] == 0, f"Expected warn=0, got {stats['warn']}"
    assert stats["fail"] == 0, f"Expected fail=0, got {stats['fail']}"


def test_audit_path_is_v12_layout():
    """_run_audit szuka tools/skill_audit.py (nie 03-quality/ z v1.1)."""
    from weekly_report import _run_audit, HEOS_ROOT
    heos = HEOS_ROOT
    expected_path = heos / "tools" / "skill_audit.py"
    assert expected_path.exists(), f"v1.2 layout missing: {expected_path}"
    # Stary v1.1 layout NIE powinien istnieć
    legacy_path = heos / "03-quality" / "skill_audit.py"
    assert not legacy_path.exists(), f"Legacy v1.1 path still present: {legacy_path}"

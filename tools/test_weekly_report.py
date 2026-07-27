"""
Testy jednostkowe dla weekly_report.py (v1.2).

Smoke test: sprawdza że główne funkcje działają bez błędów.
Pełne testy czekają na v1.3.
"""
import sys
import importlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


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

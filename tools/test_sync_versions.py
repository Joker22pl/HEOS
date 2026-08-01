#!/usr/bin/env python3
"""
Regression test: sync_versions.py.

Tło (P0.2 z audytu 2026-08-01): HEOS trzymał wersję w 4 plikach
(STATUS, CONSTITUTION, README, ARCHITECTURE) bez automatycznej synchronizacji.
CONSTITUTION=1.5.2, README=1.5.4, ARCHITECTURE=1.5.2 — kłamstwo.

Fix: `tools/sync_versions.py` z trybami --check i --sync. STATUS jest truth.
Ten test asertuje:

1. STATUS.md jest czytelny jako źródło prawdy (regex łapie wersję).
2. CONSTITUTION/README/ARCHITECTURE są zsynchronizowane (po --sync).
3. Gdy ręcznie nadpiszemy CONSTITUTION na starą wersję, --check zgłasza drift.
4. --sync naprawia drift.
5. Atomic write (per ADR-008): plik po --sync ma tę samą zawartość logiczną.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "tools" / "sync_versions.py"

CONSTITUTION = REPO_ROOT / "CONSTITUTION.md"
README = REPO_ROOT / "README.md"
ARCHITECTURE = REPO_ROOT / "ARCHITECTURE.md"
STATUS = REPO_ROOT / "STATUS.md"

VERSION_PATTERN = re.compile(
    r"\*\*Wersja(?:\s+HEOS)?:\*\*\s+`?v?(\d+\.\d+\.\d+)`?"
)


def read_version(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    m = VERSION_PATTERN.search(text)
    return m.group(1) if m else None


def run_sync(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_status_has_version():
    """STATUS.md (autoritative) musi mieć czytelną wersję."""
    v = read_version(STATUS)
    assert v, f"STATUS.md nie ma czytelnej wersji HEOS (pattern nie złapał)."
    # Akceptujemy tylko SemVer
    assert re.fullmatch(r"\d+\.\d+\.\d+", v), f"Wersja '{v}' nie jest SemVer."


def test_initial_sync_runs():
    """Po wywołaniu --check (po naszym sync) wszystkie pliki zsynchronizowane."""
    result = run_sync(["--check"])
    assert result.returncode == 0, (
        f"--check zwrócił {result.returncode}, spodziewaliśmy 0 (zsynchronizowane). "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


def test_drift_detection():
    """Gdy nadpiszemy CONSTITUTION.md na starą wersję, --check zgłasza drift (exit 1)."""
    # Zapisz oryginalną wartość.
    original = CONSTITUTION.read_text(encoding="utf-8")
    try:
        # Celowo ustawiamy drift.
        drifted = re.sub(
            VERSION_PATTERN,
            "**Wersja:** v1.5.2",
            original,
            count=1,
        )
        assert drifted != original, "Test setup nie zdraftował pliku (pattern nie złapał)."
        CONSTITUTION.write_text(drifted, encoding="utf-8")
        result = run_sync(["--check"])
        assert result.returncode == 1, (
            f"--check nie wykrył dryfu! exit={result.returncode}, "
            f"stdout={result.stdout!r}"
        )
        assert "driftem" in result.stdout or "driftem" in result.stderr, (
            f"Komunikat nie mówi o drifie: {result.stdout!r} {result.stderr!r}"
        )
    finally:
        CONSTITUTION.write_text(original, encoding="utf-8")


def test_sync_repairs_drift():
    """Pełny scenariusz: drift → --sync → --check wraca do 0."""
    original_c = CONSTITUTION.read_text(encoding="utf-8")
    original_r = README.read_text(encoding="utf-8")
    original_a = ARCHITECTURE.read_text(encoding="utf-8")
    src_v = read_version(STATUS)
    assert src_v is not None
    try:
        # Drift wszystkich 3 mirrored.
        for path in [CONSTITUTION, README, ARCHITECTURE]:
            txt = path.read_text(encoding="utf-8")
            drifted = re.sub(
                VERSION_PATTERN,
                "**Wersja:** v0.0.1-alpha",
                txt,
                count=1,
            )
            path.write_text(drifted, encoding="utf-8")

        check_drift = run_sync(["--check"])
        assert check_drift.returncode == 1, "Po drifcie --check powinien zwrócić 1."

        run_sync(["--sync"])

        check_after = run_sync(["--check"])
        assert check_after.returncode == 0, (
            f"Po --sync, --check powinien zwrócić 0. "
            f"stdout={check_after.stdout!r}"
        )
        for path in [CONSTITUTION, README, ARCHITECTURE]:
            v = read_version(path)
            assert v == src_v, (
                f"{path.name}: oczekiwałem v{src_v}, dostałem v{v}"
            )
    finally:
        CONSTITUTION.write_text(original_c, encoding="utf-8")
        README.write_text(original_r, encoding="utf-8")
        ARCHITECTURE.write_text(original_a, encoding="utf-8")


def test_atomic_write_no_corruption():
    """sync_versions używa atomic write (per ADR-008) — plik nie zostaje częściowo zapisany."""
    # Po prostu uruchamiamy --sync i sprawdzamy, że plik jest czytelny
    # i ma poprawny format (nie corrupted).
    result = run_sync(["--sync"])
    assert result.returncode == 0
    for path in [CONSTITUTION, README, ARCHITECTURE]:
        txt = path.read_text(encoding="utf-8")
        assert VERSION_PATTERN.search(txt), (
            f"{path.name} po --sync nie ma czytelnej wersji — możliwe uszkodzenie."
        )


if __name__ == "__main__":
    test_status_has_version()
    test_initial_sync_runs()
    test_drift_detection()
    test_sync_repairs_drift()
    test_atomic_write_no_corruption()
    print("✅ test_sync_versions.py — 5/5 OK")

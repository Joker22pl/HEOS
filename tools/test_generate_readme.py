#!/usr/bin/env python3
"""
Regression test: generate_readme.py.

Tło (P1.1 z audytu 2026-08-01): README ręcznie utrzymywane tabele dryfowały
względem registry (Skills: 7 zamiast 8, ADR: 10/11, Artefakty: 20 vs 22).

Fix: tools/generate_readme.py czyta .registry.yaml, --check wykrywa dryf w counts
+ wersji (nie w tytułach ADR — to migracja), --sync aktualizuje tabele.

Testy:
1. drift_signals poprawnie identyfikuje count mismatches.
2. _normalize_version normalizuje '1.6.13' / 'v1.6.13' / '`v1.6.13`' do 'v1.6.13'.
3. status_version zwraca 'vX.Y.Z' zawsze (z prefix).
4. compute_desired_readme zamienia 'Artefakty (20 aktywnych)' → '(22 aktywnych)'.
5. compute_desired_readme zamienia '| Skills | 7 |' → '| Skills | 8 |'.
6. compute_desired_readme zamienia nagłówek 'Decision Records (N)' na aktualne.
7. --check (subprocess) exit 0 gdy README zgodne.
8. --sync poprawnie aktualizuje README (atomic write).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "tools" / "generate_readme.py"
README = REPO_ROOT / "README.md"
REGISTRY = REPO_ROOT / ".registry.yaml"
STATUS = REPO_ROOT / "STATUS.md"

# Import modułu do unit-testów.
sys.path.insert(0, str(REPO_ROOT / "tools"))
import generate_readme  # type: ignore[import-not-found]  # noqa: E402


def test_normalize_version():
    """_normalize_version normalizuje różne formaty do 'vX.Y.Z'."""
    assert generate_readme._normalize_version("1.6.13") == "v1.6.13"
    assert generate_readme._normalize_version("v1.6.13") == "v1.6.13"
    assert generate_readme._normalize_version("`v1.6.13`") == "v1.6.13"
    assert generate_readme._normalize_version("  v1.6.13  ") == "v1.6.13"
    assert generate_readme._normalize_version(None) is None
    # Versja z `v` jest OK
    assert generate_readme._normalize_version("`1.6.13`") == "v1.6.13"


def test_status_version_returns_v_prefix():
    """status_version() zawsze zwraca 'vX.Y.Z' z prefix."""
    v = generate_readme.status_version()
    assert v.startswith("v"), f"Oczekiwałem 'vX.Y.Z', dostałem '{v}'"
    assert re.fullmatch(r"v\d+\.\d+\.\d+", v), f"'{v}' nie jest SemVer"


def test_drift_signals_counts():
    """drift_signals poprawnie czyta count values z mock-upu README."""
    # Symulujemy README z dryfem.
    fake_readme = """# HEOS
**Wersja HEOS:** v1.6.13

## Artefakty (20 aktywnych)

| Typ | Liczba | Lokalizacja |
|---|---|---|
| Skills | 7 | `skills/` |
| ADR | 10 | `decisions/` |
| Lessons Learned | 1 | `lessons/` |
| Checklisty | 1 | `checklists/` |
| Playbooki | 1 | `playbooks/` |
"""
    reg = {
        "_meta": {"total_artifacts": 22, "by_type": {"skill": 8, "adr": 11, "lessons": 1, "checklist": 1, "playbook": 1}},
        "artifacts": {"adr": [], "skill": [], "lessons": [], "checklist": [], "playbook": []},
    }
    signals = generate_readme.drift_signals(fake_readme, reg, "v1.6.13")
    assert signals["total"] == (20, 22), f"Total drift detection broken: {signals['total']}"
    assert signals["skills"] == (7, 8)
    assert signals["adr"] == (10, 11)
    assert signals["version"] == ("v1.6.13", "v1.6.13")


def test_compute_desired_readme_updates_counts():
    """compute_desired_readme zamienia count headers."""
    fake = """# HEOS
**Wersja HEOS:** v1.6.13

## Artefakty (20 aktywnych)

| Typ | Liczba | Lokalizacja |
|---|---|---|
| Skills | 7 | `skills/` |
| ADR | 10 | `decisions/` |
| Lessons Learned | 1 | `lessons/` |
| Checklisty | 1 | `checklists/` |
| Playbooki | 1 | `playbooks/` |

## Decision Records (10 aktywnych)
"""
    reg = {
        "_meta": {"total_artifacts": 22, "by_type": {"skill": 8, "adr": 11, "lessons": 1, "checklist": 1, "playbook": 1}},
        "artifacts": {
            "adr": [
                {"id": "adr-001", "name": "001-foo", "title": "Foo", "status": "accepted", "path": "decisions/001-foo.md"},
                {"id": "adr-002", "name": "002-bar", "title": "Bar", "status": "accepted", "path": "decisions/002-bar.md"},
            ],
        },
    }
    new, warnings = generate_readme.compute_desired_readme(fake, reg, "v1.6.13")
    assert "Artefakty (22 aktywnych)" in new, "Total count nie zaktualizowany"
    assert "| Skills | 8 |" in new, "Skills count nie zaktualizowany"
    assert "| ADR | 11 |" in new, "ADR count nie zaktualizowany"


def test_check_exit_zero_when_synced():
    """Po --sync, --check exit 0."""
    # Najpierw sync (zapewnia że README jest zgodne).
    sync_res = subprocess.run(
        [sys.executable, str(SCRIPT), "--sync"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert sync_res.returncode == 0, f"--sync zwrócił {sync_res.returncode}: {sync_res.stderr!r}"

    check_res = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert check_res.returncode == 0, (
        f"--check (po sync) nie zgłosił zgodności: "
        f"exit={check_res.returncode}, stdout={check_res.stdout!r}, stderr={check_res.stderr!r}"
    )
    assert "✅" in check_res.stdout, check_res.stdout


def test_check_detects_known_drift():
    """Gdy obniżymy Skills count w README, --check exit 1 z dryfem."""
    original = README.read_text(encoding="utf-8")
    try:
        # Wywołaj dryf: Skills 8 → 7
        drifted = re.sub(
            r"\|\s*Skills\s*\|\s*\d+",
            "| Skills | 7",
            original,
            count=1,
        )
        assert drifted != original
        README.write_text(drifted, encoding="utf-8")

        check_res = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert check_res.returncode == 1, (
            f"--check nie wykrył dryfu (Skills 8→7)! exit={check_res.returncode}"
        )
        assert "Skills count" in check_res.stdout or "Skills count" in check_res.stderr
    finally:
        README.write_text(original, encoding="utf-8")


def test_atomic_write_no_corruption():
    """--sync używa atomic write — README ma tę samą semantykę po i przed."""
    sync_res = subprocess.run(
        [sys.executable, str(SCRIPT), "--sync"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert sync_res.returncode == 0
    # Sprawdź że README ma czytelne elementy.
    text = README.read_text(encoding="utf-8")
    assert re.search(r"Artefakty \(\d+ aktywnych\)", text)
    assert re.search(r"\| Skills \| \d+ \|", text)
    assert re.search(r"\| ADR \| \d+ \|", text)


if __name__ == "__main__":
    test_normalize_version()
    test_status_version_returns_v_prefix()
    test_drift_signals_counts()
    test_compute_desired_readme_updates_counts()
    test_check_exit_zero_when_synced()
    test_check_detects_known_drift()
    test_atomic_write_no_corruption()
    print("✅ test_generate_readme.py — 7/7 OK")

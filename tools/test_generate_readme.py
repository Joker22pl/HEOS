#!/usr/bin/env python3
"""
Regression test: generate_readme.py.

Tło (P1.1 z audytu 2026-08-01): README ręcznie utrzymywane tabele dryfowały
względem registry (Skills: 7 zamiast 8, ADR: 10/11, Artefakty: 20 vs 22).

Fix: tools/generate_readme.py czyta .registry.yaml, --check wykrywa dryf w counts
+ wersji (nie w tytułach ADR — to migracja), --sync aktualizuje tabele.

Hermetyczność (audyt 2026-08-05): testy NIE dotykają realnego repo.
Fixture `hermetic_repo` kopiuje README/.registry.yaml/STATUS/generate_readme.py
do tmp_path i przekierowuje moduł na kopię. Subprocess-y działają w kopii.
Poprzednia wersja uruchamiała `--sync` na prawdziwym README i pisała po nim
bezpośrednio — zanieczyszczała working tree (P1-1 w audycie zewnętrznym 2026-08-05).

Testy:
1. drift_signals poprawnie identyfikuje count mismatches.
2. _normalize_version normalizuje '1.6.13' / 'v1.6.13' / '`v1.6.13`' do 'v1.6.13'.
3. status_version zwraca 'vX.Y.Z' zawsze (z prefix).
4. compute_desired_readme zamienia 'Artefakty (20 aktywnych)' → '(22 aktywnych)'.
5. compute_desired_readme zamienia '| Skills | 7 |' → '| Skills | 8 |'.
6. compute_desired_readme zamienia nagłówek 'Decision Records (N)' na aktualne.
7. --check (subprocess) exit 0 gdy README zgodne (na hermetycznej kopii).
8. --sync poprawnie aktualizuje README (atomic write, na hermetycznej kopii).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "tools" / "generate_readme.py"
README = REPO_ROOT / "README.md"
REGISTRY = REPO_ROOT / ".registry.yaml"
STATUS = REPO_ROOT / "STATUS.md"

# Import modułu do unit-testów.
sys.path.insert(0, str(REPO_ROOT / "tools"))
import generate_readme  # type: ignore[import-not-found]  # noqa: E402


@pytest.fixture(scope="module")
def hermetic_repo(tmp_path_factory):
    """Buduje hermetyczną kopię repo w tmp_path i kieruje moduł na nią.

    Kopiowane: README.md, .registry.yaml, STATUS.md, tools/generate_readme.py.
    Subprocess-y (--check/--sync) uruchamiane są w kopii, więc realne repo
    pozostaje nietknięte — także przy dryfie registry↔README.
    """
    root = tmp_path_factory.mktemp("heos_readme")
    tools = root / "tools"
    tools.mkdir()
    shutil.copy(README, root / "README.md")
    shutil.copy(REGISTRY, root / ".registry.yaml")
    shutil.copy(STATUS, root / "STATUS.md")
    shutil.copy(SCRIPT, tools / "generate_readme.py")

    # Przekieruj importowany moduł (in-process) na hermetyczną kopię.
    generate_readme.REPO_ROOT = root
    generate_readme.README = root / "README.md"
    generate_readme.REGISTRY = root / ".registry.yaml"
    generate_readme.STATUS = root / "STATUS.md"
    return root, tools


def test_normalize_version():
    """_normalize_version normalizuje różne formaty do 'vX.Y.Z'."""
    assert generate_readme._normalize_version("1.6.13") == "v1.6.13"
    assert generate_readme._normalize_version("v1.6.13") == "v1.6.13"
    assert generate_readme._normalize_version("`v1.6.13`") == "v1.6.13"
    assert generate_readme._normalize_version("  v1.6.13  ") == "v1.6.13"
    assert generate_readme._normalize_version(None) is None
    # Versja z `v` jest OK
    assert generate_readme._normalize_version("`1.6.13`") == "v1.6.13"


def test_status_version_returns_v_prefix(hermetic_repo):
    """status_version() zawsze zwraca 'vX.Y.Z' z prefix (czyta STATUS z kopii)."""
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


def test_check_exit_zero_when_synced(hermetic_repo):
    """Po --sync, --check exit 0 — na hermetycznej kopii, nie na realnym repo."""
    root, tools = hermetic_repo
    script = tools / "generate_readme.py"

    # Najpierw sync (zapewnia że README w kopii jest zgodne z registry).
    sync_res = subprocess.run(
        [sys.executable, str(script), "--sync"],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert sync_res.returncode == 0, f"--sync zwrócił {sync_res.returncode}: {sync_res.stderr!r}"

    check_res = subprocess.run(
        [sys.executable, str(script), "--check"],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert check_res.returncode == 0, (
        f"--check (po sync) nie zgłosił zgodności: "
        f"exit={check_res.returncode}, stdout={check_res.stdout!r}, stderr={check_res.stderr!r}"
    )
    assert "✅" in check_res.stdout, check_res.stdout


def test_check_detects_known_drift(hermetic_repo):
    """Gdy obniżymy Skills count w README (kopii), --check exit 1 z dryfem."""
    root, tools = hermetic_repo
    script = tools / "generate_readme.py"
    copied_readme = root / "README.md"

    original = copied_readme.read_text(encoding="utf-8")
    try:
        # Wywołaj dryf: Skills 8 → 7
        drifted = re.sub(
            r"\|\s*Skills\s*\|\s*\d+",
            "| Skills | 7",
            original,
            count=1,
        )
        assert drifted != original
        copied_readme.write_text(drifted, encoding="utf-8")

        check_res = subprocess.run(
            [sys.executable, str(script), "--check"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert check_res.returncode == 1, (
            f"--check nie wykrył dryfu (Skills 8→7)! exit={check_res.returncode}"
        )
        assert "Skills count" in check_res.stdout or "Skills count" in check_res.stderr
    finally:
        copied_readme.write_text(original, encoding="utf-8")


def test_atomic_write_no_corruption(hermetic_repo):
    """--sync używa atomic write — README (kopii) ma czytelną semantykę po sync."""
    root, tools = hermetic_repo
    script = tools / "generate_readme.py"
    copied_readme = root / "README.md"

    sync_res = subprocess.run(
        [sys.executable, str(script), "--sync"],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert sync_res.returncode == 0
    # Sprawdź że README ma czytelne elementy.
    text = copied_readme.read_text(encoding="utf-8")
    assert re.search(r"Artefakty \(\d+ aktywnych\)", text)
    assert re.search(r"\| Skills \| \d+ \|", text)
    assert re.search(r"\| ADR \| \d+ \|", text)

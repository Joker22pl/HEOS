#!/usr/bin/env python3
"""
Regression test: skill_audit.py default path.

Tło: 2026-08-01 audyt HEOS wykazał, że `skill_audit.py` wywołany bez argumentu
próbuje zauditować `~/.hermes/profiles/gaja/skills`. Pod spodem, gdy proces
Hermes ustawia `$HOME` na `/home/gaja/.hermes/profiles/<name>/home` (sandbox
profilu), `Path("~/...").expanduser()` zwraca `/home/gaja/.hermes/profiles/<name>/home/.hermes/...`
i `resolve()` skraca do `.../home/.hermes/profiles/gaja/skills` → katalog nie istnieje.

Fix: default = absolutna ścieżka `/home/gaja/.hermes/profiles/gaja/skills`.

Ten test asertuje:
1. Bez argumentu, skrypt NIE raportuje "Katalog nie istnieje".
2. Bez argumentu, skrypt znajduje ≥1 Skill (real katalog).
3. Po patchu zwracana wartość default jest absolutna, nie zawiera `~`.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "tools" / "skill_audit.py"

# Katalog docelowy — absolutna ścieżka, taka sama jak default w skill_audit.py po patchu.
EXPECTED_DEFAULT_PATH = Path("/home/gaja/.hermes/profiles/gaja/skills")


def test_default_path_is_absolute():
    """Default ścieżka w argparse jest absolutna, nie zaczyna się od ~."""
    src = SCRIPT.read_text(encoding="utf-8")
    # Szukamy linii `parser.add_argument("sciezka", nargs="?",`
    # i sprawdzamy czy default value jest absolutną ścieżką.
    import re

    m = re.search(
        r'parser\.add_argument\(\s*"sciezka"[^)]*?default=("([^"]*)")',
        src,
        re.DOTALL,
    )
    assert m, "Nie znaleziono parser.add_argument('sciezka', default=...)"
    default_value = m.group(2)
    assert "~" not in default_value, (
        f"Default ścieżka '{default_value}' zawiera '~' — powoduje "
        f"expanduser() bug pod Hermes profile (HOME=.../profiles/<name>/home)."
    )
    assert default_value.startswith("/"), (
        f"Default '{default_value}' nie jest absolutną ścieżką."
    )
    assert Path(default_value).is_absolute(), (
        f"Default '{default_value}' nie jest absolutną ścieżką."
    )


def test_default_path_exists():
    """Katalog docelowy default istnieje (realny katalog profilu Hermes)."""
    assert EXPECTED_DEFAULT_PATH.is_dir(), (
        f"Ścieżka '{EXPECTED_DEFAULT_PATH}' powinna istnieć dla profilu Hermes 'gaja'. "
        f"Jeśli HEOS jest uruchamiany w innym profilu, ten test wymaga aktualizacji "
        f"default path w skill_audit.py."
    )


def test_no_argument_runs_without_notfound():
    """
    Wywołanie `skill_audit.py` bez argumentów NIE powinno skończyć się
    'Katalog nie istnieje'. Jest to warunek sine qua non — własny audytor
    HEOS musi się sam siebie uruchomić z defaultu.
    """
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--quiet"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    combined = result.stdout + result.stderr
    assert "Katalog nie istnieje" not in combined, (
        f"skill_audit.py (bez argumentów) zgłasza 'Katalog nie istnieje': "
        f"{combined!r} — to jest P0 regresja."
    )
    # Exit code 0 lub 1 (success / some fails) — NIE 2 (Katalog nie istnieje).
    assert result.returncode != 2, (
        f"Exit code 2 wskazuje na 'Katalog nie istnieje'. "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


def test_no_argument_finds_skills():
    """Wywołanie bez argumentu powinno znaleźć co najmniej 1 Skill."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--quiet"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    combined = result.stdout + result.stderr
    # Szukamy linii "Zbadane Skills: N" — N >= 1.
    import re
    m = re.search(r"Zbadane Skills:\s*(\d+)", combined)
    assert m, f"Nie znaleziono 'Zbadane Skills: N' w output: {combined!r}"
    n = int(m.group(1))
    assert n >= 1, (
        f"skill_audit bez arg znalazł 0 skilli — to nie jest oczekiwane; "
        f"realna ścieżka profilu ma >120 skilli."
    )


if __name__ == "__main__":
    test_default_path_is_absolute()
    test_default_path_exists()
    test_no_argument_runs_without_notfound()
    test_no_argument_finds_skills()
    print("✅ test_skill_audit_default_path.py — 4/4 OK")

#!/usr/bin/env python3
"""
sync_versions.py — Single Source of Truth dla wersji HEOS.

Tło (P0.2 z audytu 2026-08-01): Wersja HEOS była zapisana w 4 plikach
(STATUS, CONSTITUTION, README, ARCHITECTURE). Drift między nimi to real bug —
single source of truth (P3 w CONSTITUTION §10) złamany.

Ten skrypt:
1. Czyta prawdę z `STATUS.md` (pierwsza linia `**Wersja HEOS:** vX.Y.Z`).
2. Patchuje 3 mirrored pliki żeby miały tę samą wartość (w ich odpowiednich
   miejscach: nagłówkowa linia wersji).

Użycie:
    python3 tools/sync_versions.py --check    # exit 0 jeśli wszystko zsynchronizowane
    python3 tools/sync_versions.py --sync     # aktualizuje mirrored pliki
    python3 tools/sync_versions.py --show     # pokaż obecny stan

STATUS jest źródłem prawdy (auto-generowany z tools/generate_status.py).
Kolejność priority — gdyby przyszłość wymagała ręcznej edycji:
1. STATUS.md (truth)
2. CONSTITUTION, README, ARCHITECTURE (mirrored)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Plik źródła prawdy (autoritative)
SOURCE_FILE = REPO_ROOT / "STATUS.md"

# Pliki mirrorowane (mają tę samą wartość `version` w nagłówkowej deklaracji)
# Pattern: szukamy linii typu "**Wersja HEOS:** v1.6.13" / "**Wersja:** v1.6.13"
MIRRORED_FILES = [
    REPO_ROOT / "CONSTITUTION.md",
    REPO_ROOT / "README.md",
    REPO_ROOT / "ARCHITECTURE.md",
]

# Toleruj backticki `` `v1.6.13` `` (STATUS) oraz gołe `v1.6.13` (CONSTITUTION/README/ARCHITECTURE).
VERSION_PATTERN = re.compile(
    r"\*\*Wersja(?:\s+HEOS)?:\*\*\s+`?v?(\d+\.\d+\.\d+)`?"
)


def read_version_from(path: Path) -> str | None:
    """Czyta wersję HEOS z danego pliku, szukając wzorca `**Wersja:** vX.Y.Z` lub `**Wersja HEOS:** vX.Y.Z`."""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    m = VERSION_PATTERN.search(text)
    return m.group(1) if m else None


def patch_version_in(path: Path, new_version: str) -> bool:
    """
    Patchuje pierwszą napotkaną linię `**Wersja:** vN.N.N` lub `**Wersja HEOS:** vN.N.N`
    w `path` na nową wersję. Zwraca True jeśli zmieniono.
    Atomic write per ADR-008 — tmp + rename.
    """
    text = path.read_text(encoding="utf-8")
    # Szukamy per-file: w CONSTITUTION/ARCHITECTURE to "**Wersja:**",
    # w README to "**Wersja HEOS:**" (linia 3).
    # Wspólny pattern łapie oba.
    new_text, n = VERSION_PATTERN.subn(
        lambda m: f"**{'Wersja HEOS' if 'HEOS' in m.group(0) else 'Wersja'}:** v{new_version}",
        text,
        count=1,
    )
    if n == 0:
        return False
    # Atomic write (tmp + rename).
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(new_text, encoding="utf-8")
    tmp.replace(path)
    return True


def cmd_check() -> int:
    """Sprawdza czy wszystkie mirrored pliki mają tę samą wersję co SOURCE_FILE."""
    src_version = read_version_from(SOURCE_FILE)
    if src_version is None:
        print(f"❌ Nie można odczytać wersji z {SOURCE_FILE.name}", file=sys.stderr)
        return 2

    mismatches: list[tuple[Path, str | None]] = []
    for f in MIRRORED_FILES:
        v = read_version_from(f)
        if v != src_version:
            mismatches.append((f, v))

    print(f"📋 Źródło prawdy ({SOURCE_FILE.name}): v{src_version}")
    for f in MIRRORED_FILES:
        v = read_version_from(f)
        marker = "✅" if v == src_version else "❌"
        print(f"  {marker} {f.name}: v{v or '<nie znaleziono>'}")

    if mismatches:
        print(
            f"\n❌ {len(mismatches)} plik(ów) z driftem wersji. Napraw: "
            f"`python3 tools/sync_versions.py --sync`",
            file=sys.stderr,
        )
        return 1
    print("\n✅ Wszystkie pliki zsynchronizowane do v" + src_version)
    return 0


def cmd_sync() -> int:
    """Aktualizuje mirrored pliki do wersji ze SOURCE_FILE."""
    src_version = read_version_from(SOURCE_FILE)
    if src_version is None:
        print(f"❌ Nie można odczytać wersji z {SOURCE_FILE.name}", file=sys.stderr)
        return 2

    print(f"📋 Źródło prawdy: v{src_version}")
    changed = 0
    for f in MIRRORED_FILES:
        v_before = read_version_from(f)
        if v_before == src_version:
            print(f"  ✅ {f.name}: już v{src_version}")
            continue
        if patch_version_in(f, src_version):
            print(f"  🔧 {f.name}: v{v_before} → v{src_version}")
            changed += 1
        else:
            print(f"  ⚠️  {f.name}: nie udało się spatchować (szukaj `**Wersja:** vX.Y.Z` lub `**Wersja HEOS:** vX.Y.Z`)")

    print(f"\n🔄 Zmieniono {changed} plik(ów).")
    return 0


def cmd_show() -> int:
    """Pokaż obecny stan wersji w 4 plikach."""
    print("Stan wersji HEOS w 4 kluczowych plikach:")
    print(f"  📌 SOURCE     = {SOURCE_FILE.name}")
    for f in MIRRORED_FILES:
        kind = "MIRRORED" if f.name != "STATUS.md" else "(see source)"
        print(f"     ↳ {kind:8s} {f.name}")
    print()
    for f in [SOURCE_FILE] + MIRRORED_FILES:
        v = read_version_from(f)
        marker = "📌" if f == SOURCE_FILE else "  "
        print(f"  {marker} {f.name:20s} v{v or '<nieznana>'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronizacja wersji HEOS między plikami")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Sprawdź czy wszystko zsynchronizowane")
    group.add_argument("--sync", action="store_true", help="Zsynchronizuj mirrored pliki do STATUS.md")
    group.add_argument("--show", action="store_true", help="Pokaż obecny stan")
    args = parser.parse_args()

    if args.check:
        return cmd_check()
    if args.sync:
        return cmd_sync()
    if args.show:
        return cmd_show()
    # Domyślnie: --check.
    return cmd_check()


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
generate_readme.py — aktualizuje cyfry i listy w README.md z .registry.yaml.

Tło (P1.1 z audytu 2026-08-01): README ręcznie utrzymywane tabele dryfowały
względem registry (mówił 7 skilli zamiast 8, ADR "10/11" zamiast 11).

Fix: skrypt czyta `.registry.yaml`, parsuje README, zamienia targetowane sekcje
z atomic write per ADR-008. Trzy patche:

1. "Artefakty (N aktywnych)" + 4 linie tabeli (Skills/ADR/Lessons/Checklist/Playbook).
2. Tabela "Decision Records (N aktywnych)" — generowana z registry ADRs.
3. Wersja "**Wersja HEOS:** vX.Y.Z" w nagłówku — zsynchronizowana ze STATUS.md
   (single source of truth per `tools/sync_versions.py`).

Użycie:
    python3 tools/generate_readme.py --check      # exit 1 jeśli README driftuje
    python3 tools/generate_readme.py --sync       # patch README
    python3 tools/generate_readme.py --show       # pokaż różnice (diff w stylu)

NIE edytuje CHANGELOG, CONSTITUTION, ARCHITECTURE — to robi sync_versions.
NIE edytuje logiki w CHANGELOG (Keep-a-Changelog format) — tylko sekcje
'counts' w README, które są odbiciem aktualnego stanu repo.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"
REGISTRY = REPO_ROOT / ".registry.yaml"
STATUS = REPO_ROOT / "STATUS.md"


def load_registry() -> dict:
    """Ładuje .registry.yaml (autoritative dla artefaktów)."""
    with REGISTRY.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def artifact_counts(reg: dict) -> dict[str, int]:
    """Zwraca słownik {typ_artefaktu: liczba}."""
    return dict(reg.get("_meta", {}).get("by_type", {}))


def status_version() -> str:
    """Czyta wersję z STATUS.md (truth per sync_versions.py). Zwraca 'vX.Y.Z'."""
    text = STATUS.read_text(encoding="utf-8")
    m = re.search(r"\*\*Wersja HEOS:\*\*\s+`?(v?\d+\.\d+\.\d+)`?", text)
    if not m:
        return "unknown"
    return _normalize_version(m.group(1)) or "unknown"


def _normalize_version(v: str | None) -> str | None:
    """Normalizuje 'v1.6.13' / '1.6.13' / '`v1.6.13`' do 'v1.6.13'."""
    if v is None:
        return None
    v = v.strip().strip("`")
    if not v.startswith("v"):
        v = "v" + v
    return v


def _replace_total_artifacts(text: str, n: int) -> str:
    """'Artefakty (N aktywnych)' / 'Artefakty (N aktywnych)'."""
    return re.sub(
        r"Artefakty\s+\(\d+\s+aktywnych\)",
        f"Artefakty ({n} aktywnych)",
        text,
        count=1,
    )


def _replace_artifact_counts_table(text: str, counts: dict[str, int]) -> str:
    """
    Zamienia CAŁĄ tabelę '## Artefakty (N aktywnych) + 4 wiersze' na nową, zbudowaną z counts.
    To bezpieczniejsze niż patch pojedynczych wierszy (które mają różną składnię).
    """
    # Znajdź blok od nagłówka do następnego `##`.
    pattern = re.compile(
        r"(##\s+Artefakty\s+\(\d+\s+aktywnych\)\n\n)([\s\S]*?)(?=\n## |\Z)",
        re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        return text  # Nie znaleziono — zwróć oryginał.

    skills_count = counts.get("skill", 0)
    # Opis przy Skills: jeśli skills <= 10, pokaż liczbę; w przeciwnym razie
    # całkowita liczba. Pozwala wyjaśnić "5 + 2" historyczny podział.
    skills_label = f"{skills_count}" if skills_count <= 10 else f"{skills_count}+"

    new_rows = [
        f"| Skills | {skills_label} | `skills/` |",
        f"| ADR | {counts.get('adr', 0)} | `decisions/` |",
        f"| Lessons Learned | {counts.get('lessons', 0)} | `lessons/` |",
        f"| Checklisty | {counts.get('checklist', 0)} | `checklists/` |",
        f"| Playbooki | {counts.get('playbook', 0)} | `playbooks/` |",
    ]
    new_table = "| Typ | Liczba | Lokalizacja |\n|---|---|---|\n" + "\n".join(new_rows)
    return text[: m.start(2)] + new_table + "\n" + text[m.end(2):] .lstrip("\n")


def _replace_adr_table(text: str, adrs: list[dict]) -> tuple[str, str | None]:
    """
    Zamienia 'Decision Records (N aktywnych)' i generuje nową tabelę ADR.
    CAŁY blok starej tabeli jest zastępowany (od nagłówka '| ID |' do ostatniego
    wiersza ADR) — bezpieczniej niż regex-substitute per wiersz.

    Zwraca (new_text, warning_or_None).
    """
    n = len(adrs)

    # 1. Patcher nagłówka (nagłówek 'Decision Records (N aktywnych)').
    text = re.sub(
        r"Decision Records \(\d+ aktywnych\)",
        f"Decision Records ({n} aktywnych)",
        text,
        count=1,
    )

    # 2. Zbuduj nową tabelę z registry (titles z registry, NIE z README).
    adr_rows = []
    for adr in adrs:
        adr_id = adr["id"]
        # Konwencja: id = "adr-NNN", path z registry = "decisions/NNN-tytuł.md".
        path = adr.get("path", f"decisions/{adr['name']}.md")
        # Tytuł z registry (jedyne pewne źródło prawdy dla tytułu).
        title = adr["title"]
        status = adr["status"].capitalize()
        adr_rows.append(f"| [{adr_id}]({path}) | {title} | {status} |")
    new_table = (
        "| ID | Tytuł | Status |\n|---|---|---|\n"
        + "".join(r + "\n" for r in adr_rows)
    )

    # 3. Znajdź granicę tabeli: od nagłówka '| ID | Tytuł | Status |' + separator
    # '|---|---|---|' + wszystkie wiersze zaczynające się od '| [adr-NNN]|...'.
    pattern = re.compile(
        r"(\| ID \| Tytuł \| Status \|\n\|[ -|]+\n(?:\| \[(?:adr|skill|lesson|checklist|playbook)-\d+?\].*\n)+)",
        re.MULTILINE,
    )
    m = pattern.search(text)
    if m:
        text = text[: m.start(1)] + new_table + text[m.end(1):]
    else:
        # Fallback — nie udało się znaleźć starej tabeli ADR.
        return text, (
            "Nie udało się znaleźć starej tabeli ADR (pattern '| ID | Tytuł | Status |' "
            "+ linie z '[adr-NNN]...'). README zostawiony nietknięty w tej sekcji."
        )

    return text, None


def _replace_version_in_readme(text: str, version: str) -> str:
    """'Wersja HEOS: vX.Y.Z' w pierwszej linii README."""
    return re.sub(
        r"\*\*Wersja HEOS:\*\*\s+`?v?\d+\.\d+\.\d+`?",
        f"**Wersja HEOS:** `{version}`",
        text,
        count=1,
    )


def compute_desired_readme(original_text: str, reg: dict, version: str) -> tuple[str, list[str]]:
    """
    Buduje nowy README z (original, registry, version).
    Zwraca (new_text, lista_warningów).
    """
    text = original_text
    warnings = []

    counts = artifact_counts(reg)
    total = reg.get("_meta", {}).get("total_artifacts", 0)

    text = _replace_total_artifacts(text, total)

    text = _replace_artifact_counts_table(text, counts)

    adrs = reg.get("artifacts", {}).get("adr", [])
    text, warning = _replace_adr_table(text, adrs)
    if warning:
        warnings.append(warning)

    text = _replace_version_in_readme(text, version)

    return text, warnings


def drift_signals(original_text: str, reg: dict, version: str) -> dict[str, tuple]:
    """
    Zwraca metryki dryfu: ile artefaktów w registry vs w README, wersja vs wersja.
    NIE porównuje pełnych tytułów (to jest kosmetyka).
    """
    # Sprawdź 'Artefakty (N aktywnych)' w oryginale.
    m = re.search(r"Artefakty\s+\((\d+)\s+aktywnych\)", original_text)
    readme_total = int(m.group(1)) if m else None
    registry_total = reg.get("_meta", {}).get("total_artifacts", 0)

    # Sprawdź wiersze | Skills | N |, | ADR | N |.
    skills_m = re.search(r"\|\s*Skills\s*\|\s*(\d+)", original_text)
    readme_skills = int(skills_m.group(1)) if skills_m else None
    registry_skills = reg.get("_meta", {}).get("by_type", {}).get("skill", 0)

    adr_m = re.search(r"\|\s*ADR\s*\|\s*(\d+)", original_text)
    readme_adr = int(adr_m.group(1)) if adr_m else None
    registry_adr = reg.get("_meta", {}).get("by_type", {}).get("adr", 0)

    # Wersja.
    v_m = re.search(r"\*\*Wersja HEOS:\*\*\s+`?v?(\d+\.\d+\.\d+)`?", original_text)
    readme_version = v_m.group(1) if v_m else None

    return {
        "total": (readme_total, registry_total),
        "skills": (readme_skills, registry_skills),
        "adr": (readme_adr, registry_adr),
        "version": (_normalize_version(readme_version), _normalize_version(version)),
    }


def atomic_write(path: Path, content: str) -> None:
    """Atomic write per ADR-008 (tmp + rename)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def cmd_check() -> int:
    reg = load_registry()
    text = README.read_text(encoding="utf-8")
    version = status_version()
    signals = drift_signals(text, reg, version)

    # Sprawdź tylko istotne sygnały: counts + wersja. Tytuły ADR to kosmetyka.
    drift_reasons = []
    for key, label in [
        ("total", "Artefakty (total)"),
        ("skills", "Skills count"),
        ("adr", "ADR count"),
        ("version", "Wersja HEOS"),
    ]:
        readme_v, registry_v = signals[key]
        if readme_v != registry_v:
            drift_reasons.append((label, readme_v, registry_v))

    if not drift_reasons:
        print(f"✅ README zgodne z registry ({version}). Counts: total={signals['total'][1]}, skills={signals['skills'][1]}, adr={signals['adr'][1]}.")
        return 0

    # Pokaż sygnały dryfu.
    print(f"🔍 Dryf w README:")
    for label, readme_v, registry_v in drift_reasons:
        marker = "❌" if readme_v is None or readme_v != registry_v else "✅"
        print(f"   {marker}  {label}: README={readme_v} | registry={registry_v}")
    print(
        f"\n❌ README dryfuje w {len(drift_reasons)} miejscach. "
        "Napraw: `python3 tools/generate_readme.py --sync`",
        file=sys.stderr,
    )
    return 1


def cmd_sync() -> int:
    reg = load_registry()
    text = README.read_text(encoding="utf-8")
    version = status_version()
    new, warnings = compute_desired_readme(text, reg, version)

    if new == text:
        print(f"✅ README już zsynchronizowane ({version}).")
        return 0

    atomic_write(README, new)
    print(f"🔧 README zaktualizowane do {version}.")
    for w in warnings:
        print(f"⚠️  {w}", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronizacja README z registry")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Sprawdź dryf (exit 1 jeśli jest)")
    group.add_argument("--sync", action="store_true", help="Zsynchronizuj README z registry")
    args = parser.parse_args()
    if args.sync:
        return cmd_sync()
    return cmd_check()


if __name__ == "__main__":
    sys.exit(main())

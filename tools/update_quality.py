#!/usr/bin/env python3
"""Aktualizuj quality_* pola w frontmatter na podstawie wyników audytu.

Użycie:
    python3 tools/update_quality.py [--dry-run]

Czyta każdy skill, uruchamia audyt, ustawia:
- quality_schema: pass (Schema 7/7 PASS) | fail (Schema FAIL) | pending (nie oceniony)
- quality_technical: pass (Technical PASS) | fail (Technical FAIL) | pending
- quality_operational: zostawia bez zmian (wymaga manualnej oceny)

Bezpieczne: atomic write, .bak backup, --dry-run domyślne wyłączony (commit explicit).
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from skill_audit import audytuj_skill, audytuj_katalog

HEOS_ROOT = Path(__file__).parent.parent

OBOWIĄZKOWE_POLA = ["quality_schema", "quality_technical"]


def _parsuj_frontmatter(tekst: str) -> tuple[str | None, str, str]:
    """Zwraca (frontmatter_yaml_albo_None, opener '---\\n', rest).

    opener jest pusty — caller dodaje '---' raz na początku i raz przed rest.
    """
    if not tekst.startswith("---"):
        return None, "", tekst
    parts = tekst.split("---", 2)
    if len(parts) < 3:
        return None, "", tekst
    return parts[1], "", parts[2]


def _ustaw_quality(fm_text: str, key: str, value: str) -> str:
    """Ustaw key: value w frontmatter (regex find-and-replace)."""
    pattern = re.compile(rf"^{key}:\s*\S+", re.M)
    if pattern.search(fm_text):
        return pattern.sub(f"{key}: {value}", fm_text)
    # Dodaj przed ostatnim quality_* lub na końcu frontmatter
    return re.sub(
        r"^(quality_\w+:\s*\S+\s*\n)",
        rf"\1{key}: {value}\n",
        fm_text,
        count=1,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Pokaż co by się zmieniło, bez zapisu")
    parser.add_argument("--root", default=str(HEOS_ROOT))
    args = parser.parse_args()
    root = Path(args.root).resolve()

    raporty = audytuj_katalog(root)
    if not raporty:
        print("Brak skills do aktualizacji")
        return 1

    zmienione = 0
    for r in raporty:
        if r.is_not_skill:
            continue
        # Runtime skille (np. nightly-evolution, using-chm) mają mniej wymagań
        # ale nadal powinny mieć aktualne quality_* w HEOS
        txt = r.path.read_text(encoding="utf-8")
        fm, opener, rest = _parsuj_frontmatter(txt)
        if fm is None:
            print(f"⚠️  {r.path.name}: brak frontmatter")
            continue
        # Oblicz nowe wartości
        new_schema = "pass" if r.schema_status == "PASS" else "fail"
        new_technical = "pass" if r.technical_status == "PASS" else "fail"
        # Sprawdź czy coś się zmieni
        cur_schema_m = re.search(r"^quality_schema:\s*(\S+)", fm, re.M)
        cur_tech_m = re.search(r"^quality_technical:\s*(\S+)", fm, re.M)
        cur_schema = cur_schema_m.group(1) if cur_schema_m else None
        cur_tech = cur_tech_m.group(1) if cur_tech_m else None
        if cur_schema == new_schema and cur_tech == new_technical:
            continue
        if args.dry_run:
            print(f"[dry-run] {r.path.relative_to(root)}: schema {cur_schema}→{new_schema}, technical {cur_tech}→{new_technical}")
        else:
            new_fm = _ustaw_quality(fm, "quality_schema", new_schema)
            new_fm = _ustaw_quality(new_fm, "quality_technical", new_technical)
            new_txt = f"---{opener}{new_fm}---{rest}"
            # Backup
            r.path.with_suffix(r.path.suffix + ".bak").write_text(txt)
            r.path.write_text(new_txt, encoding="utf-8")
            print(f"✓ {r.path.relative_to(root)}: schema {cur_schema}→{new_schema}, technical {cur_tech}→{new_technical}")
            zmienione += 1
    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Zmieniono: {zmienione}, bez zmian: {len(raporty) - zmienione}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
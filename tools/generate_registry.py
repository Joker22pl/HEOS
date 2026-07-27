#!/usr/bin/env python3
"""
generate_registry.py — generuje .registry.yaml z metadanych artefaktów w HEOS.

Czyta wszystkie *.md z frontmatter, pomija:
- README.md
- CONSTITUTION.md, ARCHITECTURE.md, STATUS.md
- templates/* (szablony, nie artefakty)
- heos-migration/* (infrastruktura migracji)

Output: .registry.yaml z listą artefaktów pogrupowanych wg `type`.

Backward-compat: czyta zarówno nowe (v1.2, type=skill) jak i stare (v1.1, brak type) formaty.
Dla v1.1 inferuje type ze ścieżki:
  01-domains/X/skills/Y/SKILL.md → type=skill, domain=X
  02-artifacts/skills/X/SKILL.md → type=skill
  02-artifacts/decision-records/ADR-NNN-*.md → type=adr

Użycie:
    python3 generate_registry.py [--root /path/to/HEOS] [--output .registry.yaml]
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


HEOS_ROOT_DEFAULT = Path(__file__).resolve().parent.parent
OUTPUT_DEFAULT = HEOS_ROOT_DEFAULT / ".registry.yaml"

# Pliki pomijane (nie artefakty)
EXCLUDE_PATTERNS = (
    re.compile(r"^README\.md$"),
    re.compile(r"^CONSTITUTION\.md$"),
    re.compile(r"^ARCHITECTURE\.md$"),
    re.compile(r"^STATUS\.md$"),
    re.compile(r"^templates/"),
    re.compile(r"^heos-migration/"),
    re.compile(r"^archive/"),
)

# Typy rozpoznawane
VALID_TYPES = {"skill", "adr", "lessons", "checklist", "playbook"}


def _parsuj_frontmatter(tekst: str) -> dict | None:
    """Parsuje YAML frontmatter; zwraca dict lub None."""
    if not tekst.startswith("---"):
        return None
    parts = tekst.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return None


def _parsuj_adr_v11(tekst: str, sciezka: Path) -> dict | None:
    """Parsuje ADR v1.1 (format Nygard — tabelka z metadanymi).

    Format:
      # ADR-NNN: Tytuł
      | Pole | Wartość |
      | **Status** | Accepted |
      | **Data** | YYYY-MM-DD |
      | **Autor** | ... |

    Returns: dict z polami type=adr, id=adr-NNN, name, status, created_at, tags, related
    """
    # Wyciągnij ID z nazwy pliku lub tytułu
    m = re.search(r"ADR[-_](\d+)", sciezka.name)
    if not m:
        return None
    adr_num = m.group(1)
    # Wyciągnij tytuł
    title = None
    for line in tekst.splitlines():
        if line.startswith("# "):
            t = line[2:].strip()
            # "ADR-001: MicroPython + mpremote..." → "MicroPython + mpremote..."
            if ":" in t:
                title = t.split(":", 1)[1].strip()
            else:
                title = t
            break
    if not title:
        title = f"ADR-{adr_num}"
    # Parsuj tabelkę
    fm: dict = {
        "type": "adr",
        "id": f"adr-{adr_num}",
        "name": sciezka.stem,
        "title": title,
        "adr_number": int(adr_num),
    }
    for line in tekst.splitlines()[:30]:
        # "| **Status** | Accepted |"
        m = re.match(r"\|\s*\*\*(\w[\w\s]*)\*\*\s*\|\s*(.+?)\s*\|", line)
        if m:
            key = m.group(1).strip().lower()
            value = m.group(2).strip()
            # Mapowanie nazw tabelki → nasze pola
            if key == "status":
                fm["status"] = value.lower()
            elif key == "data":
                fm["created_at"] = value
            elif key in ("autor", "author"):
                fm["owner"] = "gaja" if "gaja" in value.lower() else "joker"
            elif key in ("dotyczy domeny", "domain"):
                # Może być "01-domains/embedded" — wyciągnij ostatni segment
                # Normalnie do domeny (backticks, nawiasy, kwalifikatory)
                parts = value.split("/")
                raw = parts[-1].strip("`").strip()
                # Wyciągnij pierwszy sensowny "token" domeny
                # np. "cross-cutting (Hermes Agent)" → "cross-cutting"
                # np. "embedded" → "embedded"
                domain_token = raw.split()[0].strip("(),") if raw else "uncategorized"
                if domain_token in ("embedded", "robotics", "ai-ml", "infrastructure", "web", "cross-cutting"):
                    fm["tags"] = [domain_token]
                else:
                    fm["tags"] = ["cross-cutting"]  # safe default
    return fm


def _infer_type_v11(sciezka: Path) -> tuple[str | None, str | None]:
    """Inferuje type + domain ze ścieżki v1.1.

    Returns: (type, domain) — domain tylko dla Skills w 01-domains/.
    """
    parts = sciezka.parts
    if "01-domains" in parts:
        idx = parts.index("01-domains")
        if idx + 2 < len(parts) and parts[idx + 1] and parts[idx + 2] == "skills":
            domain = parts[idx + 1]
            return ("skill", domain)
    if "02-artifacts" in parts:
        idx = parts.index("02-artifacts")
        if idx + 1 < len(parts):
            sub = parts[idx + 1]
            if sub == "skills":
                return ("skill", "cross-cutting")
            if sub == "decision-records":
                return ("adr", None)
            if sub == "lessons-learned":
                return ("lessons", None)
            if sub == "checklists":
                return ("checklist", None)
            if sub == "playbooks":
                return ("playbook", None)
    return (None, None)


def _zbierz_artefakty(root: Path) -> list[dict]:
    """Zbiera wszystkie artefakty z HEOS/*.md (z wyjątkami)."""
    artefakty = []
    for md in sorted(root.rglob("*.md")):
        rel = md.relative_to(root)
        rel_str = str(rel)
        # Pomijaj pliki nie-artefakty
        if any(pat.search(rel_str) for pat in EXCLUDE_PATTERNS):
            continue
        tekst = md.read_text(encoding="utf-8", errors="replace")
        # Próba 1: YAML frontmatter
        fm = _parsuj_frontmatter(tekst)
        # Próba 2: ADR v1.1 (Nygard tabelka)
        if not fm and "decision-records" in rel_str and md.stem.startswith("ADR-"):
            fm = _parsuj_adr_v11(tekst, md)
        if not fm:
            continue
        # Rozpoznaj typ
        type_ = fm.get("type")
        domain_v11 = None
        if type_ not in VALID_TYPES:
            # Backward-compat: inferuj z v1.1 ścieżki
            type_, domain_v11 = _infer_type_v11(md)
            if not type_:
                # Brak type → pomijamy (prawdopodobnie template lub non-artefakt)
                continue
            # Zapisz type do fm, żeby dalej był dostępny
            fm["type"] = type_
        # Dla v1.1: dodaj tags jeśli ich nie ma
        if "tags" not in fm and domain_v11:
            fm["tags"] = [domain_v11]
        elif "tags" not in fm and not domain_v11:
            # Default tag = "uncategorized"
            fm["tags"] = ["uncategorized"]
        # Wzbogać o ścieżkę względną (dla późniejszego użycia)
        fm["_path"] = rel_str
        # Generuj id jeśli brak (backward-compat dla v1.1)
        if "id" not in fm and "name" in fm:
            fm["id"] = f"{fm['type']}-{fm['name']}"
        # Minimalny zestaw pól do registry (nie cały frontmatter — to byłoby za dużo)
        entry = {k: fm.get(k) for k in [
            "type", "id", "name", "title", "status", "owner",
            "created_at", "updated_at", "review_due", "version",
            "heos_standard_version", "tags", "related",
            "adr_number", "superseded_by",
        ] if k in fm}
        entry["path"] = rel_str
        artefakty.append(entry)
    return artefakty


def _zbuduj_inverse_index(registry: dict) -> dict:
    """Buduje inverse index: id → lista artefaktów które go cytują."""
    inverse: dict[str, list[str]] = {}
    for type_name, items in registry["artifacts"].items():
        for item in items:
            item_id = item.get("id")
            if not item_id:
                continue
            for ref in item.get("related", []):
                ref_id = ref if isinstance(ref, str) else str(ref)
                inverse.setdefault(ref_id, []).append(item_id)
    return inverse


def _pogrupuj(artefakty: list[dict]) -> dict:
    """Grupuje artefakty wg type. Każda grupa posortowana po id/name."""
    grupy: dict[str, list[dict]] = {t: [] for t in VALID_TYPES}
    for a in artefakty:
        t = a.get("type")
        if t in grupy:
            grupy[t].append(a)
    # Sortuj wg id/name
    for t in grupy:
        grupy[t].sort(key=lambda x: (x.get("id") or x.get("name") or x.get("path", "")))
    # Usuń puste grupy
    return {k: v for k, v in grupy.items() if v}


def generuj_registry(root: Path, output: Path) -> dict:
    """Generuje registry. Zwraca statystyki."""
    artefakty = _zbierz_artefakty(root)
    grupy = _pogrupuj(artefakty)
    # Inverse index (kto cytuje kogo) — przydatne do graph v0.1
    inverse = _zbuduj_inverse_index({"artifacts": grupy})
    registry = {
        "_meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "heos_root": str(root),
            "total_artifacts": len(artefakty),
            "by_type": {t: len(v) for t, v in grupy.items()},
        },
        "artifacts": grupy,
        "inverse_index": inverse,
    }
    # Zapisz YAML
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            registry, f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120,
        )
    return {
        "total": len(artefakty),
        "by_type": {t: len(v) for t, v in grupy.items()},
        "output": str(output),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generuj .registry.yaml z HEOS")
    parser.add_argument("--root", default=str(HEOS_ROOT_DEFAULT), help="Katalog HEOS")
    parser.add_argument("--output", default=str(OUTPUT_DEFAULT), help="Plik wyjściowy")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not root.is_dir():
        print(f"❌ Katalog nie istnieje: {root}", file=sys.stderr)
        return 2
    stats = generuj_registry(root, output)
    print(f"✅ Wygenerowano registry: {output}")
    print(f"   Łącznie artefaktów: {stats['total']}")
    for t, n in stats["by_type"].items():
        print(f"   - {t}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
update_frontmatter.py — aktualizuje frontmatter przeniesionych plików v1.2.

Skillsy (skills/*.md):
- Już mają v1.1 frontmatter → dodaj type, id, owner, created_at, updated_at,
  review_due, version, heos_standard_version, status (active→accepted),
  quality_* (3 poziomy)

ADR (decisions/*.md):
- Mają tylko tabelkę Nygard → wyciągnij dane + dodaj YAML frontmatter

Inferencja:
- Status: v1.1 "active" → v1.2 "accepted"
- Domain: z dotychczasowego frontmatter lub ze ścieżki v1.1
- Tags: domain (główny) + technologia (jeśli z nazwy)
- Related: z dotychczasowego `related` lub `related-adrs`
"""
import re
import sys
from datetime import date
from pathlib import Path

import yaml

HEOS = Path("/home/gaja/gaja-projekty/HEOS")
SKILLS_DIR = HEOS / "skills"
DECISIONS_DIR = HEOS / "decisions"
TODAY = date.today().isoformat()


def _parse_nygard_table(text: str) -> dict:
    """Wyciągnij metadane z tabelki Nygard (pierwsze 30 linii)."""
    fm = {}
    for line in text.splitlines()[:30]:
        m = re.match(r"\|\s*\*\*(\w[\w\s]*)\*\*\s*\|\s*(.+?)\s*\|", line)
        if m:
            key = m.group(1).strip().lower()
            value = m.group(2).strip()
            # Strip backticks
            value = value.strip("`")
            if key == "status":
                fm["status"] = value.lower()
                # Mapowanie v1.1 → v1.2
                if fm["status"] == "active":
                    fm["status"] = "accepted"
            elif key == "data":
                fm["created_at"] = value
            elif key in ("autor", "author"):
                fm["owner"] = "gaja" if "gaja" in value.lower() else "joker"
            elif key in ("dotyczy domeny", "domain"):
                # Wyciągnij "embedded" albo "cross-cutting"
                raw = value
                # Spróbuj pattern: "01-domains/embedded" lub "cross-cutting (...)"
                m2 = re.search(r"(?:01-domains/)?(\w[\w-]*)", raw)
                if m2:
                    domain = m2.group(1)
                    if domain in ("embedded", "robotics", "ai-ml", "infrastructure", "web", "cross-cutting"):
                        fm["tags"] = [domain]
    return fm


def _extract_title_h1(text: str) -> str:
    """Wyciągnij tytuł z pierwszego # nagłówka."""
    for line in text.splitlines():
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            t = m.group(1).strip()
            # "ADR-001: MicroPython + mpremote..." → "MicroPython + mpremote..."
            if ":" in t:
                return t.split(":", 1)[1].strip()
            return t
    return None


def _normalize_status_v11(s: str) -> str:
    """Mapuje v1.1 status na v1.2."""
    mapping = {
        "active": "accepted",
        "superseded": "superseded",
        "draft": "draft",
    }
    return mapping.get(s.lower(), "accepted")


def update_skill(path: Path) -> bool:
    """Aktualizuje frontmatter Skilla v1.1 (zachowuje istniejące pola)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        print(f"  ⚠️  {path.name}: brak frontmatter")
        return False
    parts = text.split("---", 2)
    if len(parts) < 3:
        print(f"  ⚠️  {path.name}: malformed frontmatter")
        return False
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        print(f"  ❌ {path.name}: YAML error: {e}")
        return False
    # Wymagane aktualizacje
    fm["type"] = "skill"
    if "id" not in fm:
        fm["id"] = f"skill-{path.stem}"
    if "name" not in fm:
        fm["name"] = path.stem
    if "title" not in fm:
        title = _extract_title_h1(text) or path.stem.replace("-", " ").title()
        fm["title"] = title
    if "status" in fm:
        fm["status"] = _normalize_status_v11(fm["status"])
    else:
        fm["status"] = "accepted"
    if "owner" not in fm:
        fm["owner"] = "gaja"
    if "created_at" not in fm:
        fm["created_at"] = TODAY
    fm["updated_at"] = TODAY
    if "review_due" not in fm:
        fm["review_due"] = "2027-01-23"
    if "version" not in fm:
        fm["version"] = "1.0.0"
    if "heos_standard_version" not in fm:
        fm["heos_standard_version"] = "1.2"
    if "tags" not in fm:
        # Inferuj z domain (v1.1) lub domyślnie cross-cutting
        domain = fm.get("domain", "cross-cutting")
        if domain in ("embedded", "robotics", "ai-ml", "infrastructure", "web"):
            fm["tags"] = [domain]
        else:
            fm["tags"] = ["cross-cutting"]
    # Zamień `related-adrs` → `related` (jeśli istnieje)
    if "related-adrs" in fm:
        fm["related"] = fm.pop("related-adrs")
    elif "related" not in fm:
        fm["related"] = []
    if not isinstance(fm["related"], list):
        fm["related"] = []
    # 3-poziomowa jakość
    if "quality_schema" not in fm:
        fm["quality_schema"] = "pending"
    if "quality_technical" not in fm:
        fm["quality_technical"] = "pending"
    if "quality_operational" not in fm:
        fm["quality_operational"] = "unmeasured"
    # Usuń stare pola v1.1 (które nie pasują do v1.2)
    fm.pop("domain", None)  # domain → tags
    # Zapisz
    new_fm = yaml.safe_dump(fm, default_flow_style=False, sort_keys=False, allow_unicode=True, width=120)
    path.write_text("---\n" + new_fm + "---" + parts[2], encoding="utf-8")
    print(f"  ✅ {path.name}: updated ({fm['status']}, {len(fm['tags'])} tags)")
    return True


def update_adr(path: Path) -> bool:
    """Aktualizuje ADR v1.1 (Nygard → YAML frontmatter)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("---"):
        # Już ma YAML (nie powinno dla v1.1 ADR)
        print(f"  ⏭️  {path.name}: już ma YAML frontmatter")
        return False
    # Wyciągnij z Nygard tabelki
    nygard = _parse_nygard_table(text)
    title = _extract_title_h1(text) or path.stem
    # Wyciągnij numer ADR z nazwy pliku
    m = re.search(r"(\d+)-", path.name)
    adr_num = int(m.group(1)) if m else 0
    # Related z treści (szukaj sekcji "Powiązane" / "Powiazane" + linie po niej)
    related = []
    in_powiazane = False
    for line in text.splitlines():
        if re.search(r"^[#]+\s*[Pp]owi[ąż]zane", line):
            in_powiazane = True
            continue
        if in_powiazane:
            # Koniec sekcji: nowy nagłówek
            if re.match(r"^#", line):
                in_powiazane = False
                continue
            # Szukamy referencji ADR-NNN lub skill-X lub decisions/Y
            refs = re.findall(r"(?:ADR|adr)[-_]?(\d+)", line)
            for r in refs:
                if f"adr-{r}" not in related:
                    related.append(f"adr-{r}")
            # Szukamy skills
            skill_refs = re.findall(r"skills?/([\w-]+)", line)
            for s in skill_refs:
                if f"skill-{s}" not in related:
                    related.append(f"skill-{s}")
    # Nowy frontmatter
    fm = {
        "type": "adr",
        "id": f"adr-{adr_num:03d}",
        "name": path.stem,
        "title": title,
        "adr_number": adr_num,
        "status": nygard.get("status", "accepted"),
        "owner": nygard.get("owner", "gaja"),
        "created_at": nygard.get("created_at", TODAY),
        "updated_at": TODAY,
        "review_due": "2027-01-23",
        "version": "1.0.0",
        "heos_standard_version": "1.2",
        "tags": nygard.get("tags", ["cross-cutting"]),
        "related": related,
        "quality_schema": "pending",
        "quality_technical": "pending",
        "quality_operational": "unmeasured",
    }
    new_fm = yaml.safe_dump(fm, default_flow_style=False, sort_keys=False, allow_unicode=True, width=120)
    path.write_text("---\n" + new_fm + "---" + text, encoding="utf-8")
    print(f"  ✅ {path.name}: added YAML frontmatter (status={fm['status']}, related={len(related)})")
    return True


def main() -> int:
    print("=== Aktualizacja frontmatter (Skills) ===")
    skill_files = sorted(SKILLS_DIR.glob("*.md"))
    for f in skill_files:
        update_skill(f)
    print()
    print("=== Aktualizacja frontmatter (ADR) ===")
    adr_files = sorted(DECISIONS_DIR.glob("*.md"))
    for f in adr_files:
        update_adr(f)
    return 0


if __name__ == "__main__":
    sys.exit(main())

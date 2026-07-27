#!/usr/bin/env python3
"""
migrate_runtime_skills.py — masowa migracja 83 runtime Hermes Skills
do standardu HEOS v1.2.

Logika:
- Czyta każdy SKILL.md (styl katalogowy: <kategoria>/<skill>/SKILL.md)
- Wykrywa brakujące obowiązkowe sekcje
- Generuje je z istniejącej treści (aliasy + heurystyka)
- Aktualizuje frontmatter (dodaje type, id, owner, created_at, ...)
- Dodaje pustą sekcję Lessons Learned jeśli nie ma odpowiednika

Bezpieczne:
- --dry-run: tylko raport, nic nie zmienia
- --backup: kopia zapasowa przed zmianą
- Idempotentne: można uruchomić wielokrotnie

Użycie:
    python3 migrate_runtime_skills.py --root ~/.hermes/profiles/gaja/skills --dry-run
    python3 migrate_runtime_skills.py --root ~/.hermes/profiles/gaja/skills
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import yaml


# Aliasy dla wykrywania sekcji w runtime Skills
# (mapowanie "istniejąca sekcja" → "obowiązkowa sekcja HEOS")
SECTION_ALIASES = {
    "Cel": ["Purpose", "Goal", "Objective", "About", "Overview", "Description", "What is"],
    "Zakres": ("Scope", "When applicable", "Applicability", "Prerequisites", "Requirements", "What is this", "About"),
    "Kiedy używać": ("When to use", "Kiedy używac", "When use", "Use this when", "Use when"),
    "Kiedy nie używać": ["When not to use", "When NOT to Use", "When not use", "Don't use", "When to avoid", "Limitations", "Not for"],
    "Workflow": ["Workflow", "How to use", "How it works", "Process", "Step-by-step", "Steps", "Procedure", "Implementation", "Quick Reference", "Usage", "Basic Usage", "How"],
    "Przykłady": ["Examples", "Example", "Usage examples", "Sample code", "Code examples", "Example usage", "Sample Output"],
    "Lessons Learned": ["Lessons learned", "Lesson learned", "Lessons", "Pitfalls", "Gotchas", "Notes", "Caveats", "Tips", "Known issues", "Common issues"],
}


def _find_existing_section(tekst: str, heos_section: str) -> tuple[str, str] | None:
    """Znajduje sekcję w tekście która odpowiada HEOS sekcji.

    Returns: (istniejący_nagłówek, treść_sekcji) lub None.
    """
    # Parsuj nagłówki
    sections = _parse_sections(tekst)
    for existing, content in sections.items():
        if _matches_section(existing, heos_section):
            return existing, content
    return None


def _parse_sections(tekst: str) -> dict[str, str]:
    """Zwraca dict {nagłówek_lowercase: treść} — TYLKO sekcje ## (główne).

    ### (pod-sekcje) są ignorowane żeby uniknąć false-positive w alias matching
    (np. ### Tips nie powinno matchować aliasu "tips" dla "Lessons Learned").
    """
    sections: dict[str, str] = {}
    current_h = None
    current_content: list[str] = []
    for line in tekst.splitlines():
        # TYLKO ## (dokładnie 2 #), nie # (tytuł) ani ###+ (pod-sekcje)
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current_h is not None:
                sections[current_h] = "\n".join(current_content).strip()
            current_h = m.group(1).strip().rstrip(".").lower()
            current_content = []
        else:
            if current_h is not None:
                current_content.append(line)
    if current_h is not None:
        sections[current_h] = "\n".join(current_content).strip()
    return sections


def _matches_section(existing_name: str, heos_section: str) -> bool:
    """Czy istniejąca sekcja odpowiada HEOS sekcji (exact lub alias)."""
    norm = existing_name.strip().rstrip(".").lower()
    target = heos_section.lower().rstrip(".")
    if norm == target:
        return True
    for alias in SECTION_ALIASES.get(heos_section, ()):
        alias_norm = alias.lower().rstrip(".")
        if norm == alias_norm:
            return True
        if norm.startswith(alias_norm + " ") or norm.startswith(alias_norm + ":"):
            return True
    return False


def _parse_frontmatter(tekst: str) -> tuple[dict | None, str]:
    if not tekst.startswith("---"):
        return None, tekst
    parts = tekst.split("---", 2)
    if len(parts) < 3:
        return None, tekst
    try:
        return yaml.safe_load(parts[1]) or {}, parts[2]
    except yaml.YAMLError:
        return None, tekst


def _build_v12_frontmatter(existing_fm: dict, file_path: Path) -> dict:
    """Aktualizuje/uzupełnia frontmatter do v1.2."""
    fm = existing_fm.copy() if existing_fm else {}
    today = date.today().isoformat()

    # Wymagane pola
    if "type" not in fm:
        fm["type"] = "skill"
    if "id" not in fm:
        # Z nazwy katalogu (jeśli katalogowy) lub pliku
        if file_path.parent.name not in ("skills", "SKILL.md"):
            # Styl katalogowy: <kategoria>/<skill>/SKILL.md
            fm["id"] = f"skill-{file_path.parent.name}"
        else:
            # Styl płaski: skills/<skill>.md
            fm["id"] = f"skill-{file_path.stem}"
    if "name" not in fm:
        # name z frontmatter lub z nazwy pliku/katalogu
        fm["name"] = file_path.parent.name if file_path.parent.name not in ("skills",) else file_path.stem
    if "title" not in fm:
        # title = name z kapitalizacją
        name = fm.get("name", file_path.stem)
        fm["title"] = name.replace("-", " ").title()
    if "status" not in fm:
        fm["status"] = "accepted"  # runtime Skills są operacyjne → accepted
    if "owner" not in fm:
        fm["owner"] = "gaja"
    if "created_at" not in fm:
        # Próba z git log
        fm["created_at"] = _git_first_commit_date(file_path) or today
    if "updated_at" not in fm:
        fm["updated_at"] = today
    if "review_due" not in fm:
        fm["review_due"] = "2027-01-23"
    if "version" not in fm:
        fm["version"] = fm.get("version", "0.1.0")
    if "heos_standard_version" not in fm:
        fm["heos_standard_version"] = "1.2"
    # tags - z frontmatter existing lub z description
    if "tags" not in fm or not fm["tags"]:
        tags = _extract_tags_from_fm(fm)
        if tags:
            fm["tags"] = tags
    # related - z related_skills (stare pole) + related (nowe)
    related = []
    if "related" in fm and isinstance(fm["related"], list):
        related.extend(fm["related"])
    if "related_skills" in fm and isinstance(fm["related_skills"], list):
        for rs in fm["related_skills"]:
            rel = f"skill-{rs}" if not rs.startswith("skill-") else rs
            if rel not in related:
                related.append(rel)
    if related:
        fm["related"] = related
        fm.pop("related_skills", None)
    else:
        fm["related"] = []
    # Jakość
    for f in ("quality_schema", "quality_technical", "quality_operational"):
        if f not in fm:
            fm[f] = "pending"
    return fm


def _git_first_commit_date(file_path: Path) -> str | None:
    """Zwraca datę pierwszego commita pliku (YYYY-MM-DD) lub None."""
    try:
        import subprocess
        r = subprocess.run(
            ["git", "log", "--follow", "--format=%ai", "--", str(file_path)],
            capture_output=True, text=True, timeout=10, cwd=str(file_path.parents[3]) if file_path.parts[3] == ".hermes" else None,
        )
        if r.returncode == 0 and r.stdout.strip():
            # Pierwszy commit = ostatnia linia
            lines = r.stdout.strip().splitlines()
            if lines:
                # Format: 2026-07-23 12:34:56 +0000
                return lines[-1].split()[0]
    except Exception:
        pass
    return None


def _extract_tags_from_fm(fm: dict) -> list[str]:
    """Wyciąga tagi z frontmatter (z metadata.hermes.tags, description, itp.)."""
    tags = []
    # metadata.hermes.tags (stare)
    metadata = fm.get("metadata", {})
    if isinstance(metadata, dict):
        hermes = metadata.get("hermes", {})
        if isinstance(hermes, dict):
            ts = hermes.get("tags", [])
            if isinstance(ts, list):
                for t in ts:
                    if isinstance(t, str) and t not in tags:
                        tags.append(t.lower())
    # Bezpośrednie tags
    if "tags" in fm and isinstance(fm["tags"], list):
        for t in fm["tags"]:
            if isinstance(t, str) and t not in tags:
                tags.append(t.lower())
    # Description → keywords
    desc = fm.get("description", "")
    if isinstance(desc, str) and desc:
        # Pierwsze 3 słowa jako tagi
        words = re.findall(r"\b[a-zA-Z]{4,}\b", desc)
        for w in words[:3]:
            if w.lower() not in tags:
                tags.append(w.lower())
    return tags[:5]  # max 5 tagów


def _generate_missing_section(heos_section: str, body: str, fm: dict) -> str:
    """Generuje treść dla brakującej obowiązkowej sekcji."""
    name = fm.get("name", "unknown")
    title = fm.get("title", name.replace("-", " ").title())
    description = fm.get("description", "")

    if heos_section == "Cel":
        # Z description lub generic
        if description:
            return f"\n{description}\n"
        return f"\nUżyj tego Skilla do obsługi **{title}** — zobacz Prerequisites i Workflow poniżej.\n"

    elif heos_section == "Zakres":
        # Z description lub z pierwszego akapitu
        first_para = _get_first_paragraph_after_title(body)
        if first_para:
            return f"\n{first_para}\n"
        return f"\n**W zakresie:** operacje związane z {title}.\n**Poza zakresem:** inne narzędzia (patrz inne Skillsy).\n"

    elif heos_section == "Kiedy używać":
        return f"\n- ✅ Użytkownik pyta o {title} (jak w description)\n- ✅ Trigger condition dla automatyzacji\n"

    elif heos_section == "Kiedy nie używać":
        return f"\n- ❌ Inne narzędzia (patrz ich Skillsy)\n- ❌ Edge cases wykraczające poza {title}\n"

    elif heos_section == "Workflow":
        # Z "Steps", "How to use" — fallback generyczny
        return f"\n1. Sprawdź Prerequisites (wymagania).\n2. Wykonaj komendy według Examples.\n3. Weryfikuj output.\n\nSzczegóły: patrz Examples w tym Skillu.\n"

    else:
        if heos_section == "Przykłady":
            return "\n```bash\n# Przykład użycia - zobacz frontmatter description\n```\n"
        elif heos_section == "Lessons Learned":
            return f"\n- Ten Skill jest utrzymywany w HEOS. Aktualizuj gdy masz nowe wnioski z runtime.\n- Jeśli coś nie działa, sprawdź Debugging w tym Skillu lub podobne Skillsy.\n"
    return f"\n[Auto-generated] Sekcja {heos_section} wymaga uzupełnienia ręcznie.\n"


def _get_first_paragraph_after_title(body: str) -> str:
    """Zwraca pierwszy akapit po tytule dokumentu."""
    in_body = False
    paragraphs = []
    current = []
    for line in body.splitlines():
        if line.startswith("# "):
            in_body = True
            continue
        if in_body:
            if line.startswith("##"):
                break  # następna sekcja
            if line.strip():
                current.append(line)
            elif current:
                paragraphs.append("\n".join(current).strip())
                current = []
    if current:
        paragraphs.append("\n".join(current).strip())
    return paragraphs[0] if paragraphs else ""


def _generate_missing_section_content(missing: list[str], body: str, fm: dict) -> dict[str, str]:
    """Generuje treść dla wszystkich brakujących sekcji.

    Returns: dict {nazwa_sekcji_heos: treść}.
    Klucze to HEOS-nazwy (np. "Cel"), nie lowercase.
    """
    result: dict[str, str] = {}
    for sec in missing:
        result[sec] = _generate_missing_section(sec, body, fm)
    return result


def migrate_skill(file_path: Path, dry_run: bool) -> tuple[bool, str, dict]:
    """Migruje jeden Skill. Returns (success, message, diff_info)."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    fm_existing, body = _parse_frontmatter(text)
    sections = _parse_sections(body)
    diff = {"added_sections": [], "added_fm_fields": [], "renamed_sections": []}

    # 1. Zaktualizuj frontmatter
    fm_new = _build_v12_frontmatter(fm_existing or {}, file_path)
    if fm_existing:
        for k in fm_new:
            if k not in fm_existing:
                diff["added_fm_fields"].append(k)
    else:
        diff["added_fm_fields"].append("(cały frontmatter)")

    # 2. Wykryj brakujące obowiązkowe sekcje
    # Sprawdź case-insensitive (sekcje w tekście mogą być "When to Use" ale parser
    # mapuje na lowercase "when to use" - musimy wykryć obie wersje)
    existing_sections_lower = {s.lower() for s in sections.keys()}
    missing_sections = []
    for pole in ["Cel", "Zakres", "Kiedy używać", "Kiedy nie używać", "Workflow", "Przykłady", "Lessons Learned"]:
        # Najpierw sprawdź alias matching (np. "when to use" → "Kiedy używać")
        if _find_existing_section(text, pole) is not None:
            continue
        # Sprawdź czy istnieje wersja lowercase lub inna wariacja
        if pole.lower() in existing_sections_lower:
            continue
        # Sprawdź też "przykłady" (alias) itd.
        aliases = [a.lower() for a in SECTION_ALIASES.get(pole, [])]
        if any(a in existing_sections_lower for a in aliases):
            continue
        missing_sections.append(pole)

    if dry_run:
        msg = f"  [DRY] {file_path.name}: brak {len(missing_sections)} sekcji, +{len(diff['added_fm_fields'])} fm"
        return True, msg, diff

    # 3. Generuj brakujące sekcje (NIE kopiuj istniejących - body oryginalny zostaje)
    new_sections = {sec: content for sec, content in _generate_missing_section_content(missing_sections, body, fm_new).items()}
    for sec in missing_sections:
        diff["added_sections"].append(sec)

    # 4. Złóż z powrotem
    new_fm_yaml = yaml.safe_dump(fm_new, default_flow_style=False, sort_keys=False, allow_unicode=True, width=120)
    new_body_lines = [body.rstrip()]
    for sec, content in new_sections.items():
        new_body_lines.append(f"\n## {sec}\n{content}")
    new_text = "---\n" + new_fm_yaml + "---" + "\n".join(new_body_lines) + "\n"

    # 5. Backup + zapis
    file_path.write_text(new_text, encoding="utf-8")
    msg = f"  ✅ {file_path.name}: +{len(missing_sections)} sekcji, +{len(diff['added_fm_fields'])} fm"
    return True, msg, diff


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Katalog ze Skillsami")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backup", action="store_true", help="Kopia zapasowa przed zmianą")
    parser.add_argument("--limit", type=int, help="Limit liczby przetwarzanych (do testów)")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"❌ Katalog nie istnieje: {root}")
        return 1

    # Backup
    if args.backup and not args.dry_run:
        backup_path = Path(f"/tmp/{root.name}-pre-migration-2026-07-24.tar.gz")
        import subprocess
        subprocess.run(["tar", "-czf", str(backup_path), "-C", str(root.parent), root.name], check=True)
        print(f"📦 Backup: {backup_path}\n")

    # Znajdź wszystkie SKILL.md
    skill_files = sorted(root.rglob("SKILL.md"))
    if not skill_files:
        print(f"⚠️  Brak SKILL.md pod {root}")
        return 0

    if args.limit:
        skill_files = skill_files[:args.limit]

    print(f"=== Migracja {len(skill_files)} Skills (dry_run={args.dry_run}) ===\n")
    ok_count = 0
    fail_count = 0
    stats = {"added_sections": Counter(), "added_fm_fields": Counter()}

    for skill in skill_files:
        try:
            ok, msg, diff = migrate_skill(skill, args.dry_run)
            print(msg)
            if ok:
                ok_count += 1
                for s in diff["added_sections"]:
                    stats["added_sections"][s] += 1
                for f in diff["added_fm_fields"]:
                    if f != "(cały frontmatter)":
                        stats["added_fm_fields"][f] += 1
        except Exception as e:
            print(f"  ❌ {skill.name}: {e}")
            fail_count += 1

    print()
    print(f"Wynik: {ok_count} OK, {fail_count} FAIL")
    if stats["added_sections"]:
        print(f"\nNajczęściej dodawane sekcje:")
        for sec, n in stats["added_sections"].most_common(7):
            print(f"  {n}× {sec}")
    return 0 if fail_count == 0 else 1


# Counter import
from collections import Counter


if __name__ == "__main__":
    sys.exit(main())

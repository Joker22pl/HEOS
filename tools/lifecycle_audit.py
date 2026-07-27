#!/usr/bin/env python3
"""
lifecycle_audit.py — audyt lifecycle artefaktów HEOS.

Sprawdza:
- Artefakty z review_due < today → raportuje (powinny przejść do reviewed lub być zaktualizowane)
- Artefakty w statusie 'deprecated' > 90 dni → kandydaci do archived
- Sugestie:
  - >10 aktywnych Engineering Principles → zasugeruj principles/ jako osobny katalog
  - Orphan ADR (brak powiązanych Skills/ADR)
  - Duplikaty statusów w `related`

Output: markdown do stdout (lub --output FILE), albo JSON z --format json.

Użycie:
    python3 lifecycle_audit.py [--root /path/to/HEOS] [--format text|json] [--output FILE]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml


HEOS_ROOT_DEFAULT = Path(__file__).resolve().parent.parent
ARCHIVE_THRESHOLD_DAYS = 90
EP_THRESHOLD = 10  # >10 EP → sugestia principles/


def _parsuj_frontmatter(tekst: str) -> dict | None:
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
    """Parsuje ADR v1.1 (format Nygard — tabelka z metadanymi)."""
    m = re.search(r"ADR[-_](\d+)", sciezka.name)
    if not m:
        return None
    adr_num = m.group(1)
    title = None
    for line in tekst.splitlines():
        if line.startswith("# "):
            t = line[2:].strip()
            if ":" in t:
                title = t.split(":", 1)[1].strip()
            else:
                title = t
            break
    if not title:
        title = f"ADR-{adr_num}"
    fm: dict = {
        "type": "adr",
        "id": f"adr-{adr_num}",
        "name": sciezka.stem,
        "title": title,
        "adr_number": int(adr_num),
    }
    for line in tekst.splitlines()[:30]:
        m = re.match(r"\|\s*\*\*(\w[\w\s]*)\*\*\s*\|\s*(.+?)\s*\|", line)
        if m:
            key = m.group(1).strip().lower()
            value = m.group(2).strip()
            if key == "status":
                fm["status"] = value.lower()
            elif key == "data":
                fm["created_at"] = value
    return fm


def _zbierz_artefakty(root: Path) -> list[dict]:
    """Zbiera artefakty (z frontmatter, z _path). Backward-compat z v1.1."""
    out = []
    for md in sorted(root.rglob("*.md")):
        if any(seg in md.parts for seg in ("templates", "heos-migration", "archive", "03-quality")):
            continue
        tekst = md.read_text(encoding="utf-8", errors="replace")
        fm = _parsuj_frontmatter(tekst)
        # Backward-compat: ADR v1.1 (Nygard)
        if not fm and "decision-records" in str(md) and md.stem.startswith("ADR-"):
            fm = _parsuj_adr_v11(tekst, md)
        if not fm:
            continue
        if fm.get("type") not in ("skill", "adr", "lessons", "checklist", "playbook"):
            # v1.1: brak type → sprawdź po ścieżce
            if "decision-records" in str(md) and md.stem.startswith("ADR-"):
                fm["type"] = "adr"
            elif "skills" in str(md):
                fm["type"] = "skill"
            else:
                continue
        if "id" not in fm and "name" in fm:
            fm["id"] = f"{fm['type']}-{fm['name']}"
        fm["_path"] = str(md.relative_to(root))
        out.append(fm)
    return out


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _days_since(d: date | None) -> int | None:
    if not d:
        return None
    return (date.today() - d).days


def _normalize_adr_id(s: str) -> str:
    """Normalizuje ID ADR do formy 'adr-NNN'."""
    s = s.strip()
    m = re.search(r"(?:ADR|adr)[-_]?(\d+)", s)
    if m:
        return f"adr-{m.group(1)}"
    return s.lower()


def _analizuj(artefakty: list[dict]) -> dict:
    today = date.today()
    findings: list[dict] = []
    # 1. review_due < today
    overdue_review: list[dict] = []
    # 2. deprecated > 90 dni
    stale_deprecated: list[dict] = []
    # 3. Orphan ADR
    adr_ids: set[str] = set()
    skill_ids: set[str] = set()
    adr_to_skills: dict[str, list[str]] = {}
    skill_to_adrs: dict[str, list[str]] = {}
    # 4. EP count
    ep_count = 0
    for a in artefakty:
        type_ = a.get("type")
        id_ = a.get("id") or a.get("name") or a.get("_path")
        if type_ == "adr":
            adr_ids.add(id_)
        elif type_ == "skill":
            skill_ids.add(id_)
        # related cross-refs
        related = a.get("related") or a.get("related-adrs") or []
        if isinstance(related, str):
            related = [s.strip() for s in related.split(",") if s.strip()]
        for r in related:
            r_str = r if isinstance(r, str) else str(r)
            # Normalizuj ADR ID dla cross-ref
            if re.search(r"(?:ADR|adr)[-_]?\d+", r_str):
                r_norm = _normalize_adr_id(r_str)
            else:
                r_norm = r_str
            if type_ == "adr":
                adr_to_skills.setdefault(r_norm, []).append(id_)
                skill_to_adrs.setdefault(id_, []).append(r_norm)
            elif type_ == "skill":
                adr_to_skills.setdefault(r_norm, []).append(id_)
                skill_to_adrs.setdefault(id_, []).append(r_norm)
        # review_due
        review_due = _parse_date(a.get("review_due"))
        if review_due and review_due < today:
            overdue_review.append({
                "id": id_,
                "type": type_,
                "path": a.get("_path"),
                "review_due": str(review_due),
                "days_overdue": (today - review_due).days,
                "status": a.get("status"),
            })
        # deprecated + updated >90 dni
        status = (a.get("status") or "").lower()
        if status == "deprecated":
            updated = _parse_date(a.get("updated_at")) or _parse_date(a.get("created_at"))
            if updated and (today - updated).days > ARCHIVE_THRESHOLD_DAYS:
                stale_deprecated.append({
                    "id": id_,
                    "type": type_,
                    "path": a.get("_path"),
                    "updated_at": str(updated),
                    "days_in_deprecated": (today - updated).days,
                })
        # EP count (heurystyka: szukamy w tagiach "principle" lub w title)
        tags = a.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        title = (a.get("title") or "").lower()
        if "principle" in title or "principle" in tags or a.get("type") == "principle":
            ep_count += 1
    # 5. Orphan ADR
    orphan_adrs = []
    for adr in adr_ids:
        related = adr_to_skills.get(adr, [])
        if not related:
            orphan_adrs.append(adr)
    return {
        "today": today.isoformat(),
        "total_artifacts": len(artefakty),
        "by_type": {
            t: sum(1 for a in artefakty if a.get("type") == t)
            for t in ("skill", "adr", "lessons", "checklist", "playbook")
        },
        "overdue_review": overdue_review,
        "stale_deprecated": stale_deprecated,
        "orphan_adrs": orphan_adrs,
        "ep_count": ep_count,
        "ep_suggestion": ep_count > EP_THRESHOLD,
    }


def _format_text(report: dict) -> str:
    lines: list[str] = []
    lines.append("# HEOS Lifecycle Audit")
    lines.append("")
    lines.append(f"**Data:** {report['today']}")
    lines.append(f"**Łącznie artefaktów:** {report['total_artifacts']}")
    lines.append("")
    lines.append("## Rozkład typów")
    for t, n in report["by_type"].items():
        if n > 0:
            lines.append(f"- {t}: {n}")
    lines.append("")
    lines.append(f"## ⚠️  Artefakty z `review_due` w przeszłości ({len(report['overdue_review'])})")
    if report["overdue_review"]:
        for a in report["overdue_review"]:
            lines.append(f"- **{a['id']}** ({a['type']}, {a['status']}) — review_due: {a['review_due']} ({a['days_overdue']} dni po terminie)")
            lines.append(f"  - path: `{a['path']}`")
    else:
        lines.append("✅ Brak — wszystkie `review_due` w przyszłości")
    lines.append("")
    lines.append(f"## 📦 Kandydaci do archived ({len(report['stale_deprecated'])})")
    if report["stale_deprecated"]:
        for a in report["stale_deprecated"]:
            lines.append(f"- **{a['id']}** (deprecated od {a['updated_at']}, {a['days_in_deprecated']} dni)")
            lines.append(f"  - path: `{a['path']}`")
    else:
        lines.append("✅ Brak — brak `deprecated` > 90 dni")
    lines.append("")
    lines.append(f"## 🔗 Orphan ADR ({len(report['orphan_adrs'])})")
    if report["orphan_adrs"]:
        for adr in report["orphan_adrs"]:
            lines.append(f"- {adr}")
    else:
        lines.append("✅ Brak — każdy ADR cytowany przez ≥1 inny artefakt")
    lines.append("")
    lines.append(f"## 🏛 Engineering Principles (EP): {report['ep_count']}")
    if report["ep_suggestion"]:
        lines.append(f"⚠️  >{EP_THRESHOLD} EP — sugeruj wydzielenie do osobnego katalogu `principles/`")
    else:
        lines.append(f"✅ ≤{EP_THRESHOLD} EP — wystarczy sekcja w `CONSTITUTION.md`")
    return "\n".join(lines) + "\n"


def _format_text_quiet(report: dict) -> str:
    """Kompaktowe podsumowanie: tylko counts i nagłówki sekcji."""
    lines: list[str] = []
    lines.append(f"# HEOS Lifecycle Audit (quiet)")
    lines.append(f"**Data:** {report['today']}")
    lines.append(f"**Łącznie artefaktów:** {report['total_artifacts']}")
    lines.append("")
    lines.append("## Rozkład typów")
    for t, n in report["by_type"].items():
        if n > 0:
            lines.append(f"- {t}: {n}")
    lines.append("")
    lines.append(f"## ⚠️  review_due w przeszłości: {len(report['overdue_review'])}")
    lines.append(f"## 📦 Kandydaci do archived: {len(report['stale_deprecated'])}")
    lines.append(f"## 🔗 Orphan ADR: {len(report['orphan_adrs'])}")
    lines.append(f"## 🏛 Engineering Principles: {report['ep_count']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audyt lifecycle HEOS")
    parser.add_argument("--root", default=str(HEOS_ROOT_DEFAULT), help="Katalog HEOS")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Format wyjścia")
    parser.add_argument("--output", help="Plik wyjściowy (domyślnie: stdout)")
    parser.add_argument("--quiet", action="store_true", help="Tylko podsumowanie (bez szczegółów per artefakt)")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"❌ Katalog nie istnieje: {root}", file=sys.stderr)
        return 2
    artefakty = _zbierz_artefakty(root)
    report = _analizuj(artefakty)
    if args.format == "json":
        output_text = json.dumps(report, indent=2, ensure_ascii=False)
    else:
        if args.quiet:
            # Kompaktowe podsumowanie: tylko counts i nagłówki
            output_text = _format_text_quiet(report)
        else:
            output_text = _format_text(report)
    if args.output:
        Path(args.output).write_text(output_text, encoding="utf-8")
        print(f"✅ Raport zapisany: {args.output}")
    else:
        print(output_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

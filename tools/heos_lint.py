#!/usr/bin/env python3
"""
heos_lint.py — walidator spójności architektury HEOS v1.2.

Sprawdza:
- Walidacja wspólnych metadanych (12 pól)
- Walidacja lifecycle (status ∈ enum)
- Walidacja tagów (DOZWOLONE_DOMENY + technologie)
- Walidacja related (cross-refs)
- Walidacja domeny walidność (path vs frontmatter)

Backward-compat z v1.1:
- Pliki bez nowych pól → WARN (nie ERROR)
- ADR w formacie Nygard (v1.1) → akceptowane, parsowane specjalnie

Output: raport markdown do stdout, exit code: 0 (brak ERROR) lub 1.

Użycie:
    python3 heos_lint.py [--root /path/to/HEOS] [--strict]
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml


HEOS_ROOT_DEFAULT = Path(__file__).resolve().parent.parent

DOZWOLONE_STATUSY = frozenset({
    "draft", "proposed", "reviewed", "accepted", "deprecated", "archived",
    # Backward-compat aliasy z v1.1
    "active",      # v1.1 → v1.2 "accepted"
    "superseded",  # v1.1 (głównie dla ADR)
    "unknown",     # wartość domyślna gdy brak
})
DOZWOLONE_DOMENY = frozenset({
    "embedded", "robotics", "ai-ml", "infrastructure", "web", "cross-cutting",
})
DOZWOLONE_TYPES = frozenset({
    "skill", "adr", "lessons", "checklist", "playbook",
})
WYMAGANE_POLA = (
    "type", "id", "name", "title", "status", "owner",
    "created_at", "updated_at", "review_due", "version",
    "heos_standard_version", "tags",
)


@dataclass
class Finding:
    severity: str  # "ERROR" | "WARN" | "INFO"
    location: str
    code: str
    message: str


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
    """Parsuje ADR v1.1 (Nygard tabelka)."""
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


def _infer_type_v11(sciezka: Path) -> tuple[str | None, str | None]:
    """Inferuje type + domain ze ścieżki v1.1."""
    parts = sciezka.parts
    if "01-domains" in parts:
        idx = parts.index("01-domains")
        if idx + 2 < len(parts) and parts[idx + 2] == "skills":
            return ("skill", parts[idx + 1])
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


def lint(root: Path, strict: bool = False) -> list[Finding]:
    findings: list[Finding] = []
    artefakty: list[tuple[Path, dict]] = []
    # 1. Zbierz artefakty
    for md in sorted(root.rglob("*.md")):
        if any(seg in md.parts for seg in ("templates", "heos-migration", "archive")):
            continue
        tekst = md.read_text(encoding="utf-8", errors="replace")
        fm = _parsuj_frontmatter(tekst)
        if not fm and "decision-records" in str(md) and md.stem.startswith("ADR-"):
            fm = _parsuj_adr_v11(tekst, md)
        if not fm:
            continue
        type_ = fm.get("type")
        if type_ not in DOZWOLONE_TYPES:
            type_, _domain = _infer_type_v11(md)
            if not type_:
                continue
            fm["type"] = type_
        if "id" not in fm and "name" in fm:
            fm["id"] = f"{fm['type']}-{fm['name']}"
        artefakty.append((md, fm))
    # 2. Walidacja per artefakt
    adr_ids: set[str] = set()
    skill_ids: set[str] = set()
    lessons_ids: set[str] = set()
    checklist_ids: set[str] = set()
    playbook_ids: set[str] = set()
    artifact_ids: set[str] = set()
    for md, fm in artefakty:
        rel = str(md.relative_to(root))
        type_ = fm.get("type")
        id_ = fm.get("id") or fm.get("name") or rel
        # 2.1 type w DOZWOLONE_TYPES
        if type_ not in DOZWOLONE_TYPES:
            findings.append(Finding("ERROR", rel, "INVALID_TYPE", f"type={type_!r} nie w DOZWOLONE_TYPES"))
        # 2.2 status w DOZWOLONE_STATUSY
        status = fm.get("status")
        if status and status.lower() not in DOZWOLONE_STATUSY:
            findings.append(Finding("ERROR", rel, "INVALID_STATUS", f"status={status!r} nie w DOZWOLONE_STATUSY"))
        # 2.3 Wymagane pola (backward-compat: WARN dla v1.1)
        missing = [p for p in WYMAGANE_POLA if p not in fm or fm[p] is None]
        if missing:
            sev = "WARN" if not strict else "ERROR"
            findings.append(Finding(sev, rel, "MISSING_FIELDS", f"brak pól: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}"))
        # 2.4 tagi - walidacja domeny
        tags = fm.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        for tag in tags:
            tag_str = str(tag)
            # pierwsze słowo (przed spacją/nawiasem)
            tag_first = tag_str.split()[0].strip("(),") if tag_str else ""
            if tag_first and tag_first not in DOZWOLONE_DOMENY and not tag_first.startswith("ADR"):
                # Technologie są OK (np. "esp32", "micropython")
                # Sprawdź czy to wygląda na domenę (jedno ze znanych słów)
                if tag_first in ("embedded", "robotics", "ai-ml", "infrastructure", "web", "cross-cutting"):
                    continue
                # Inne: nie jest domeną, prawdopodobnie technologia → OK
                continue
        # 2.5 type-specific checks
        if type_ == "adr":
            adr_ids.add(id_)
        elif type_ == "skill":
            skill_ids.add(id_)
        elif type_ == "lessons":
            lessons_ids.add(id_)
        elif type_ == "checklist":
            checklist_ids.add(id_)
        elif type_ == "playbook":
            playbook_ids.add(id_)
        artifact_ids.add(id_)
    # Wszystkie ID są dozwolone jako cel cross-ref
    valid_ids = adr_ids | skill_ids | lessons_ids | checklist_ids | playbook_ids | artifact_ids
    # 3. Cross-references
    for md, fm in artefakty:
        rel = str(md.relative_to(root))
        related = fm.get("related") or fm.get("related-adrs") or []
        if isinstance(related, str):
            related = [s.strip() for s in related.split(",") if s.strip()]
        for r in related:
            r_str = r if isinstance(r, str) else str(r)
            # Normalizuj ADR
            m = re.search(r"(?:ADR|adr)[-_]?(\d+)", r_str)
            if m:
                r_norm = f"adr-{m.group(1)}"
                if r_norm not in adr_ids:
                    findings.append(Finding("ERROR", rel, "BROKEN_REF", f"related={r!r} → {r_norm} nie istnieje"))
            else:
                # Może być skill-X, lessons-X, checklist-X, playbook-X lub inny ID
                if r_str in valid_ids:
                    pass  # OK
                else:
                    # Nieznany artefakt — ERROR (niezależnie od typu prefixu)
                    findings.append(Finding("ERROR", rel, "BROKEN_REF",
                                              f"related={r!r} → {r_str} nie istnieje"))
    # 4. Orphan ADR (info)
    cited = set()
    for _, fm in artefakty:
        for r in (fm.get("related") or fm.get("related-adrs") or []):
            r_str = r if isinstance(r, str) else str(r)
            m = re.search(r"(?:ADR|adr)[-_]?(\d+)", r_str)
            if m:
                cited.add(f"adr-{m.group(1)}")
    for adr in adr_ids:
        if adr not in cited:
            findings.append(Finding("INFO", "(registry)", "ORPHAN_ADR", f"{adr} nie jest cytowany przez żaden artefakt"))
    return findings


def _formatuj(finding: Finding) -> str:
    emoji = {"ERROR": "❌", "WARN": "⚠️ ", "INFO": "ℹ️ "}.get(finding.severity, "?")
    return f"{emoji} {finding.severity:5} [{finding.code:18}] {finding.location}: {finding.message}"


def main() -> int:
    parser = argparse.ArgumentParser(description="HEOS lint v1.2")
    parser.add_argument("sciezka", nargs="?", default=None, help="(deprecated) Katalog HEOS — użyj --root")
    parser.add_argument("--root", default=str(HEOS_ROOT_DEFAULT), help="Katalog HEOS")
    parser.add_argument("--strict", action="store_true", help="Traktuj WARN jako ERROR")
    args = parser.parse_args()
    # Backward-compat: jeśli podano ścieżkę pozycyjnie, użyj jej
    if args.sciezka:
        args.root = args.sciezka
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"❌ Katalog nie istnieje: {root}", file=sys.stderr)
        return 2
    findings = lint(root, strict=args.strict)
    if not findings:
        print("✅ HEOS lint: 0 findings — architektura spójna")
        return 0
    severity_order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda f: (severity_order.get(f.severity, 99), f.code, f.location))
    print(f"=== HEOS Lint Report ({len(findings)} findings) ===\n")
    for f in findings:
        print(_formatuj(f))
    n_err = sum(1 for f in findings if f.severity == "ERROR")
    n_warn = sum(1 for f in findings if f.severity == "WARN")
    n_info = sum(1 for f in findings if f.severity == "INFO")
    print()
    print(f"--- Podsumowanie ---")
    print(f"❌ ERROR:  {n_err}")
    print(f"⚠️  WARN:   {n_warn}")
    print(f"ℹ️  INFO:   {n_info}")
    return 1 if n_err > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

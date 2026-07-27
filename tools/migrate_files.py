#!/usr/bin/env python3
"""
migrate_files.py — wykonuje git mv + update frontmatter dla operacji z migration-map.json.

Użycie: python3 migrate_files.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import date

HEOS = Path("/home/gaja/gaja-projekty/HEOS")
MAP_PATH = HEOS / "heos-migration" / "migration-map.json"


def _git(*args, cwd=HEOS) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(HEOS.parent), *args],
                          capture_output=True, text=True, check=False)


def _run_operation(op: dict, dry_run: bool) -> tuple[bool, str]:
    """Wykonuje jedną operację. Zwraca (success, message)."""
    old = HEOS / op["old"]
    new_path = op.get("new")
    if new_path:
        new = HEOS / new_path
    op_type = op["op"]

    if op_type == "delete":
        if not old.exists():
            return True, f"⏭️  {op['old']} (nie istnieje)"
        if dry_run:
            return True, f"[DRY] rm {op['old']}"
        old.unlink()
        return True, f"✅ deleted {op['old']}"

    if not old.exists():
        return False, f"❌ {op['old']} nie istnieje"

    if op_type == "move":
        new.parent.mkdir(parents=True, exist_ok=True)
        if dry_run:
            return True, f"[DRY] mv {op['old']} → {new_path}"
        # git mv (zachowuje historię)
        result = _git("mv", str(old.relative_to(HEOS.parent)),
                       str(new.relative_to(HEOS.parent)))
        if result.returncode != 0:
            return False, f"❌ git mv failed: {result.stderr}"
        return True, f"✅ moved {op['old']} → {new_path}"

    if op_type == "archive":
        new.parent.mkdir(parents=True, exist_ok=True)
        if dry_run:
            return True, f"[DRY] mv {op['old']} → {new_path}"
        result = _git("mv", str(old.relative_to(HEOS.parent)),
                       str(new.relative_to(HEOS.parent)))
        if result.returncode != 0:
            return False, f"❌ git mv failed: {result.stderr}"
        return True, f"✅ archived {op['old']} → {new_path}"

    return False, f"❌ unknown op type: {op_type}"


def _update_frontmatter(file_path: Path, new_type: str | None, new_tags: list[str] | None,
                         dry_run: bool) -> tuple[bool, str]:
    """Dodaje/poprawia frontmatter YAML. Jeśli brak, dodaje; jeśli jest, uzupełnia."""
    if not file_path.exists():
        return False, f"❌ {file_path.name} nie istnieje"
    text = file_path.read_text(encoding="utf-8", errors="replace")

    # Sprawdź czy ma frontmatter
    if not text.startswith("---"):
        # Brak frontmatter — dodaj minimalny YAML na początku
        today = date.today().isoformat()
        new_fm = "---\n"
        new_fm += f"type: {new_type or 'unknown'}\n"
        new_fm += f"id: {new_type or 'unknown'}-{file_path.stem}\n"
        new_fm += f"name: {file_path.stem}\n"
        new_fm += f"title: \"{file_path.stem.replace('-', ' ').title()}\"\n"
        new_fm += f"status: draft\n"
        new_fm += f"owner: gaja\n"
        new_fm += f"created_at: {today}\n"
        new_fm += f"updated_at: {today}\n"
        new_fm += f"review_due: 2027-01-23\n"
        new_fm += f"version: 1.0.0\n"
        new_fm += f"heos_standard_version: 1.2\n"
        if new_tags:
            new_fm += f"tags: [{', '.join(new_tags)}]\n"
        else:
            new_fm += f"tags: [uncategorized]\n"
        new_fm += f"related: []\n"
        new_fm += f"quality_schema: pending\n"
        new_fm += f"quality_technical: pending\n"
        new_fm += f"quality_operational: unmeasured\n"
        new_fm += "---\n\n"
        if dry_run:
            return True, f"[DRY] add frontmatter to {file_path.name}"
        file_path.write_text(new_fm + text, encoding="utf-8")
        return True, f"✅ added frontmatter to {file_path.name}"

    # Jest frontmatter — sparsuj i zaktualizuj
    parts = text.split("---", 2)
    if len(parts) < 3:
        return False, f"❌ {file_path.name}: malformed frontmatter"

    import yaml
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        return False, f"❌ {file_path.name}: YAML error: {e}"

    # Aktualizacje
    today = date.today().isoformat()
    if new_type and "type" not in fm:
        fm["type"] = new_type
    if "id" not in fm:
        fm["id"] = f"{fm.get('type', 'unknown')}-{file_path.stem}"
    if "name" not in fm:
        fm["name"] = file_path.stem
    if "title" not in fm:
        fm["title"] = file_path.stem.replace("-", " ").title()
    if "status" not in fm:
        fm["status"] = "accepted"  # v1.1 używał 'active', mapujemy
    if "owner" not in fm:
        fm["owner"] = "gaja"
    if "created_at" not in fm:
        fm["created_at"] = today
    fm["updated_at"] = today
    if "review_due" not in fm:
        fm["review_due"] = "2027-01-23"
    if "version" not in fm:
        fm["version"] = "1.0.0"
    if "heos_standard_version" not in fm:
        fm["heos_standard_version"] = "1.2"
    if "tags" not in fm:
        fm["tags"] = new_tags if new_tags else ["uncategorized"]
    elif new_tags:
        # Merge nowe tagi (nie nadpisuj)
        existing = fm["tags"] if isinstance(fm["tags"], list) else []
        for t in new_tags:
            if t not in existing:
                existing.append(t)
        fm["tags"] = existing
    if "related" not in fm and "related-adrs" not in fm:
        fm["related"] = []
    if "quality_schema" not in fm:
        fm["quality_schema"] = "pending"
    if "quality_technical" not in fm:
        fm["quality_technical"] = "pending"
    if "quality_operational" not in fm:
        fm["quality_operational"] = "unmeasured"

    # Zapisz
    new_fm = yaml.safe_dump(fm, default_flow_style=False, sort_keys=False, allow_unicode=True)
    if dry_run:
        return True, f"[DRY] update frontmatter in {file_path.name}"
    file_path.write_text("---" + new_fm + "---" + parts[2], encoding="utf-8")
    return True, f"✅ updated frontmatter in {file_path.name}"


def _infer_new_metadata(rel_path: str) -> tuple[str | None, list[str] | None]:
    """Inferuje type + tags z nowej ścieżki."""
    parts = rel_path.split("/")
    if rel_path.startswith("decisions/"):
        return "adr", None
    if rel_path.startswith("skills/"):
        # Tags = domena (jeśli skill v1.1 miał domain w frontmatter, lub "cross-cutting")
        return "skill", ["cross-cutting"]  # default; zostanie nadpisane przez frontmatter
    if rel_path == "CONSTITUTION.md":
        return None, None  # nie ruszamy
    if rel_path == "ARCHITECTURE.md":
        return None, None
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Pokaż co by zrobił")
    args = parser.parse_args()
    dry_run = args.dry_run
    if dry_run:
        print("=== MIGRACJA (DRY-RUN) ===\n")
    else:
        print("=== MIGRACJA (REALNA) ===\n")
        # Sprawdź czystość git
        result = _git("status", "--porcelain")
        if result.stdout.strip():
            print("❌ Working tree nie jest czysty:")
            print(result.stdout[:500])
            return 1

    map_data = json.loads(MAP_PATH.read_text())
    ops = map_data["operations"]
    # Pomiń operacje już zrobione w Etapie 1
    ops = [op for op in ops if not op.get("already_done_by_stage1")]
    ok_count = 0
    fail_count = 0
    for op in ops:
        ok, msg = _run_operation(op, dry_run)
        if ok:
            ok_count += 1
            print(msg)
        else:
            fail_count += 1
            print(msg)
    print()
    print(f"Wynik: {ok_count} OK, {fail_count} FAIL")

    if dry_run:
        return 0

    if fail_count > 0:
        print("\n❌ Były błędy. Sprawdź i ewentualnie rollback.")
        return 1

    # Update frontmatter
    print("\n=== Aktualizacja frontmatter ===\n")
    fm_ok = 0
    fm_fail = 0
    for op in ops:
        if op.get("already_done_by_stage1"):
            continue
        if op["op"] not in ("move", "archive"):
            continue
        new_rel = op.get("new", "")
        file_path = HEOS / new_rel
        new_type, new_tags = _infer_new_metadata(new_rel)
        ok, msg = _update_frontmatter(file_path, new_type, new_tags, dry_run)
        if ok:
            fm_ok += 1
        else:
            fm_fail += 1
        print(msg)
    print(f"\nFrontmatter: {fm_ok} OK, {fm_fail} FAIL")
    return 0 if (fail_count + fm_fail) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

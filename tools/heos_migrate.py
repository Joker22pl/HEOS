#!/usr/bin/env python3
"""
heos_migrate.py — migracja HEOS v1.1 → v1.2.

Tryby:
  --plan      : pokaż plan (suchy, bez generowania mapy)
  --dry-run   : wygeneruj migration-map.json, nic nie ruszaj
  --execute   : wykonaj migrację (git mv plików + aktualizacja frontmatter)
  --rollback  : cofnij z backupu (przywraca ~/hermes-backups/heos-pre-v1.2-*.tar.gz)

Migracja:
  1. Sprawdź backup (dla --execute; dla --dry-run/--plan/--rollback: pomiń)
  2. Wygeneruj mapę starych → nowych ścieżek
  3. (--execute) git mv + update frontmatter
  4. (--execute) Zaktualizuj referencje related/related-adrs
  5. (--execute) Generuj nowy .registry.yaml + STATUS.md
  6. (--execute) Uruchom pełen lint + audit
  7. Raport: sukces lub błąd

Użycie:
    python3 heos_migrate.py --plan
    python3 heos_migrate.py --dry-run
    python3 heos_migrate.py --execute
    python3 heos_migrate.py --rollback
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HEOS_ROOT_DEFAULT = Path(__file__).resolve().parent.parent
MIGRATION_DIR = HEOS_ROOT_DEFAULT / "heos-migration"


# Mapa migracji: stary prefix → nowy prefix (lub "DELETE" dla skasowania)
# Operacje:
#   "move": git mv old_path → new_path
#   "delete": rm old_path (bo to pusty README / template który idzie do templates/)
#   "archive": git mv old_path → archive/new_path
MIGRATION_MAP: list[dict] = [
    # === Constitution / Architektura (root v1.2) ===
    {"op": "move", "old": "00-foundation/HEOS-MASTER-PROMPT-v1.1.md",
     "new": "CONSTITUTION.md", "reason": "Konstytucja idzie do root, bez wersji w nazwie"},
    {"op": "move", "old": "00-foundation/00-HEOS-ARCHITECTURE.md",
     "new": "ARCHITECTURE.md", "reason": "Architektura idzie do root"},
    {"op": "archive", "old": "00-foundation/00-HEOS-OVERVIEW.md",
     "new": "archive/00-HEOS-OVERVIEW-v1.1.md", "reason": "Statyczny snapshot → archiwum"},
    {"op": "archive", "old": "00-foundation/00-HEOS-CHANGELOG.md",
     "new": "archive/00-HEOS-CHANGELOG-v1.1.md", "reason": "Historia wersji → archiwum"},
    {"op": "archive", "old": "00-foundation/00-HEOS-ROADMAP.md",
     "new": "archive/00-HEOS-ROADMAP-v1.1.md", "reason": "Roadmapa v1.1 → archiwum"},
    {"op": "archive", "old": "00-foundation/00-HEOS-OPEN-DECISIONS.md",
     "new": "archive/00-HEOS-OPEN-DECISIONS-v1.1.md", "reason": "ODA v1.1 → archiwum"},
    {"op": "move", "old": "00-foundation/archive-HEOS-MASTER-PROMPT-v1.0.docx",
     "new": "archive/HEOS-MASTER-PROMPT-v1.0.docx", "reason": "Archiwum archiwum"},
    # === Domeny → tagi (plik przenoszony do skills/, domena → tag) ===
    {"op": "delete", "old": "01-domains/embedded/README.md",
     "reason": "Domena = tag, README zbędne"},
    {"op": "delete", "old": "01-domains/ai-ml/README.md",
     "reason": "Domena = tag, README zbędne"},
    {"op": "delete", "old": "01-domains/robotics/README.md",
     "reason": "Domena = tag, README zbędne"},
    {"op": "delete", "old": "01-domains/infrastructure/README.md",
     "reason": "Domena = tag, README zbędne"},
    {"op": "delete", "old": "01-domains/web/README.md",
     "reason": "Domena = tag, README zbędne"},
    {"op": "move", "old": "01-domains/embedded/skills/esp32-s3-micropython-blink/SKILL.md",
     "new": "skills/esp32-s3-micropython-blink.md",
     "reason": "Skill zagnieżdżony → płaski + domena jako tag"},
    # === Decision Records (ADR) → decisions/ płasko ===
    {"op": "delete", "old": "02-artifacts/decision-records/README.md",
     "reason": "Rejestr → .registry.yaml"},
    {"op": "move", "old": "02-artifacts/decision-records/template.md",
     "new": "templates/adr.md", "reason": "Template do templates/"},
    {"op": "move", "old": "02-artifacts/decision-records/ADR-001-micropython-esp32-s3-pico.md",
     "new": "decisions/001-micropython-esp32-s3-pico.md", "reason": "ADR płasko"},
    {"op": "move", "old": "02-artifacts/decision-records/ADR-002-hub-repo-i-osobne-repo-per-projekt.md",
     "new": "decisions/002-hub-repo-i-osobne-repo.md", "reason": "ADR płasko"},
    {"op": "move", "old": "02-artifacts/decision-records/ADR-003-konwencja-commitow-po-polsku.md",
     "new": "decisions/003-konwencja-commitow-po-polsku.md", "reason": "ADR płasko"},
    {"op": "move", "old": "02-artifacts/decision-records/ADR-004-cookiecutter-i-pre-commit.md",
     "new": "decisions/004-cookiecutter-i-pre-commit.md", "reason": "ADR płasko"},
    {"op": "move", "old": "02-artifacts/decision-records/ADR-005-granice-profili-hermes.md",
     "new": "decisions/005-granice-profili-hermes.md", "reason": "ADR płasko"},
    # === Skillsy cross-cutting ===
    {"op": "delete", "old": "02-artifacts/skills/README.md",
     "reason": "Rejestr → .registry.yaml"},
    {"op": "move", "old": "02-artifacts/skills/using-heos/SKILL.md",
     "new": "skills/using-heos.md", "reason": "Skill płasko + domena cross-cutting jako tag"},
    {"op": "move", "old": "02-artifacts/skills/nightly-evolution/SKILL.md",
     "new": "skills/nightly-evolution.md", "reason": "Skill płasko + domena cross-cutting jako tag"},
    # === Puste katalogi (Lessons, Checklists, Playbooks) — puste README do skasowania ===
    {"op": "delete", "old": "02-artifacts/checklists/README.md",
     "reason": "Pusty katalog, brak zawartości"},
    {"op": "delete", "old": "02-artifacts/lessons-learned/README.md",
     "reason": "Pusty katalog, brak zawartości"},
    {"op": "delete", "old": "02-artifacts/playbooks/README.md",
     "reason": "Pusty katalog, brak zawartości"},
    # === Narzędzia 03-quality/ → tools/ ===
    {"op": "move", "old": "03-quality/skill_audit.py",
     "new": "tools/skill_audit.py", "reason": "tools/ zamiast 03-quality/"},
    {"op": "move", "old": "03-quality/heos_lint.py",
     "new": "tools/heos_lint.py", "reason": "tools/ zamiast 03-quality/"},
    {"op": "move", "old": "03-quality/heos_weekly_audit.py",
     "new": "tools/weekly_report.py", "reason": "tools/ + nowa nazwa (bez heos_ prefix)"},
    {"op": "archive", "old": "03-quality/baseline-report-2026-07-23.txt",
     "new": "archive/03-quality-baseline-v1.1.txt", "reason": "Baseline v1.1 → archiwum"},
    {"op": "archive", "old": "03-quality/full-audit-2026-07-23.txt",
     "new": "archive/03-quality-full-audit-v1.1.txt", "reason": "Full audit v1.1 → archiwum"},
    {"op": "archive", "old": "03-quality/weekly-reports/audit-2026-07-23.md",
     "new": "archive/weekly-reports-v1.1/audit-2026-07-23.md", "reason": "Weekly report → archiwum"},
    {"op": "archive", "old": "03-quality/weekly-reports/audit-2026-07-23-updated.txt",
     "new": "archive/weekly-reports-v1.1/audit-2026-07-23-updated.txt", "reason": "Weekly report → archiwum"},
]


def _validate_map(root: Path) -> list[str]:
    """Sprawdza czy każdy `old` istnieje. Zwraca listę błędów."""
    errors = []
    for entry in MIGRATION_MAP:
        old = root / entry["old"]
        if not old.exists() and entry["op"] != "delete":
            # delete może dotyczyć nieistniejącego pliku (już skasowanego) — ale to też raportujemy
            errors.append(f"Brak: {entry['old']}")
    return errors


def _find_backup() -> Path | None:
    """Znajduje najnowszy backup heos-pre-v1.2-*.tar.gz."""
    backup_glob = Path.home() / "hermes-backups"
    if not backup_glob.is_dir():
        return None
    backups = sorted(backup_glob.glob("heos-pre-v1.2-*.tar.gz"), key=lambda p: p.stat().st_mtime)
    return backups[-1] if backups else None


def _check_backup_exists() -> Path | None:
    """Dla --execute: wymaga backupu. Zwraca Path lub None."""
    backup = _find_backup()
    if not backup:
        print("❌ Brak backupu w ~/hermes-backups/heos-pre-v1.2-*.tar.gz", file=sys.stderr)
        print("   Wykonaj najpierw Etap 1.7 (backup + tag)", file=sys.stderr)
        return None
    return backup


def cmd_plan(root: Path) -> int:
    """Wyświetl plan migracji (suchy)."""
    print(f"=== PLAN MIGRACJI HEOS v1.1 → v1.2 ===\n")
    print(f"Katalog HEOS: {root}")
    print(f"Łącznie operacji: {len(MIGRATION_MAP)}\n")
    moves = [e for e in MIGRATION_MAP if e["op"] == "move"]
    archives = [e for e in MIGRATION_MAP if e["op"] == "archive"]
    deletes = [e for e in MIGRATION_MAP if e["op"] == "delete"]
    print(f"- move: {len(moves)}")
    print(f"- archive: {len(archives)}")
    print(f"- delete: {len(deletes)}\n")
    # Walidacja
    errors = _validate_map(root)
    if errors:
        print("⚠️  Błędy walidacji (pliki nie istnieją):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("✅ Walidacja: wszystkie `old` istnieją\n")
    print("=== Szczegóły (pierwsze 10) ===")
    for entry in MIGRATION_MAP[:10]:
        if entry["op"] == "move":
            print(f"  {entry['old']}\n    → {entry['new']}\n    ({entry['reason']})")
        elif entry["op"] == "archive":
            print(f"  {entry['old']}\n    → ARCHIWUM: {entry['new']}\n    ({entry['reason']})")
        else:
            print(f"  {entry['old']}\n    DELETE\n    ({entry['reason']})")
    if len(MIGRATION_MAP) > 10:
        print(f"\n  ... i {len(MIGRATION_MAP) - 10} więcej (patrz migration-map.json po --dry-run)")
    return 0


def cmd_dry_run(root: Path) -> int:
    """Generuj migration-map.json, nic nie ruszaj."""
    print(f"=== DRY-RUN: generuję mapę ===\n")
    errors = _validate_map(root)
    if errors:
        print("❌ Błędy walidacji:")
        for e in errors:
            print(f"  - {e}")
        return 1
    map_path = MIGRATION_DIR / "migration-map.json"
    map_data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "heos_root": str(root),
        "operations": MIGRATION_MAP,
        "summary": {
            "total": len(MIGRATION_MAP),
            "move": sum(1 for e in MIGRATION_MAP if e["op"] == "move"),
            "archive": sum(1 for e in MIGRATION_MAP if e["op"] == "archive"),
            "delete": sum(1 for e in MIGRATION_MAP if e["op"] == "delete"),
        },
    }
    MIGRATION_DIR.mkdir(parents=True, exist_ok=True)
    map_path.write_text(json.dumps(map_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Wygenerowano mapę: {map_path}")
    print(f"   Łącznie operacji: {len(MIGRATION_MAP)}")
    print(f"   - move: {map_data['summary']['move']}")
    print(f"   - archive: {map_data['summary']['archive']}")
    print(f"   - delete: {map_data['summary']['delete']}")
    return 0


def cmd_execute(root: Path) -> int:
    """Wykonaj migrację (git mv + update frontmatter). W Etapie 2, nie 1."""
    print("❌ --execute NIE JEST IMPLEMENTOWANY W ETAPIE 1", file=sys.stderr)
    print("   Etap 1 dostarcza tylko: --plan, --dry-run, --rollback", file=sys.stderr)
    print("   --execute będzie dostępny w Etapie 2 po akceptacji planu", file=sys.stderr)
    return 1


def cmd_rollback(root: Path) -> int:
    """Cofnij migrację z backupu."""
    backup = _find_backup()
    if not backup:
        print("❌ Brak backupu do rollback", file=sys.stderr)
        return 1
    print(f"=== ROLLBACK ===\n")
    print(f"Backup: {backup}")
    print(f"Target: {root}")
    print()
    print("⚠️  Ta operacja NADPISZE obecny katalog HEOS zawartością backupu.")
    print("   Użyj --dry-run jeśli chcesz tylko sprawdzić co by się stało.")
    print()
    print("Aby wykonać rollback:")
    print(f"  tar -xzf {backup} -C /")
    print(f"  cd {root.parent} && git checkout v1.1.0-pre-migration")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Migracja HEOS v1.1 → v1.2")
    parser.add_argument("--root", default=str(HEOS_ROOT_DEFAULT), help="Katalog HEOS")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--plan", action="store_true", help="Pokaż plan (suchy)")
    mode_group.add_argument("--dry-run", action="store_true", help="Generuj mapę, nic nie ruszaj")
    mode_group.add_argument("--execute", action="store_true", help="Wykonaj migrację (Etap 2)")
    mode_group.add_argument("--rollback", action="store_true", help="Cofnij z backupu")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"❌ Katalog nie istnieje: {root}", file=sys.stderr)
        return 2
    if args.plan:
        return cmd_plan(root)
    if args.dry_run:
        return cmd_dry_run(root)
    if args.execute:
        return cmd_execute(root)
    if args.rollback:
        return cmd_rollback(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())

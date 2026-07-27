#!/usr/bin/env python3
"""Sprawdź rekomendowany quality_operational dla skilli HEOS na podstawie
runtime usage z Hermes sidecar (~/.hermes/skills/.usage.json).

Narzędzie READ-ONLY: nie modyfikuje plików HEOS ani Hermes.
Raportuje rekomendacje; autor musi ręcznie zaktualizować frontmatter.

Model dowodu operacyjnego (per ADR-007):
  unmeasured: skill nie ma wpisu w usage.json LUB use_count = 0
  candidate:  use_count >= 1
  proven:     use_count >= 3 ORAZ ostatnie użycie < 180 dni ORAZ okres >= 7 dni
  stale:      ostatnie użycie > 180 dni LUB brak użycia
  failed:     ręczne (NIE automatyczne)

Użycie:
    python3 tools/check_operational_proven.py [--root HEOS_ROOT]
                                            [--profile gaja]
                                            [--usage-json PATH]
                                            [--check]
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# HEOS standard version — ile dni = "proven" wymaga aktywności
PROVEN_MIN_USES = 3
PROVEN_MIN_DAYS = 7
STALE_AFTER_DAYS = 180
# Ile dni od created_at = skill jest "dojrzały" do ewaluacji
EVALUATION_GRACE_DAYS = 0  # brak grace period — od razu można być candidate

HEOS_ROOT = Path(__file__).parent.parent

# ADR-007 dozwolone wartości quality_operational
VALID_OPERATIONAL = {"unmeasured", "candidate", "proven", "stale", "failed"}


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        # Handle timezone-aware ISO format
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _read_usage_json(path: Path) -> dict[str, dict]:
    """Czyta Hermes sidecar `.usage.json`.

    Returns: dict[skill_name, record_dict]. Empty dict jeśli plik nie istnieje.
    """
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return data
    except (json.JSONDecodeError, OSError):
        return {}


def _recommend_operational(record: dict | None) -> str:
    """Oblicz rekomendowany quality_operational dla jednego skilla."""
    if not record:
        return "unmeasured"

    use_count = int(record.get("use_count") or 0)
    state = record.get("state") or "active"
    created_at = _parse_iso(record.get("created_at"))
    last_used_at = _parse_iso(record.get("last_used_at"))

    # Archived skills = unmeasured (nie powinny być rekomendowane jako proven)
    if state == "archived":
        return "unmeasured"

    # Brak użycia = unmeasured
    if use_count == 0 or last_used_at is None:
        return "unmeasured"

    # Stale (>180 dni od ostatniego użycia)
    now = datetime.now(timezone.utc)
    days_since_use = (now - last_used_at).days
    if days_since_use > STALE_AFTER_DAYS:
        return "stale"

    # Single use = candidate
    if use_count < PROVEN_MIN_USES:
        return "candidate"

    # Check grace period — musi istnieć co najmniej od PROVEN_MIN_DAYS
    if created_at and (now - created_at).days < PROVEN_MIN_DAYS:
        return "candidate"

    # Wszystkie warunki spełnione
    return "proven"


def _list_skills(heos_root: Path) -> list[Path]:
    """Lista SKILL.md plików w HEOS (płaskie + katalogowe)."""
    skills_dir = heos_root / "skills"
    paths = []
    if not skills_dir.is_dir():
        return paths
    for p in sorted(skills_dir.glob("*.md")):
        paths.append(p)
    for d in sorted(skills_dir.iterdir()):
        if d.is_dir() and (d / "SKILL.md").exists():
            paths.append(d / "SKILL.md")
    return paths


def _read_skill_name(skill_path: Path) -> str | None:
    """Czyta `name:` z frontmatter skilla."""
    try:
        txt = skill_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.match(r"---\n(.*?)\n---", txt, re.DOTALL)
    if not m:
        return None
    fm = m.group(1)
    name_m = re.search(r"^name:\s*(\S+)", fm, re.M)
    if not name_m:
        return None
    return name_m.group(1)


def _read_quality_operational(skill_path: Path) -> str | None:
    """Czyta `quality_operational:` z frontmatter."""
    try:
        txt = skill_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.match(r"---\n(.*?)\n---", txt, re.DOTALL)
    if not m:
        return None
    fm = m.group(1)
    q_m = re.search(r"^quality_operational:\s*(\S+)", fm, re.M)
    return q_m.group(1) if q_m else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(HEOS_ROOT))
    parser.add_argument("--profile", default="gaja",
                        help="Profil Hermesa (default: gaja)")
    parser.add_argument("--usage-json",
                        default="/home/gaja/.hermes/skills/.usage.json",
                        help="Ścieżka do Hermes .usage.json sidecar")
    parser.add_argument("--check", action="store_true",
                        help="Tylko raportuj (default). NIE modyfikuje.")
    args = parser.parse_args()

    heos_root = Path(args.root).resolve()
    usage_json = Path(args.usage_json).expanduser()

    if not heos_root.is_dir():
        print(f"❌ HEOS root nie istnieje: {heos_root}")
        return 2

    usage_data = _read_usage_json(usage_json)

    skills = _list_skills(heos_root)
    if not skills:
        print(f"⚠️  Brak skills w {heos_root}/skills/")
        return 1

    n_consistent = 0
    n_diff = 0
    print(f"📊 Sprawdzam {len(skills)} skilli HEOS z {usage_json}\n")
    print(f"{'Skill':<35} {'Aktualny':<13} {'Runtime':<14} {'Rekomendacja':<13} {'Status'}")
    print("-" * 100)
    for skill_path in skills:
        name = _read_skill_name(skill_path)
        if not name:
            print(f"⚠️  {skill_path.relative_to(heos_root)}: brak `name:` w frontmatter")
            continue

        current = _read_quality_operational(skill_path) or "(brak)"
        record = usage_data.get(name)
        runtime_status = record.get("state", "active") if record else "—"
        recommended = _recommend_operational(record)

        is_consistent = current == recommended
        marker = "✓" if is_consistent else "⚠️  diff"
        if is_consistent:
            n_consistent += 1
        else:
            n_diff += 1

        print(f"{name:<35} {current:<13} {runtime_status:<14} {recommended:<13} {marker}")

    print()
    print(f"📈 {n_consistent}/{len(skills)} skilli ma quality_operational zgodny z rekomendacją")
    if n_diff:
        print(f"   ⚠️  {n_diff} skille wymagają ręcznej aktualizacji frontmatter")
        print()
        print("Workflow:")
        print("  1. Przejrzyj rekomendacje (Runtime → Rekomendacja)")
        print("  2. Ręcznie ustaw quality_operational w frontmatter skilla")
        print("  3. Dodaj: last_verified: YYYY-MM-DD, verified_on: runtime evidence")
        print("  4. Uruchom: python3 tools/skill_audit.py . --level all")
        return 0  # zawsze 0 — to jest rekomendacja, nie blokada

    return 0


if __name__ == "__main__":
    sys.exit(main())
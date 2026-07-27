#!/usr/bin/env python3
"""Sprawdź mosty HEOS → profil Hermesa (symlinki SKILL.md).

Raportuje:
- ✓ działające symlinki (cel istnieje)
- ✗ BROKEN (cel nie istnieje)
- ⚠️  asymetryczne (most istnieje, ale skill nie istnieje w HEOS)

Użycie:
    python3 tools/validate_symlinks.py [--root HEOS_ROOT] [--profiles-dir PATH]
"""
import argparse
import sys
from pathlib import Path

HEOS_ROOT = Path(__file__).parent.parent
DEFAULT_PROFILES = Path("/home/gaja/.hermes/profiles")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(HEOS_ROOT), help="HEOS root (z skills/)")
    parser.add_argument("--profiles-dir", default=str(DEFAULT_PROFILES), help="Katalog profili Hermesa")
    parser.add_argument("--profiles", nargs="+", default=["gaja"], help="Profile do sprawdzenia")
    args = parser.parse_args()
    heos_root = Path(args.root).resolve()
    profiles_dir = Path(args.profiles_dir).expanduser().resolve()

    skills_dir = heos_root / "skills"
    if not skills_dir.is_dir():
        print(f"❌ Brak katalogu {skills_dir}")
        return 2

    # Inventory HEOS skills
    heos_skills = set()
    for p in skills_dir.glob("*.md"):
        if p.stem != "SKILL":
            heos_skills.add(p.stem)
    for d in skills_dir.iterdir():
        if d.is_dir() and (d / "SKILL.md").exists():
            heos_skills.add(d.name)

    broken = 0
    ok = 0
    not_in_heos = 0
    for profile in args.profiles:
        profile_dir = profiles_dir / profile / "skills"
        if not profile_dir.is_dir():
            print(f"⚠️  Profil {profile}: brak katalogu {profile_dir}")
            continue
        for link in sorted(profile_dir.glob("*/*/SKILL.md")):
            if not link.is_symlink():
                continue
            target = link.resolve()
            skill_name = link.parent.name
            if not target.exists():
                print(f"✗ BROKEN: {profile}: {link.relative_to(profile_dir.parent.parent)} -> {target}")
                broken += 1
            elif skill_name not in heos_skills:
                # Cel istnieje ale skill nie ma w HEOS (np. runtime-only skill)
                print(f"⚠️  {profile}: {skill_name} → {target.relative_to(heos_root.parent.parent)} (nie ma w HEOS)")
                not_in_heos += 1
            else:
                print(f"✓ {profile}: {skill_name} → {target.relative_to(heos_root.parent.parent)}")
                ok += 1

    print(f"\nPodsumowanie: ✓ {ok} działających, ✗ {broken} złamanych, ⚠️ {not_in_heos} runtime-only")
    return 0 if broken == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
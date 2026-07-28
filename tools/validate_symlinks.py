#!/usr/bin/env python3
"""Sprawdź mosty HEOS → profil Hermesa (symlinki LUB hardlinki SKILL.md).

Raportuje:
- ✓ działające mosty (cel istnieje — symlink lub hardlink)
- ✗ BROKEN (cel nie istnieje — dangling symlink)
- ⚠️  asymetryczne (most istnieje, ale skill nie istnieje w HEOS)
- ⚠️  REAL FILE (kopia, nie most — może być drift)

Użycie:
    python3 tools/validate_symlinks.py [--root HEOS_ROOT] [--profiles-dir PATH]
    python3 tools/validate_symlinks.py --profiles gaja gaja-it

Default: sprawdza WSZYSTKIE profile w profiles_dir (nie tylko gaja).

Mosty HEOS → profil to hardlink lub symlink SKILL.md. Hardlink jest
preferowany (atomic update, brak dangling risk), ale validate_symlinks.py
historycznie sprawdzał tylko symlinki.
"""
import argparse
import sys
from pathlib import Path

HEOS_ROOT = Path(__file__).parent.parent
DEFAULT_PROFILES = Path("/home/gaja/.hermes/profiles")


def discover_profiles(profiles_dir: Path) -> list[str]:
    """Znajdź wszystkie profile Hermes (katalogi z skills/)."""
    profiles = []
    for entry in sorted(profiles_dir.iterdir()):
        if not entry.is_dir():
            continue
        if (entry / "skills").is_dir():
            profiles.append(entry.name)
    return profiles


def heos_source_inodes(skills_dir: Path) -> dict[str, int]:
    """Zwraca mapę: skill_name → inode SKILL.md w HEOS source."""
    inodes = {}
    for p in skills_dir.glob("*.md"):
        if p.stem != "SKILL":
            inodes[p.stem] = p.stat().st_ino
    for d in skills_dir.iterdir():
        if d.is_dir():
            skill_md = d / "SKILL.md"
            if skill_md.exists() and not skill_md.is_symlink():
                inodes[d.name] = skill_md.stat().st_ino
    return inodes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(HEOS_ROOT), help="HEOS root (z skills/)")
    parser.add_argument("--profiles-dir", default=str(DEFAULT_PROFILES), help="Katalog profili Hermesa")
    parser.add_argument("--profiles", nargs="+", default=None,
                        help="Profile do sprawdzenia (default: auto-discover wszystkie)")
    args = parser.parse_args()
    heos_root = Path(args.root).resolve()
    profiles_dir = Path(args.profiles_dir).expanduser().resolve()

    skills_dir = heos_root / "skills"
    if not skills_dir.is_dir():
        print(f"❌ Brak katalogu {skills_dir}")
        return 2

    # Inventory HEOS skills (po inodes — hardlink NIE jest symlinkiem)
    heos_inodes = heos_source_inodes(skills_dir)
    heos_skills = set(heos_inodes.keys())

    # Profile (auto-discover lub explicit)
    if args.profiles is None:
        profiles = discover_profiles(profiles_dir)
    else:
        profiles = args.profiles

    broken = 0
    ok_symlink = 0
    ok_hardlink = 0
    not_in_heos = 0
    real_file = 0
    no_skills_dir = 0
    for profile in profiles:
        profile_dir = profiles_dir / profile / "skills"
        if not profile_dir.is_dir():
            print(f"⚠️  Profil {profile}: brak katalogu {profile_dir}")
            no_skills_dir += 1
            continue
        # Sprawdzamy WSZYSTKIE SKILL.md w subkatalogach (glob */*/SKILL.md)
        for link in sorted(profile_dir.glob("*/*/SKILL.md")):
            skill_name = link.parent.name
            if link.is_symlink():
                target = link.resolve()
                if not target.exists():
                    print(f"✗ BROKEN: {profile}: {link.relative_to(profile_dir.parent.parent)} -> {target}")
                    broken += 1
                elif skill_name not in heos_skills:
                    print(f"⚠️  {profile}: {skill_name} → {target.relative_to(heos_root.parent.parent)} (nie ma w HEOS)")
                    not_in_heos += 1
                else:
                    print(f"✓ {profile}: {skill_name} → {target.relative_to(heos_root.parent.parent)} (symlink)")
                    ok_symlink += 1
            else:
                # Real file — może być hardlink do HEOS source (OK) lub kopia (drift)
                inode = link.stat().st_ino
                if skill_name in heos_inodes and heos_inodes[skill_name] == inode:
                    print(f"✓ {profile}: {skill_name} = hardlink do HEOS source")
                    ok_hardlink += 1
                else:
                    print(f"⚠️  REAL FILE: {profile}: {skill_name} = {link.relative_to(profile_dir.parent.parent)} (kopia, sprawdź czy aktualna)")
                    real_file += 1

    print(f"\nPodsumowanie: ✓ {ok_symlink + ok_hardlink} mostów ({ok_symlink} symlink, {ok_hardlink} hardlink), "
          f"✗ {broken} złamanych, ⚠️  {not_in_heos} runtime-only, "
          f"⚠️  {real_file} real-file (drift risk), ⚠️  {no_skills_dir} brak skills/")
    return 0 if broken == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
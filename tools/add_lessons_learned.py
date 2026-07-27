#!/usr/bin/env python3
"""
add_lessons_learned.py — dodaje sekcję "Lessons Learned" do ADR v1.2.

Logika:
- Czyta ADR
- Sprawdza czy ma już sekcję "Lessons Learned"
- Jeśli nie: dodaje krótką (3-5 linii) na podstawie analizy treści
- Jeśli tak: pomija (nie nadpisuje)

Użycie:
    python3 add_lessons_learned.py [--dry-run] [--adr ADR-001-...]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEOS = Path("/home/gaja/gaja-projekty/HEOS")
DECISIONS = HEOS / "decisions"


# Wzorce dla generowania Lessons Learned na podstawie tytułu
# (ręcznie napisane wnioski z naszej historii)
LESSONS_TEMPLATES = {
    "001-micropython-esp32-s3-pico": """## Lessons Learned

- **Pinout per board** — każda płytka ESP32 (Feather/Pico/DevKitC) ma inny pin RGB LED. Zawsze sprawdzaj docs producenta PRZED pisaniem kodu, nie po.
- **Bootloader vs App port** — po wgraniu MicroPython dwa porty `/dev/ttyACM*` się zamieniają. Nie hardkoduj `/dev/ttyACM0` — sprawdzaj po każdym restarcie.
- **`sys.platform` nie rozróżnia wariantów** — MicroPython zwraca `"esp32"` dla wszystkich S3/C3/Pico. Nie pytaj Pythona o model, pytaj pinout.
- **Arduino core ma warianty boardów** — zły wariant = złe piny BEZ błędu kompilacji. MicroPython eliminuje tę pułapkę.""",

    "002-hub-repo-i-osobne-repo": """## Lessons Learned

- **Hub + sub-repo to sweet spot** — nie monorepo (za ciężki), nie każdy projekt osobno bez śledzenia (chaos). Hub z tabelką + linkami + statusami daje widoczność bez coupling'u.
- **Konwencja commitów musi być w WORKFLOW.md** — w innym miejscu nikt nie sprawdzi.
- **Cookiecutter > ręczne kopiowanie** — template z pre-commit + .editorconfig + LICENSE eliminuje "zapomniałem dodać .gitignore" syndrome.
- **gitleaks w pre-commit blokuje wyciek PAT** — Joker miał nawyk wysyłania tokenów na Discorda. Bramka techniczna > apel do dyscypliny.""",

    "003-konwencja-commitow-po-polsku": """## Lessons Learned

- **Polski w commitach działa** dla solo developera. Gdyby doszli inni kontrybutorzy, rozważ angielski.
- **Kanon 7 tagów wystarczy** — nie wymyślaj nowych tagów na siłę. `[chore]` dla wszystkiego co nie pasuje.
- **Format `[tag] opis` parsowalny przez `git log --grep="^\\[fix\\]"`** — przydatne do audytu zmian.
- **Format v1.0 działa, ale to nie Conventional Commits** — brak semver + breaking changes. Wystarczające dla solowych projektów, niewystarczające dla release managementu.""",

    "004-cookiecutter-i-pre-commit": """## Lessons Learned

- **Cookiecutter z lokalnego katalogu** działa lepiej niż z GitHub URL (brak network dependency przy tworzeniu projektu).
- **`.pre-commit-config.yaml` w template** (nie w tutorialu) — nowy projekt ma gotową bramkę od razu.
- **ruff + ruff-format > black + flake8** — szybsze, jeden tool, mniej konfiguracji.
- **gitleaks musi być w pre-commit**, nie w CI — bo CI blokuje po push (za późno, secret jest w historii).
- **`.editorconfig` eliminuje "spaces vs tabs" w dyskusjach** — trywialna, ale irytująca bez niej.""",

    "005-granice-profili-hermes": """## Lessons Learned

- **Profile Hermesa to naturalne granice kontekstu** — nie próbuj ich scalać. Każdy profil ma swoją pamięć, skills, sesje.
- **NIE współdziel sekretów między profilami** — każdy profil powinien mieć własne klucze API. Tavyly/Firecrawl osobno dla gaja, gaja-it, gaja-med.
- **Cross-profile reads są możliwe** (read_file z explicit path), ale **domyślnie zablokowane** (cross_profile guard). To jest dobre zabezpieczenie.
- **Asymetria related** w v1.2: Skills cytują ADR-005 ale ADR-005 nie cytował Skills z powrotem. Naprawione w v1.2.1 (auto-fix).""",
}


def _extract_adr_number(frontmatter: dict) -> str | None:
    """Zwraca ADR number jako string (np. '001')."""
    adr_num = frontmatter.get("adr_number")
    if adr_num is not None:
        return f"{int(adr_num):03d}"
    return None


def _get_lesson_for(adr_name: str) -> str | None:
    """Zwraca template Lessons Learned dla danego ADR (po name)."""
    for key, lesson in LESSONS_TEMPLATES.items():
        if key in adr_name:
            return lesson
    return None


def process_adr(adr_path: Path, dry_run: bool) -> tuple[bool, str]:
    """Dodaje sekcję Lessons Learned do jednego ADR. Zwraca (success, message)."""
    text = adr_path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return False, f"  ⚠️  {adr_path.name}: brak frontmatter"

    parts = text.split("---", 2)
    if len(parts) < 3:
        return False, f"  ⚠️  {adr_path.name}: malformed frontmatter"

    import yaml
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        return False, f"  ❌ {adr_path.name}: YAML error: {e}"

    body = parts[2]

    # Sprawdź czy już ma "## Lessons Learned"
    if re.search(r"^## Lessons Learned\s*$", body, re.MULTILINE):
        return True, f"  ⏭️  {adr_path.name}: już ma Lessons Learned"

    # Pobierz ADR name z frontmatter lub filename
    adr_name = fm.get("name", adr_path.stem)

    # Pobierz lesson template
    lesson = _get_lesson_for(adr_name)
    if lesson is None:
        return False, f"  ⚠️  {adr_path.name}: brak template dla tego ADR (name={adr_name!r})"

    # Dodaj przed "## Powiązane" (jeśli istnieje) lub na końcu
    if "## Powiązane" in body:
        # Wstaw PRZED "## Powiązane"
        body = body.replace("## Powiązane", f"{lesson}\n## Powiązane", 1)
    else:
        # Dodaj na końcu
        body = body.rstrip() + "\n\n" + lesson

    # Zaktualizuj updated_at
    fm["updated_at"] = "2026-07-24"

    new_fm = yaml.safe_dump(fm, default_flow_style=False, sort_keys=False, allow_unicode=True, width=120)
    new_text = "---\n" + new_fm + "---" + body

    if dry_run:
        return True, f"  [DRY] {adr_path.name}: dodałby Lessons Learned"

    adr_path.write_text(new_text, encoding="utf-8")
    return True, f"  ✅ {adr_path.name}: dodano Lessons Learned"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--adr", help="Tylko jeden ADR (np. ADR-001-micropython-...)")
    args = parser.parse_args()

    # Pliki ADR w v1.2 mają nazwę NNN-tytuł.md (nie ADR-NNN-...)
    # ale dla bezpieczeństwa sprawdzamy oba wzorce
    adrs = sorted(DECISIONS.glob("*.md"))
    # Filtruj: tylko pliki które wyglądają jak ADR (zawierają ADR-NNN lub są NNN-)
    adrs = [a for a in adrs if re.match(r"^\d{3}-", a.name) or a.name.startswith("ADR-")]
    if args.adr:
        adrs = [a for a in adrs if a.name.startswith(args.adr)]
        if not adrs:
            print(f"❌ Nie znaleziono ADR: {args.adr}")
            return 1

    print(f"=== Dodawanie Lessons Learned do {len(adrs)} ADR ===\n")
    ok_count = 0
    skip_count = 0
    fail_count = 0

    for adr in adrs:
        ok, msg = process_adr(adr, args.dry_run)
        print(msg)
        if ok:
            if "⏭️" in msg or "[DRY]" in msg:
                skip_count += 1
            else:
                ok_count += 1
        else:
            fail_count += 1

    print()
    print(f"Wynik: {ok_count} dodanych, {skip_count} pominiętych, {fail_count} błędów")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

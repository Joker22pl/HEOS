#!/usr/bin/env python3
"""
skill_audit.py v1.2 — walidator Skillów z 3-poziomową oceną.

Trzy poziomy:
1. **Schema Compliance** — czy ma wszystkie wymagane pola, nagłówki, typy
2. **Technical Validity** — czy treść jest sensowna (nie puste sekcje, kod się parsuje)
3. **Operational Usefulness** — czy używany (logi, cytowania)

Użycie:
    python3 skill_audit.py [ścieżka] [--level=schema|technical|operational|all] [--strict]

Backward compat: bez --level działa jak v1.1 (schema only).
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


# === Schema (v1.1 - kompatybilne) ===
OBOWIĄZKOWE: tuple[str, ...] = (
    "Cel", "Zakres", "Kiedy używać", "Kiedy nie używać",
    "Workflow", "Przykłady", "Lessons Learned",
)
# Runtime Skills (plugin/cron/MCP) — mniej wymagań, bo to nie wiedza dla użytkownika
OBOWIĄZKOWE_RUNTIME: tuple[str, ...] = (
    "Cel",          # musi być jasne co Skill robi
    "Lessons Learned",  # Lessons z runtime (pułapki, edge cases)
)
OPCJONALNE: tuple[str, ...] = (
    "Typowe błędy", "Debugging", "Biblioteki", "Narzędzia",
    "Oficjalne źródła", "Wersjonowanie", "Checklisty", "Najlepsze praktyki",
)
ALIASY: dict[str, tuple[str, ...]] = {
    "Cel": ("Purpose", "Goal", "Objective", "About", "Overview", "Description"),
    "Zakres": ("Scope", "When applicable", "Applicability", "Prerequisites", "Requirements", "What is this", "About"),
    "Kiedy używać": ("When to use", "Kiedy używac", "When use", "Use this when", "Use when"),
    "Kiedy nie używać": ("When not to use", "Kiedy używac", "When not use", "Don't use", "When to avoid", "Limitations", "Not for"),
    "Workflow": ("Workflow", "How to use", "How it works", "Process", "Step-by-step", "Steps", "Procedure", "Implementation", "Quick Reference", "Usage", "Basic Usage", "How"),
    "Przykłady": ("Examples", "Example", "Usage examples", "Usage", "Sample code", "Code examples", "Example usage", "Przykłady użycia"),
    "Lessons Learned": ("Lessons learned", "Lessons learned.", "Lesson learned", "Lessons", "Pitfalls", "Pitfalls / Lessons Learned", "Pitfalle", "Pitfalle / Lessons Learned", "Gotchas", "Tips", "Notes", "Caveats", "Known issues", "Common issues"),
    "Typowe błędy": ("Common errors", "Common mistakes", "Common pitfalls", "Typical errors", "Mistakes to avoid"),
    "Debugging": ("Debugging", "Debug", "Troubleshooting", "Common issues", "Troubleshooting guide"),
    "Biblioteki": ("Libraries", "Dependencies", "Required packages"),
    "Narzędzia": ("Tools", "Utilities"),
    "Oficjalne źródła": ("Official sources", "Oficjalne zrodla", "Sources", "References", "Documentation", "Docs"),
    "Wersjonowanie": ("Versioning", "Version", "Changelog"),
    "Checklisty": ("Checklist", "Checklists", "Pre-flight", "Pre-flight checklist"),
    "Najlepsze praktyki": ("Best practices", "Best Practices", "Best practice", "Tips", "Recommendations"),
}

# === Schema v1.2 (nowe pola w frontmatter) ===
SCHEMA_V12_FIELDS: tuple[str, ...] = (
    "type", "id", "name", "title", "status", "owner",
    "created_at", "updated_at", "review_due", "version",
    "heos_standard_version", "tags",
)

# Minimalne limity treści (Technical)
MIN_WORDS_PER_SECTION = 5   # sekcja z <5 słów to prawdopodobnie pusta
MIN_CODE_BLOCKS = 1         # Skill powinien mieć przynajmniej 1 przykład kodu


@dataclass
class SkillReport:
    path: Path
    obecne_obowiązkowe: list[str] = field(default_factory=list)
    brakujące_obowiązkowe: list[str] = field(default_factory=list)
    obecne_opcjonalne: list[str] = field(default_factory=list)
    brakujące_opcjonalne: list[str] = field(default_factory=list)
    # Nowe pola v1.2
    schema_v12_missing: list[str] = field(default_factory=list)
    schema_v12_present: list[str] = field(default_factory=list)
    # Technical
    empty_sections: list[str] = field(default_factory=list)
    short_sections: list[str] = field(default_factory=list)
    no_code_examples: bool = True
    has_frontmatter: bool = False
    # Operational (placeholder — nie zbieramy w Etapie 2, tylko marker)
    operational: str = "unmeasured"
    # Czy to runtime Skill (mniej wymagań) — wykrywane w audytuj_skill()
    is_runtime: bool = False
    # Marker: plik nie jest skilliem (type: lessons/checklist/playbook/adr)
    is_not_skill: bool = False
    # Wymagane sekcje (zależne od typu)
    required_sections: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        """Status v1.1-compat: PASS/WARN/FAIL na podstawie schema."""
        if self.brakujące_obowiązkowe:
            return "FAIL"
        if len(self.brakujące_opcjonalne) > 2:
            return "WARN"
        return "PASS"

    @property
    def schema_status(self) -> str:
        if self.brakujące_obowiązkowe:
            return "FAIL"
        return "PASS"

    @property
    def technical_status(self) -> str:
        """Technical: FAIL jeśli puste sekcje lub brak kodu."""
        if self.empty_sections or self.no_code_examples:
            return "FAIL"
        if self.short_sections:
            return "WARN"
        return "PASS"

    @property
    def operational_status(self) -> str:
        """Operational: aktualnie placeholder (unmeasured)."""
        if self.operational == "unmeasured":
            return "N/A"
        if self.operational == "fresh":
            return "WARN"
        if self.operational == "proven":
            return "PASS"
        return "N/A"

    @property
    def combined_status(self) -> str:
        """Połączony: approved = all 3 PASS."""
        s = self.schema_status
        t = self.technical_status
        o = self.operational_status
        if s == "FAIL" or t == "FAIL":
            return "invalid" if s == "FAIL" else "broken"
        if o == "N/A" or o == "WARN":
            return "partial"
        if s == "PASS" and t == "PASS" and o == "PASS":
            return "approved"
        return "partial"


def _czy_pasuje(naglowek: str, pole: str) -> bool:
    norm = naglowek.strip().rstrip(".").lower()
    if norm == pole.lower().rstrip("."):
        return True
    for alias in ALIASY.get(pole, ()):
        alias_norm = alias.lower().rstrip(".")
        if norm == alias_norm:
            return True
        if norm.startswith(alias_norm + " ") or norm.startswith(alias_norm + ":"):
            return True
    return False


def _wyciagnij_naglowki(tekst: str) -> list[str]:
    pattern = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
    return [m.group(1).strip() for m in pattern.finditer(tekst)]


def _parsuj_frontmatter(tekst: str) -> tuple[dict | None, str]:
    """Zwraca (frontmatter_dict, reszta_tekstu)."""
    if not tekst.startswith("---"):
        return None, tekst
    parts = tekst.split("---", 2)
    if len(parts) < 3:
        return None, tekst
    try:
        import yaml
        return yaml.safe_load(parts[1]) or {}, parts[2]
    except Exception:
        return None, tekst


def _wyciagnij_sekcje(tekst: str) -> dict[str, str]:
    """Wyciągnij treść każdej sekcji (nagłówek → treść).

    Reguły:
    - # (level 1) to TYTUŁ dokumentu, NIE jest sekcją
    - Sekcje zaczynają się od ## (level 2)
    - Nagłówek level N zamyka poprzedni nagłówek level M jeśli N <= M
    - Nagłówek level N jest pod-sekcją poprzedniego jeśli N > M
    - Nagłówki level 1 wewnątrz dokumentu są traktowane jak level 2 (anomalia)
    """
    ordered: list[tuple[str, list[str]]] = []
    current_h = None
    current_level = 2  # startujemy z level 2, żeby ## na początku zamykały "wirtualny" początek
    current_content: list[str] = []
    for line in tekst.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            level = len(m.group(1))
            heading = m.group(2).strip().rstrip(".").lower()
            # Traktuj # tak jak ## (zabezpieczenie: anomalia w środku dokumentu)
            if level == 1:
                level = 2
            if current_h is not None:
                if level <= current_level:
                    ordered.append((current_h, current_content))
                    current_h = heading
                    current_level = level
                    current_content = []
                else:
                    current_content.append(line)
            else:
                current_h = heading
                current_level = level
                current_content = []
        else:
            if current_h is not None:
                current_content.append(line)
    if current_h is not None:
        ordered.append((current_h, current_content))
    sections: dict[str, str] = {}
    for h, content in ordered:
        content_str = "\n".join(content).strip()
        if h in sections:
            sections[h] = (sections[h] + "\n\n" + content_str) if sections[h] else content_str
        else:
            sections[h] = content_str
    return sections


def _sekcje_pusta_or_short(sekcje: dict[str, str], obowiazkowe: Iterable[str]) -> tuple[list[str], list[str]]:
    """Zwraca (puste, krótkie) sekcje obowiązkowe."""
    empty = []
    short = []
    for sec_name in obowiazkowe:
        # Szukamy sekcji (case-insensitive, z aliasami)
        content = None
        for alias in [sec_name] + list(ALIASY.get(sec_name, ())):
            key = alias.lower().rstrip(".")
            for actual_key, actual_content in sekcje.items():
                if actual_key == key or actual_key.startswith(key + " "):
                    content = actual_content
                    break
            if content is not None:
                break
        if content is None or not content.strip():
            empty.append(sec_name)
        elif len(content.split()) < MIN_WORDS_PER_SECTION:
            short.append(sec_name)
    return empty, short


def _ma_code_blocks(tekst: str) -> bool:
    """Sprawdza czy tekst ma bloki kodu (``` lub indented)."""
    return bool(re.search(r"^```", tekst, re.MULTILINE))


def audytuj_skill(sciezka: Path) -> SkillReport:
    """Przeanalizuj jeden plik SKILL.md."""
    raport = SkillReport(path=sciezka)
    if not sciezka.exists():
        raport.brakujące_obowiązkowe = list(OBOWIĄZKOWE)
        return raport
    try:
        tekst = sciezka.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        tekst = sciezka.read_text(encoding="latin-1")
    # Frontmatter
    fm, body = _parsuj_frontmatter(tekst)
    # Pomiń pliki które nie są skillami (np. lessons/checklists/playbooks/adr)
    # Zwracamy "skip" marker, który audytuj_katalog odfiltrowuje
    if fm and fm.get("type") and fm.get("type") != "skill":
        raport.has_frontmatter = True
        raport.is_not_skill = True
        return raport
    if fm:
        raport.has_frontmatter = True
        for f in SCHEMA_V12_FIELDS:
            if f in fm and fm[f] is not None:
                raport.schema_v12_present.append(f)
            else:
                raport.schema_v12_missing.append(f)
    # Czy to runtime Skill?
    runtime_marker = (fm or {}).get("skill_kind") == "runtime" or _jest_plik_runtime(sciezka)
    raport.is_runtime = runtime_marker
    # Wybierz odpowiednią listę obowiązkowych sekcji
    required = OBOWIĄZKOWE_RUNTIME if runtime_marker else OBOWIĄZKOWE
    raport.required_sections = list(required)
    # Schema (sekcje)
    naglowki = _wyciagnij_naglowki(tekst)
    for pole in required:
        if any(_czy_pasuje(h, pole) for h in naglowki):
            raport.obecne_obowiązkowe.append(pole)
        else:
            raport.brakujące_obowiązkowe.append(pole)
    for pole in OPCJONALNE:
        if any(_czy_pasuje(h, pole) for h in naglowki):
            raport.obecne_opcjonalne.append(pole)
        else:
            raport.brakujące_opcjonalne.append(pole)
    # Technical (treść)
    sekcje = _wyciagnij_sekcje(tekst)
    empty, short = _sekcje_pusta_or_short(sekcje, required)
    raport.empty_sections = empty
    raport.short_sections = short
    raport.no_code_examples = not _ma_code_blocks(tekst)
    return raport


def _jest_plik_runtime(sciezka: Path) -> bool:
    """Czy plik to runtime Hermes (plugin/cron) a nie HEOS Skill?

    Heurystyka — jeśli WSZYSTKIE poniższe są spełnione, to runtime:
    - Brak frontmatter v1.2 (heos_standard_version) LUB ma "data_root" / "data_root:"
    - W treści ma wzmiankę o plugin/cron (np. "plugins/", "data_root", "Loop freq")
    - W treści ma wzmiankę o "~/.hermes" (katalog runtime Hermes)

    Prostsze: jeśli nazwa pliku zaczyna się od "using-" i ma "plugin"
    w description lub treści, to prawdopodobnie runtime.
    """
    try:
        tekst = sciezka.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    # Hard excludes
    if "data_root:" in tekst and "~/.hermes" in tekst:
        return True
    # Heurystyka: Skills opisujące "plugin" lub "cron" lub "mcp server"
    # są runtime, nie wiedzą wiedzy
    fm = _parsuj_frontmatter(tekst)[0] if _parsuj_frontmatter(tekst)[0] else {}
    description = fm.get("description", "") or ""
    text_lower = tekst.lower()
    runtime_signals = 0
    for keyword in ["plugin", "cron", "mcp server", "loop freq", "loop_frequency"]:
        if keyword in description.lower() or keyword in text_lower[:1000]:
            runtime_signals += 1
    # Musi mieć ≥1 sygnał + wzmiankę o katalogu Hermes
    if runtime_signals >= 1 and "~/.hermes" in tekst:
        return True
    return False


def audytuj_katalog(root: Path) -> list[SkillReport]:
    """Audytuj wszystkie artefakty typu 'skill'.

    Obsługiwane lokalizacje:
    - HEOS v1.2: skills/*.md
    - HEOS v1.1: 01-domains/*/skills/*/SKILL.md
    - Profil Hermesa: <kategoria>/<skill>/SKILL.md  (np. apple/apple-notes/SKILL.md)
    - Profil Hermesa: <kategoria>/<skill>.md  (flat, nowy styl)
    - Profil Hermesa: <kategoria>/DESCRIPTION.md  (opis kategorii, nie Skill)

    Filtr: pomija pliki runtime Hermes (plugins, cron jobs).
    """
    raporty = []
    seen: set[Path] = set()
    # v1.2 HEOS: skills/*.md
    skills_dir = root / "skills"
    if skills_dir.is_dir():
        for p in sorted(skills_dir.glob("*.md")):
            raporty.append(audytuj_skill(p))
            seen.add(p)
        # v1.2+ HEOS: skills/<name>/SKILL.md (skills with references/scripts)
        for p in sorted(skills_dir.glob("*/SKILL.md")):
            raporty.append(audytuj_skill(p))
            seen.add(p)
    # v1.1 HEOS: 01-domains/*/skills/*/SKILL.md
    for p in sorted(root.rglob("SKILL.md")):
        if "01-domains" in p.parts and p not in seen:
            raporty.append(audytuj_skill(p))
            seen.add(p)
    # Profil Hermesa: */<skill>/SKILL.md (styl katalogowy)
    # UWAGA: nie filtruj po 'skills' w p.parts (bo root sam się nazywa skills)
    # Filtrujemy tylko: tools/, templates/, heos-migration/, archive/, decisions/, 01-domains/
    # UWAGA: 'HEOS' NIE jest w filtrze bo w submoduł layout (gaja-projekty/HEOS/)
    # KAŻDA ścieżka pod root zawiera 'HEOS' w parts → filtr odrzuca wszystko.
    # HEOS root jest zawsze katalogiem najwyższego poziomu więc 'skills/' jest legit
    # ścieżką dla HEOS Skills.
    HEOS_KATALOGI = ("tools", "templates", "heos-migration", "archive", "decisions",
                  "01-domains", "joker-deliverables", "lessons", "checklists", "playbooks")
    for p in sorted(root.rglob("SKILL.md")):
        # Pomiń jeśli już dodany i jeśli to HEOS katalog (już obsłużone)
        if p in seen:
            continue
        # Pomiń pliki w HEOS subkatalogach (v1.1 obsłużone wyżej, ale sprawdzamy)
        if any(s in p.parts for s in HEOS_KATALOGI):
            continue
        if _jest_plik_runtime(p):
            continue
        raporty.append(audytuj_skill(p))
        seen.add(p)
    # Profil Hermesa: flat *.md (bezpośrednio w katalogu kategorii)
    for cat_dir in root.iterdir():
        if not cat_dir.is_dir():
            continue
        # Pomiń katalogi HEOS tools/templates/etc.
        if cat_dir.name in HEOS_KATALOGI:
            continue
        # Pomiń opisy kategorii (np. DESCRIPTION.md, README.md)
        for p in sorted(cat_dir.glob("*.md")):
            if p in seen:
                continue
            if p.name.upper() in ("DESCRIPTION.MD", "README.MD", "INDEX.MD"):
                continue
            if _jest_plik_runtime(p):
                continue
            r = audytuj_skill(p)
            # Filtruj non-skille (lessons/checklists/playbooks w root)
            if r.is_not_skill:
                continue
            raporty.append(r)
            seen.add(p)
    return raporty


# === Main + formatowanie ===

def _emoji_for_status(status: str) -> str:
    return {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌", "N/A": "ℹ️ "}.get(status, "?")


def _format_report(r: SkillReport, levels: set[str]) -> str:
    lines = [f"\n--- {r.path.name} ---"]
    if "schema" in levels:
        emoji = _emoji_for_status(r.schema_status)
        missing_ob = ", ".join(r.brakujące_obowiązkowe) or "—"
        n_opc = len(r.obecne_opcjonalne)
        lines.append(f"  {emoji} Schema: {len(r.obecne_obowiązkowe)}/7 obowiązkowych, {n_opc}/8 opcjonalnych")
        if r.brakujące_obowiązkowe:
            lines.append(f"     Brak: {missing_ob}")
    if "technical" in levels:
        emoji = _emoji_for_status(r.technical_status)
        empty = ", ".join(r.empty_sections) if r.empty_sections else "—"
        short = ", ".join(r.short_sections) if r.short_sections else "—"
        lines.append(f"  {emoji} Technical: empty={empty}, short={short}, code_examples={not r.no_code_examples}")
    if "operational" in levels:
        lines.append(f"  ℹ️  Operational: {r.operational_status} (unmeasured w Etapie 2)")
    lines.append(f"  → Combined: {r.combined_status}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Skill audit v1.2 (3 poziomy)")
    # NOTE: hardcoded absolute path (nie "~") bo pod Hermes profile HOME=/home/gaja/.hermes/profiles/<name>/home
    #       a expanduser("~") zwraca wtedy "/home/gaja/.hermes/profiles/<name>/home/.hermes/..." — podwójny root.
    #       Realna ścieżka Hermes profile 'gaja' z skills/ jest zawsze stała.
    parser.add_argument("sciezka", nargs="?",
                        default="/home/gaja/.hermes/profiles/gaja/skills",
                        help="Katalog ze Skillami")
    parser.add_argument("--level", default="schema",
                        choices=["schema", "technical", "operational", "all"],
                        help="Poziom audytu (domyślnie: schema)")
    parser.add_argument("--strict", action="store_true", help="Traktuj WARN jako FAIL")
    parser.add_argument("--quiet", action="store_true", help="Tylko podsumowanie")
    parser.add_argument("--with-runtime", action="store_true",
                        help="Dodatkowo sprawdź runtime evidence (Hermes sidecar ~/.hermes/skills/.usage.json). "
                             "Raportuje rozbieżności quality_operational vs runtime rekomendacja.")
    args = parser.parse_args()
    root = Path(args.sciezka).expanduser().resolve()
    if not root.is_dir():
        print(f"❌ Katalog nie istnieje: {root}", file=sys.stderr)
        return 2
    raporty = audytuj_katalog(root)
    if not raporty:
        print(f"⚠️  Brak SKILL.md pod {root}", file=sys.stderr)
        return 0
    levels = {"schema", "technical", "operational"} if args.level == "all" else {args.level}
    if not args.quiet:
        for r in raporty:
            print(_format_report(r, levels))
    # Statystyki
    n_pass = sum(1 for r in raporty if r.schema_status == "PASS")
    n_warn = sum(1 for r in raporty if r.schema_status == "WARN")
    n_fail = sum(1 for r in raporty if r.schema_status == "FAIL")
    n_approved = sum(1 for r in raporty if r.combined_status == "approved")
    n_partial = sum(1 for r in raporty if r.combined_status == "partial")
    n_broken = sum(1 for r in raporty if r.combined_status == "broken")
    n_invalid = sum(1 for r in raporty if r.combined_status == "invalid")
    print()
    print(f"--- Podsumowanie (poziom: {args.level}) ---")
    print(f"Zbadane Skills: {len(raporty)}")
    print(f"Schema: ✅ {n_pass} PASS | ⚠️  {n_warn} WARN | ❌ {n_fail} FAIL")
    n_tech_pass = sum(1 for r in raporty if r.technical_status == "PASS")
    n_tech_fail = sum(1 for r in raporty if r.technical_status == "FAIL")
    if "technical" in levels or args.level == "all":
        print(f"Technical: ✅ {n_tech_pass} PASS | ❌ {n_tech_fail} FAIL")
    if "all" in levels or args.level == "all":
        print(f"Combined: approved={n_approved} | partial={n_partial} | broken={n_broken} | invalid={n_invalid}")
    # Runtime evidence check (per ADR-007)
    if args.with_runtime:
        try:
            from check_operational_proven import _read_usage_json, _recommend_operational
            import re
            # ~/.hermes/skills/.usage.json jest HARD-CODED w Hermes
            # (skill_usage.py używa hermes_constants.get_hermes_home()).
            # Dla HEOS hardcodujemy ścieżkę ~/.hermes/skills/.usage.json
            # — NIE expanduser (który w profilu Hermesa daje dziwną ścieżkę).
            usage_path = Path("/home/gaja/.hermes/skills/.usage.json")
            usage_data = _read_usage_json(usage_path)
            n_runtime_diff = 0
            print()
            print("--- Runtime evidence (ADR-007) ---")
            print(f"Source: {usage_path}")
            for r in raporty:
                if r.is_not_skill:
                    continue
                # Parsuj name: z frontmatter (re-use read_text)
                try:
                    txt = r.path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                m = re.match(r"---\n(.*?)\n---", txt, re.DOTALL)
                if not m:
                    continue
                name_m = re.search(r"^name:\s*(\S+)", m.group(1), re.M)
                if not name_m:
                    continue
                skill_name = name_m.group(1)
                record = usage_data.get(skill_name)
                recommended = _recommend_operational(record)
                cur_m = re.search(r"^quality_operational:\s*(\S+)", m.group(1), re.M)
                current = cur_m.group(1) if cur_m else "(brak)"
                if current != recommended:
                    n_runtime_diff += 1
                    print(f"  ⚠️  {skill_name}: {current} (frontmatter) vs {recommended} (runtime) — diff")
            if n_runtime_diff == 0:
                print("  ✓ Wszystkie skille mają quality_operational zgodny z runtime rekomendacją")
            else:
                print(f"  → {n_runtime_diff} skille wymagają ręcznej aktualizacji")
        except ImportError:
            print("⚠️  check_operational_proven.py nie znaleziony — runtime check pominięty")
    selected_failed = n_fail > 0
    if "technical" in levels:
        selected_failed = selected_failed or n_tech_fail > 0
    if args.strict:
        selected_failed = selected_failed or n_warn > 0
    return 1 if selected_failed else 0


if __name__ == "__main__":
    sys.exit(main())

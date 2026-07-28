---
name: using-heos
description: How to use, extend, and contribute to HEOS (Hermes Engineering Operating System). Load when starting any task
  that touches standards, ADR, Skills, or HEOS quality audits.
status: accepted
type: skill
id: skill-using-heos
title: Using HEOS
owner: gaja
created_at: '2026-07-24'
updated_at: '2026-07-28'
review_due: '2027-01-23'
version: 1.5.0
heos_standard_version: '1.2'
tags:
- cross-cutting
related:
- adr-002
- adr-005
- adr-006
- adr-007
- adr-008
- adr-009
- adr-010
- lessons-2026-07-27-heos-audit-fix-bug
- playbook-heos-new-skill
- skill-using-chm
- checklist-heos-pre-commit-validation
quality_schema: pass
quality_technical: pass
quality_operational: unmeasured
---

# Using HEOS

## Cel

HEOS to system standardów, ADR i Skills dla Hermesa. Ten Skill mówi CI (agentowi) jak z niego korzystać efektywnie i jak go rozszerzać bez bałaganu.

## Zakres

**W zakresie:**
- Lokalizacja plików (`skills/`, `decisions/`, `lessons/`, `checklists/`, `playbooks/`, `templates/`, `tools/`)
- Kiedy pisać ADR, kiedy Skill, kiedy Lessons Learned
- Jak uruchomić audyt (`skill_audit.py`, `heos_lint.py`, `check_operational_proven.py`)
- Konwencja commitów i statusów (active/deprecated/superseded)
- Cross-cutting indeksy (`registry.yaml`, `STATUS.md`)
- Wersjonowanie SemVer (major/minor/patch) + tagi git

**Poza zakresem (inne Skillsy):**
- Konkretne domeny (embedded, robotics) — mają własne Skills
- Sam HEOS Master Prompt — to dokument konstytucyjny, nie Skill
- Konfiguracja Hermes profiles — patrz `hermes-agent` skill (główny profil)

## Kiedy używać

- ✅ Zaczynasz zadanie które dotyka standardów, ADR lub Skills
- ✅ Użytkownik pyta "jak coś dodać do HEOS" lub "gdzie to powinno trafić"
- ✅ Przed commitem nowego Skilla — żeby sprawdzić że spełnia 7 obowiązkowych
- ✅ Przy podejmowaniu decyzji architektonicznej — żeby wiedzieć czy iść w ADR
- ✅ Co tydzień (cron `HEOS Weekly Audit`) — do interpretacji raportu audytu

## Kiedy nie używać

- ❌ Zadanie **nie dotyczy** HEOS (czysty feature work, bug fix w kodzie) → nie ładuj tego Skilla
- ❌ Użytkownik chce tylko szybkiej odpowiedzi bez dokumentowania → HEOS to overhead, nie rób go na siłę
- ❌ Pracujesz w profilu `gaja-med` / `gaja-it` — HEOS jest w profilu `gaja` (granice profili: ADR-005)

## Workflow

### 1. Nowy Skill: gdzie i jak

```
skills/<skill-name>.md                      # flat (≤200 linii, brak references)
skills/<skill-name>/SKILL.md                # katalog (≥200 linii lub ma references/scripts)
skills/<skill-name>/references/             # supporting files
skills/<skill-name>/scripts/                # executable helpers
```

Reguła z **ADR-006**: flat dla prostych skilli, katalog dla dużych/z references. Loader Hermesa akceptuje oba formaty.

Wymagane sekcje (7 obowiązkowych):
1. **Cel** — co Skill robi
2. **Zakres** — kiedy ma zastosowanie, co poza
3. **Kiedy używać** — trigger conditions
4. **Kiedy nie używać** — explicit anti-patterns
5. **Workflow** — krok-po-kroku
6. **Przykłady** — ≥1 konkretny use-case
7. **Lessons Learned** — co się sprawdziło, co nie

Plus opcjonalne (8): Typowe błędy, Debugging, Biblioteki, Narzędzia, Oficjalne źródła, Wersjonowanie, Checklisty, Najlepsze praktyki.

Walidacja: `python3 tools/skill_audit.py <ścieżka>`.

### 2. Nowa decyzja architektoniczna: ADR

```
decisions/NNN-krotki-tytul.md
```

Użyj `templates/ADR.md.template`. Numeracja kolejna (3 cyfry). Powiąż z Skills (jeśli istnieją) przez `related: [adr-NNN]` w frontmatter Skilla. ADR jest **Accepted** dopiero po decyzji Jokera — wcześniej status **Proposed**.

### 3. Audyt

```bash
# Pojedynczy Skill
python3 tools/skill_audit.py ścieżka/do/skilla

# Cały HEOS
python3 tools/skill_audit.py HEOS/

# Profil Hermesa
python3 tools/skill_audit.py ~/.hermes/profiles/gaja/skills

# Cross-references (per ADR-008)
python3 tools/heos_lint.py

# Asymetria cross-refs (related forward = backward)
python3 tools/check_related_symmetry.py

# Operational Evidence Model (per ADR-007)
python3 tools/check_operational_proven.py

# Atomic write contract (per ADR-008)
# Wszystkie narzędzia modyfikujące używają _heos_atomic.atomic_write()

# Tygodniowy raport (z opcją save)
python3 tools/weekly_report.py --save
```

Status: `PASS` (kompletne), `WARN` (obowiązkowe OK, brak >2 opcjonalnych), `FAIL` (brak ≥1 obowiązkowego).

### 5. Deprecation

Stary Skill → nagłówek frontmatter:
```yaml
status: deprecated
# lub
status: superseded
superseded_by: skills/new-skill-name
```

Nie usuwaj plików — zostają jako historia.

## Przykłady

### Przykład 1: Pisanie Skilla dla nowej płytki

Sytuacja: dodajesz wsparcie dla nowej płytki (np. ESP32-C3).

Wynik: tworzysz `skills/esp32-c3-micropython-blink/SKILL.md` (jeśli >200 linii lub z references) albo `skills/esp32-c3-micropython-blink.md` (flat) z wszystkimi 7 obowiązkowymi sekcjami + powiązanym ADR jeśli decyzja "dlaczego MicroPython dla C3" jest nieoczywista.

### Przykład 2: Decyzja: serializować stan do JSON czy YAML

Sytuacja: projekt wymaga wyboru formatu serializacji.

Wynik: porównanie w tabelce (szybkość, debugowalność, bezpieczeństwo, ekosystem), decyzja + uzasadnienie → `decisions/011-serialization-format.md`. Potem nowy Skill `using-state-serialization` z `related: [adr-011]`.

### Przykład 3: Deprecate starego Skilla

Sytuacja: Skill `old-orm-guide` opisuje ORM który umarł.

Wynik: w frontmatter `status: deprecated`. W Skills które się do niego odwołują, zaktualizuj `related_skills`. Jeśli jest następca — `superseded_by: skills/new-orm-guide`.

## Lessons Learned (z naszej historii)

1. **HEOS bez enforcementu = muzeum** — 100% Skillsów w profilu gaja było "FAIL" przy pierwszym audycie, bo nikt nie sprawdzał. To jest powód dlaczego mamy `skill_audit.py` i cron.
2. **"Cel" vs "Zakres" to nie to samo** — Cel = co, Zakres = kiedy/granice. Pierwsze wersje HEOS v1.0 miały to pomieszane w jednej sekcji "About".
3. **Płaski numer modułów (00-07) nie skaluje się** — po 10 modułach zaczyna się renumeracja. Dlatego v1.1 przeszło na 2-wymiarową architekturę (domeny × typy artefaktów), a v1.2 upraszcza do płaskiej struktury z tagami.
4. **ADR nie może być opcjonalny** — bez niego każda decyzja ginie przy rotacji kontekstu. Dlatego skill "Framework decyzji" wymaga ADR jako deliverable.
5. **15-punktowy szablon Skilla to za dużo** — 5 sekcji zawsze puste. Dlatego v1.1 ma 7 obowiązkowych + 8 opcjonalnych (z fallbackiem).
6. **Audyt działa nawet z aliasami** — `skill_audit.py` ma 30+ aliasów (angielski ↔ polski, "Workflow" ↔ "How to use"). Pierwszy audyt 0/87 PASS, po naprawie top 3 — lekcja: najpierw audyt, potem poprawki.
7. **Atomic write eliminuje silent corruption** (ADR-008) — `_heos_atomic.atomic_write()` + `transaction()` context manager eliminuje klasę błędów P0-3 (non-atomic) i P0-4 (brak transakcyjności) z `update_quality.py` v2.
8. **Forward ↔ backward related asymmetry** (ADR-007/009) — jeśli Skill A ma `related: [skill-B]`, to Skill B musi mieć `related: [skill-A]`. Asymetria to bug; `check_related_symmetry.py` wykrywa i raportuje.

## Typowe błędy

- **Pisanie Skilla bez uprzedniego audytowania istniejących** — duplikacja. Najpierw `skill_audit.py` + `search_files`, potem pisz.
- **ADR bez daty i statusu** — nikt nie wie czy decyzja jest aktualna. Nagłówek frontmatter (YAML) lub tabelka na górze (Markdown) — obowiązkowo.
- **"Cel" = "Kiedy używać"** — to są dwie różne sekcje. Cel opisuje co, Kiedy używać kiedy.
- **Brak "Kiedy nie używać"** — bez tego Skill będzie używany do wszystkiego, w tym tam gdzie nie powinien.
- **Niecommitowanie HEOS po edycji** — HEOS żyje w `~/gaja-projekty/HEOS`, w git, push do `Joker22pl/gaja-projekty`. Bez push jest lokalne i ginie.

## Debugging

| Objaw | Przyczyna | Fix |
|---|---|---|
| `skill_audit.py` mówi FAIL na sekcji która jest | brak aliasu dla nazwy sekcji | dodaj alias w `ALIASY` dict |
| Tygodniowy raport ma 0% PASS | normalne na początku | plan uzupełniania Skills, nie panika |
| ADR ma złamane linki do Skills | Skill nie istnieje lub zmieniono nazwę | napraw link lub dodaj `superseded` |
| Skill przechodzi audyt ale jest bezużyteczny | ma wszystkie nagłówki ale puste treści | audyt sprawdza strukturę, nie treść — recenzja ręczna |

## Narzędzia (w HEOS `tools/`)

- `skill_audit.py` — walidator Skills (7 obowiązkowych sekcji + 8 opcjonalnych)
- `heos_lint.py` — walidator cross-references + metadanych + spójności
- `check_related_symmetry.py` — wykrywa asymetrię `related: [X]` forward vs backward
- `check_operational_proven.py` — Operational Evidence Model (ADR-007), waliduje runtime usage
- `generate_registry.py` — generuje `.registry.yaml` (indeks artefaktów)
- `generate_status.py` — generuje `STATUS.md` (snapshot stanu)
- `lifecycle_audit.py` — audyt `review_due`, `deprecated`
- `update_frontmatter.py` — aktualizuje frontmatter (migracja)
- `update_quality.py` — aktualizuje `quality_schema`/`quality_technical` (atomic write per ADR-008)
- `weekly_report.py` — raport tygodniowy (cron poniedziałek 9:00 UTC)
- `_heos_atomic.py` — biblioteka atomic write (ADR-008)
- `git` + push do `Joker22pl/HEOS` (branch `main`)

## Oficjalne źródła

- `CONSTITUTION.md` — aktualne zasady (v1.5.2, 2026-07-28)
- `ARCHITECTURE.md` — aktualna architektura (v1.5.2, 2026-07-28)
- `STATUS.md` — auto-generowany snapshot stanu (v1.5.4)
- `CHANGELOG.md` — pełna historia wersji HEOS (v1.0 → v1.5.5)
- ADR rejestr: `decisions/` + `.registry.yaml`
- ADR template: `templates/ADR.md.template`
- Pierwszy audyt (baseline): audyt specjalisty 2026-07-27 (P0/P1/P2 lista)

## Wersjonowanie

- **v1.0** (2026-07-23) — pierwsza wersja, oparta na HEOS Master Prompt v1.0
- **v1.1** (2026-07-23) — 5 ADR, `skill_audit.py`, baseline; 2-wymiarowa architektura (domeny × typy)
- **v1.2** (2026-07-24) — architektura 2D → płaska z tagami; STATUS.md; registry; 3-poziomowa ocena (Schema/Technical/Operational); 6-etapowy lifecycle
- **v1.3** (2026-07-27) — ADR-007 (Operational Evidence), ADR-008 (Atomic Write), `check_operational_proven.py`, `_heos_atomic.py`, GitHub Actions CI, push do `Joker22pl/HEOS`
- **v1.4** (2026-07-28) — ADR-006 (skills format policy), ADR-009 (v1.4 scope); nightly-evolution split 957 → 498 linii + 3 `references/`
- **v1.5** (2026-07-28) — ADR-010 (v1.5 scope); nightly-evolution split Kroki 4-12 → `output-templates.md` (~70% redukcja kontekstu); CHANGELOG.md (audyt historii); STATUS regen

Aktualna wersja tego skilla: **1.5.0** (2026-07-28).

## Checklisty

### Pre-write (nowy Skill)
- [ ] Sprawdziłem `search_files` w HEOS — nie ma duplikatu
- [ ] Mam jasny "Cel" i "Zakres" (to dwie różne rzeczy)
- [ ] Wiem kiedy Skill NIE powinien być użyty

### Post-write
- [ ] `python3 tools/skill_audit.py <ścieżka>` → PASS
- [ ] `python3 tools/heos_lint.py` → 0 findings
- [ ] `python3 tools/check_related_symmetry.py` → 0 asymetrii (per ADR-009)
- [ ] Powiązane ADR istnieje (jeśli decyzja architektoniczna)
- [ ] Commit + push do `Joker22pl/HEOS`

## Najlepsze praktyki

1. **Jeden koncept = jeden Skill** — jeśli Skill ma >500 linii, rozważ podział
2. **Przykłady > opis** — użytkownik (i agent) uczy się szybciej z przykładów
3. **Aliasy w `skill_audit.py` zamiast tłumaczenia nazw sekcji** — pozwala na legacy Skills bez przepisywania
4. **Audyty co tydzień** (cron) — lepiej mały postęp niż wielki jednorazowy
5. **Lessons Learned tylko z prawdziwych doświadczeń** — nie z teorii

## Powiązane

- **ADR-002** — hub repo + osobne repo per projekt
- **ADR-005** — granice profili Hermes
- **ADR-006** — polityka formatu skilli (flat vs katalog)
- **ADR-007** — Operational Evidence Model
- **ADR-008** — Atomic Write Contract
- **ADR-009** — HEOS v1.4 scope
- **ADR-010** — HEOS v1.5 scope
- `CONSTITUTION.md` — konstytucja HEOS (v1.5.2)

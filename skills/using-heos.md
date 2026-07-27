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
updated_at: '2026-07-24'
review_due: '2027-01-23'
version: 1.0.0
heos_standard_version: '1.2'
tags:
- cross-cutting
related:
- adr-002
- adr-005
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---

# Using HEOS

## Cel

HEOS to system standardów, ADR i Skills dla Hermesa. Ten Skill mówi CI (agentowi) jak z niego korzystać efektywnie i jak go rozszerzać bez bałaganu.

## Zakres

**W zakresie:**
- Lokalizacja plików (00-foundation, 01-domains, 02-artifacts, 03-quality, 04-knowledge-graph)
- Kiedy pisać ADR, kiedy Skill, kiedy Lessons Learned
- Jak uruchomić audyt (`skill_audit.py`, `heos_lint.py`)
- Konwencja commitów i statusów (active/deprecated/superseded)
- Cross-cutting indeksy (registry.yaml)

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
HEOS/01-domains/<domena>/skills/<skill-name>/SKILL.md
HEOS/02-artifacts/skills/<skill-name>/SKILL.md   # cross-cutting
```

Wymagane sekcje (7 obowiązkowych):
1. **Cel** — co Skill robi
2. **Zakres** — kiedy ma zastosowanie, co poza
3. **Kiedy używać** — trigger conditions
4. **Kiedy nie używać** — explicit anti-patterns
5. **Workflow** — krok-po-kroku
6. **Przykłady** — ≥1 konkretny use-case
7. **Lessons Learned** — co się sprawdziło, co nie

Plus opcjonalne (8): Typowe błędy, Debugging, Biblioteki, Narzędzia, Oficjalne źródła, Wersjonowanie, Checklisty, Najlepsze praktyki.

Walidacja: `python3 HEOS/03-quality/skill_audit.py <ścieżka>`.

### 2. Nowa decyzja architektoniczna: ADR

```
HEOS/02-artifacts/decision-records/ADR-NNN-krotki-tytul.md
```

Użyj `template.md` z tego katalogu. Wpisz do rejestru w `README.md`. Powiąż z Skills (jeśli istnieją) przez `related-adrs: [ADR-NNN]` w frontmatter Skilla.

### 3. Nowa domena: kiedy?

Domena (`01-domains/<x>/`) to nowy **rozłączny** obszar wiedzy. Dodaj kiedy:
- Masz ≥3 Skillsy które nie pasują do istniejących domen
- To nowy "kierunek" pracy (np. audio synthesis, blockchain — jeśli kiedyś dojdzie)

**Nie dodawaj** domeny "na zapas" — czekaj aż się obroni sama use-case'ami.

### 4. Audyt

```bash
# Pojedynczy Skill
python3 HEOS/03-quality/skill_audit.py ścieżka/do/skilla

# Cały HEOS
python3 HEOS/03-quality/skill_audit.py HEOS/

# Profil Hermesa
python3 HEOS/03-quality/skill_audit.py ~/.hermes/profiles/gaja/skills

# Tygodniowy raport (z opcją save)
python3 HEOS/03-quality/heos_weekly_audit.py --save
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

Wynik: tworzysz `HEOS/01-domains/embedded/skills/esp32-c3-micropython-blink/SKILL.md` z wszystkimi 7 obowiązkowymi sekcjami + powiązanym ADR jeśli decyzja "dlaczego MicroPython dla C3" jest nieoczywista.

### Przykład 2: Decyzja: serializować stan do JSON czy YAML

Sytuacja: projekt wymaga wyboru formatu serializacji.

Wynik: porównanie w tabelce (szybkość, debugowalność, bezpieczeństwo, ekosystem), decyzja + uzasadnienie → ADR-006. Potem nowy Skill `using-state-serialization` z `related-adrs: [ADR-006]`.

### Przykład 3: Deprecate starego Skilla

Sytuacja: Skill `old-orm-guide` opisuje ORM który umarł.

Wynik: w frontmatter `status: deprecated`. W Skills które się do niego odwołują, zaktualizuj `related_skills`. Jeśli jest następca — `superseded_by: skills/new-orm-guide`.

## Lessons Learned (z naszej historii)

1. **HEOS bez enforcementu = muzeum** — 100% Skillsów w profilu gaja było "FAIL" przy pierwszym audycie, bo nikt nie sprawdzał. To jest powód dlaczego mamy `skill_audit.py` i cron.
2. **"Cel" vs "Zakres" to nie to samo** — Cel = co, Zakres = kiedy/granice. Pierwsze wersje HEOS v1.0 miały to pomieszane w jednej sekcji "About".
3. **Plaski numer modułów (00-07) nie skaluje się** — po 10 modułach zaczyna się renumeracja. Dlatego v1.1 przeszło na 2-wymiarową architekturę (domeny × typy artefaktów).
4. **ADR nie może być opcjonalny** — bez niego każda decyzja ginie przy rotacji kontekstu. Dlatego skill "Framework decyzji" wymaga ADR jako deliverable.
5. **15-punktowy szablon Skilla to za dużo** — 5 sekcji zawsze puste. Dlatego v1.1 ma 7 obowiązkowych + 8 opcjonalnych (z fallbackiem).
6. **Audyt działa nawet z aliasami** — `skill_audit.py` ma 30+ aliasów (angielski ↔ polski, "Workflow" ↔ "How to use"). Pierwszy audyt 0/87 PASS, po naprawie top 3 — lekcja: najpierw audyt, potem poprawki.

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

## Narzędzia (w HEOS)

- `HEOS/03-quality/skill_audit.py` — walidator Skills
- `HEOS/03-quality/heos_weekly_audit.py` — raport tygodniowy
- `HEOS/03-quality/heos_lint.py` (TODO) — walidator cross-references
- `git` + push do `Joker22pl/gaja-projekty`

## Oficjalne źródła

- HEOS Master Prompt v1.1: `HEOS/00-foundation/HEOS-MASTER-PROMPT-v1.1.md`
- ADR rejestr: `HEOS/02-artifacts/decision-records/README.md`
- ADR template: `HEOS/02-artifacts/decision-records/template.md`
- Pierwszy audyt (baseline): `HEOS/03-quality/baseline-report-2026-07-23.txt`

## Wersjonowanie

- **v1.0** (2026-07-23) — pierwsza wersja, oparta na HEOS Master Prompt v1.1

## Checklisty

### Pre-write (nowy Skill)
- [ ] Sprawdziłem `search_files` w HEOS — nie ma duplikatu
- [ ] Mam jasny "Cel" i "Zakres" (to dwie różne rzeczy)
- [ ] Wiem kiedy Skill NIE powinien być użyty

### Post-write
- [ ] `python3 HEOS/03-quality/skill_audit.py <ścieżka>` → PASS
- [ ] Powiązane ADR istnieje (jeśli decyzja architektoniczna)
- [ ] Commit + push do `Joker22pl/gaja-projekty`

## Najlepsze praktyki

1. **Jeden koncept = jeden Skill** — jeśli Skill ma >500 linii, rozważ podział
2. **Przykłady > opis** — użytkownik (i agent) uczy się szybciej z przykładów
3. **Aliasy w `skill_audit.py` zamiast tłumaczenia nazw sekcji** — pozwala na legacy Skills bez przepisywania
4. **Audyty co tydzień** (cron) — lepiej mały postęp niż wielki jednorazowy
5. **Lessons Learned tylko z prawdziwych doświadczeń** — nie z teorii

## Powiązane

- **ADR-002** — hub repo + osobne repo per projekt
- **ADR-005** — granice profili Hermes
- HEOS Master Prompt v1.1 — konstytucja

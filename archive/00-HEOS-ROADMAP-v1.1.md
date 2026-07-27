# HEOS — Roadmapa Rozwoju

**Wersja:** 1.1
**Data:** 2026-07-23
**Horyzont:** 6 miesięcy (do 2027-01-23)

---

## Fazy rozwoju

| Faza | Okres | Cel | Status |
|---|---|---|---|
| **F0 — Fundament** | 2026-07-23 | Konstytucja v1.1, 5 ADR, skill_audit, baseline | ✅ DONE |
| **F1 — Egzekucja** | 2026-07-23 → 2026-08-23 | Pierwsze Skillsy w HEOS, heos_lint, cron | ✅ DONE (częściowo) |
| **F2 — Pokrycie** | 2026-08-23 → 2026-10-23 | Uzupełnienie Skillsów profilu Hermesa do 50% PASS | 🟡 TODO |
| **F3 — Dojrzałość** | 2026-10-23 → 2026-12-23 | Pierwsze Lessons Learned, registry.yaml, CI | ⚪ TODO |
| **F4 — Skala** | 2026-12-23 → 2027-01-23 | Knowledge graph, multi-profile, roczny audyt | ⚪ TODO |

---

## F0 — Fundament ✅ (2026-07-23, 1 dzień)

**Status: COMPLETED**

Co zrobiono:
- ✅ Krytyczna analiza RFA v1.0
- ✅ HEOS Master Prompt v1.1
- ✅ 5 ADR z naszej historii
- ✅ `skill_audit.py` (walidator 15-punktowego szablonu)
- ✅ `heos_lint.py` (walidator cross-references)
- ✅ `heos_weekly_audit.py` (cron wrapper)
- ✅ Cron job co poniedziałek 9:00 UTC
- ✅ Baseline audyt 87 Skillsów: 0/87 PASS, 87/87 FAIL

**Metryka:** HEOS działa, jest wersjonowany, ma enforcement. Architektura dwuwymiarowa.

---

## F1 — Egzekucja ✅ (2026-07-23, ten sam dzień)

**Status: COMPLETED**

Co zrobiono:
- ✅ Pierwszy Skill w HEOS: `esp32-s3-micropython-blink` (PASS)
- ✅ Drugi Skill w HEOS: `using-heos` (PASS)
- ✅ 2 Skillsy w profilu Hermesa zaktualizowane do WARN (design-md, heartmula)
- ✅ Cron przetestowany, działa
- ✅ Push na GitHub zweryfikowany przez API

**Metryka:**
- HEOS Skills: 2/2 PASS (100%)
- Profil Hermesa: 0/87 PASS, 2/87 WARN, 85/87 FAIL (z 0/0/87)
- Lint: 0 ERROR, 0 WARN, 2 INFO (orphan ADR-003 i ADR-004)

---

## F2 — Pokrycie (TODO, 2 miesiące: 2026-08-23 → 2026-10-23)

**Cel:** HEOS Skills + profil Hermesa = **50% PASS**

### Priorytety F2 (w kolejności)

| # | Zadanie | Priorytet | Est. czas | KPI |
|---|---|---|---|---|
| F2.1 | Uzupełnij 5 top Skillsów z profilu Hermesa do PASS | P1 | 1 tydzień | 5 Skills z 3/7 → 7/7 |
| F2.2 | Napisz Skill dla ADR-003 (konwencja commitów) | P1 | 1 dzień | `using-commit-conventions` PASS |
| F2.3 | Napisz Skill dla ADR-004 (cookiecutter) | P1 | 1 dzień | `using-cookiecutter` PASS |
| F2.4 | Pierwszy playbook (np. "jak zacząć nowy projekt robota") | P2 | 2 dni | 1 playbook w `02-artifacts/playbooks/` |
| F2.5 | Pierwszy Lessons Learned (z bieżącej pracy) | P1 | ciągły | 1 wpis |
| F2.6 | Pierwszy Engineering Principle (EP-001) | P2 | 1 dzień | 1 EP w `00-foundation/engineering-principles/` |
| F2.7 | Uzupełnij 10 kolejnych Skillsów profilu Hermesa | P2 | 2 tygodnie | 15 Skills z 3/7 → 7/7 |
| F2.8 | ADR dla ESP32-C3 (jeśli pojawi się płytka) | P3 | ad hoc | ADR-006 |

### Kamienie milowe F2

- **2026-08-23** (miesiąc): 10/87 Skills profilu PASS, 2/5 ADR ma Skills
- **2026-09-23** (2 miesiące): 25/87 Skills PASS, pierwszy playbook, pierwszy EP
- **2026-10-23** (koniec F2): **50% Skills PASS**, registry.yaml v0.1

### Ryzyka F2

- **Prokrastynacja** — uzupełnianie 87 Skillsów to żmudne. Mitigation: **max 1 Skill na sesję**, nie więcej.
- **Burnout na formalnościach** — Skillsy to overhead. Mitigation: **pisać Skills przy okazji** (gdy i tak piszesz kod, dopisz Skill), nie jako osobny task.
- **Dryf konstytucji** — HEOS v1.1 może wymagać poprawek po 2 miesiącach używania. Mitigation: **2-miesięczny review** zaplanowany.

---

## F3 — Dojrzałość (TODO, 2 miesiące: 2026-10-23 → 2026-12-23)

**Cel:** HEOS ma **CI, registry, knowledge graph v0.1, regularne Lessons Learned**

### Priorytety F3

| # | Zadanie | Priorytet | Est. czas | KPI |
|---|---|---|---|---|
| F3.1 | GitHub Actions: `skill_audit.py` + `heos_lint.py` per PR | P0 | 2 dni | CI włączone, badge w README |
| F3.2 | `registry.yaml` w `04-knowledge-graph/` | P1 | 1 tydzień | wszystkie Skills + ADR zarejestrowane |
| F3.3 | 5 kolejnych Skillsów w HEOS (cross-cutting + domenowe) | P1 | 2 tygodnie | 7+ Skills w HEOS |
| F3.4 | Pierwszy Checklist (np. "Definition of Done Template") | P2 | 1 dzień | 1 w `02-artifacts/checklists/` |
| F3.5 | 3 Lessons Learned z bieżącej pracy | P1 | ciągły | wpisy co 2 tygodnie |
| F3.6 | 5 kolejnych ADR (z decyzji podejmowanych w międzyczasie) | P1 | ciągły | registry rośnie |
| F3.7 | Review HEOS v1.1, decyzja o v1.2 (lub v2.0) | P2 | 1 dzień | HEOS-MASTER-PROMPT-v1.2.md |
| F3.8 | Migracja 100% Skillsów profilu Hermesa do v1.1 (PASS lub WARN) | P2 | 1 miesiąc | 87/87 spełnia v1.1 |

### Kamienie milowe F3

- **2026-11-23** (miesiąc): CI działa, registry.yaml v0.5, 50% Skills w HEOS ma `related-adrs`
- **2026-12-23** (koniec F3): **CI + registry + 100% zgodność profilu Hermesa**

### Ryzyka F3

- **CI overhead** — Actions dla HEOS to 1-2 min na PR. Mitigation: cache + tylko changed files.
- **Registry rot** — ręcznie utrzymywany YAML się zdezaktualizuje. Mitigation: **automatyczna generacja** z frontmatter (TODO w F4).

---

## F4 — Skala (TODO, 1 miesiąc: 2026-12-23 → 2027-01-23)

**Cel:** HEOS ma **knowledge graph, multi-profile, roczny audyt**

### Priorytety F4

| # | Zadanie | Priorytet | Est. czas | KPI |
|---|---|---|---|---|
| F4.1 | Knowledge graph: zautomatyzowana generacja z frontmatter | P1 | 1 tydzień | `04-knowledge-graph/registry.yaml` auto-generated |
| F4.2 | Multi-profile: HEOS wariant dla `gaja-it` i `gaja-med`? | P3 | dyskusja | decyzja: 1 HEOS czy 3? |
| F4.3 | 5 Engineering Principles (EP-001 do EP-005) | P2 | 2 tygodnie | 5 EP w `00-foundation/engineering-principles/` |
| F4.4 | Self Review template (wymagany po każdym zadaniu) | P1 | 2 dni | template w `03-quality/templates/` |
| F4.5 | Roczny audyt HEOS: co zadziałało, co nie, co zmienić | P0 | 1 dzień | `00-foundation/HEOS-2026-REVIEW.md` |
| F4.6 | HEOS v2.0 (jeśli roczny audyt wskaże potrzebę) | P2 | 1 tydzień | HEOS-MASTER-PROMPT-v2.0.md |

### Kamienie milowe F4

- **2027-01-23** (koniec F4): **HEOS v2.0 gotowy, roczny audyt publicznie dostępny**

---

## Priorytety absolutne (cross-fazowe)

### P0 — nigdy nie odpuszczaj
- Bezpieczeństwo (P0 w HEOS = P0 w tej roadmapie)
- Definition of Done (każde zadanie)
- Lessons Learned (po większych zadaniach)
- ADR (przy każdej decyzji architektonicznej)

### P1 — rób regularnie
- Cotygodniowy audyt Skills (cron działa)
- Nowy Skill przy każdej nowej technologii
- Cross-references poprawne (heos_lint)

### P2 — rób przy okazji
- Uzupełnianie istniejących Skillsów
- Nowe ADR dla bieżących decyzji
- Backlog cleanup (deprecated Skills)

### P3 — rób gdy trzeba
- Nowe domeny
- Multi-profile HEOS
- Rozbudowa narzędzi (np. heos_lint v2)

### Nie rób (YAGNI)
- Mikroserwisy / rozproszone HEOS — to **jeden** system, nie 10
- Własny język zapytań — YAML + markdown wystarczy
- Blockchain / AI do generowania ADR — overkill
- Automatyczne tłumaczenie Skills na inne języki — niepotrzebne

---

## Metryki sukcesu (roczne)

| Metryka | Baseline (2026-07-23) | Cel roczny (2027-07-23) |
|---|---|---|
| Skills w HEOS spełniające standard | 2/2 (100%) | 20+/20+ (100%) |
| Skills profilu Hermesa PASS | 0/87 (0%) | 80/87 (92%) |
| ADR z Skillsem (non-orphan) | 3/5 (60%) | 15/15 (100%) |
| Cotygodniowy audyt działa bez przerwy | ✅ | ✅ |
| Lessons Learned napisane | 0 | ≥12 (1/miesiąc) |
| Engineering Principles | 0 | ≥10 |
| Cross-references w registry.yaml | 0% | 100% |
| Multi-profile (gaja, gaja-it, gaja-med) | tylko gaja | wszystkie 3 (jeśli decyzja) |

---

## Otwarte pytania (do decyzji w trakcie rozwoju)

1. Czy HEOS powinien mieć **multi-profile** (gaja, gaja-it, gaja-med) czy **jeden współdzielony**?
2. Czy Skillsy profilu Hermesa powinny **migrować** do HEOS, czy zostać w profilu z audytem?
3. Czy Engineering Principles to **osobny katalog** czy **sekcja w 00-foundation**?
4. Czy registry.yaml to **plik** czy **baza danych** (SQLite)?

Patrz `00-HEOS-OPEN-DECISIONS.md` dla pełnej listy.

---

*Patrz też: `00-HEOS-OVERVIEW.md` (co jest), `00-HEOS-ARCHITECTURE.md` (jak działa), `00-HEOS-OPEN-DECISIONS.md` (co nie wiemy).*

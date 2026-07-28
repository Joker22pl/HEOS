---
# === Wspólne metadane (wymagane) ===
type: adr
id: adr-009
name: 009-heos-v1-4-scope
title: HEOS v1.4 — scope deklaracja (split nightly-evolution, CHANGELOG)
status: accepted
owner: gaja
created_at: '2026-07-28'
updated_at: '2026-07-28'
review_due: '2027-01-26'
version: 1.0.0
heos_standard_version: "1.2"
tags:
- cross-cutting
- heos-internal
- governance
related:
- adr-006
- adr-007
- adr-008
- skill-nightly-evolution

# === Specyficzne dla ADR ===
adr_number: 9
superseded_by: (none)

# === Jakość ===
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---

# ADR-009: HEOS v1.4 — scope deklaracja

## Status

Accepted (2026-07-28). Deklaracja zakresu v1.4 zamyka v1.3 (który zakończył się tagiem `v1.3.2`, commit `8cda935`).

## Kontekst

Po v1.3.2 (commit `8cda935`, 2026-07-28) HEOS ma:

- 17 artefaktów (7 skilli + 8 ADR + 1 lessons + 1 checklist + 1 playbook)
- 60/60 testów PASS, wszystkie bramki zielone
- 1 działający CI run na GitHub Actions (15/15 success)
- `Joker22pl/HEOS` pushnięty, publiczny

Pozostałe znalezione w audycie specjalisty (2026-07-27) tematy techniczne:

| Temat | Severity | Źródło |
|---|---|---|
| `nightly-evolution.md` = 957 linii | P2 (token economy) | raport §14.1 |
| Brak `CHANGELOG.md` | P2 (audyt) | raport §20.2, P2-8 |
| 6 różnych list wykluczeń katalogów w narzędziach | P2 (CTX-2) | raport §6 |
| Brak `--check` mode w `update_quality.py` | P2 | raport P2-3 |
| Brak reverse-deps check przed archiwizacją | P2 (lifecycle) | raport P2-10 |
| Bug: STATUS liczy 25 tools, real 22 | P2 (drobiazg) | obserwacja |

Wszystkie pozostałe P0/P1 z raportu są zamknięte (P0-1..P0-5, P1-1, P1-2, P1-6, P1-7 — przez `_heos_atomic.py`, `check_operational_proven.py`, GitHub Actions CI, push do GH, 60 testów).

## Decyzja

**v1.4 ma TYLKO dwa cele:**

1. **Split `nightly-evolution.md`** (957 linii → ~200 linii SKILL.md + 4 references/)
   - `skills/nightly-evolution/SKILL.md` (≤200 linii) — overview + workflow + kroki 0-2
   - `references/etap-K-knowledge-routing.md` (~150 linii)
   - `references/etap-L-error-intelligence.md` (~120 linii)
   - `references/cron-job-prompt.md` (~100 linii)
   - `references/data-sources.md` (~80 linii)

2. **`CHANGELOG.md`** — audyt wersji HEOS z pełną historią v1.0 → v1.4 (manuskrypt z archiwum + v1.1/v1.2/v1.3/v1.4 dodane).

## Uzasadnienie

| Cel | Kryterium | Ocena |
|---|---|---|
| 1. Split nightly-evolution | Token economy | Realna oszczędność ~50% kontekstu przy każdym ładowaniu (3-4K tokenów → ~1.5-2K). Przy ~30 uses/miesiąc = ~120K tokenów/rok |
| 1. Split nightly-evolution | Jakość (granica 500 linii HEOS) | Raport §7.3: `memory-hygiene/SKILL.md` 674 linii przekraczało heurystyczną granicę HEOS i wymagało refaktoru. `nightly-evolution` 957 linii = 2× to. |
| 2. CHANGELOG.md | Audyt | Zewnętrzny audytor / specjalista musi widzieć "co było w której wersji" bez rekonstrukcji z `git log`. |

**Oba cele mają jasny "Definition of Done" i mierzalny efekt.**

## Konsekwencje

**Pozytywne:**

- v1.4 jest krótka (2 commity, ~3h pracy łącznie), zamyka realne otwarte tematy.
- Brak nowego API / nowych narzędzi — tylko reorganizacja istniejącego kodu.
- Idempotentne: split nie zmienia zachowania `nightly-evolution`, tylko strukturę pliku.

**Negatywne / ryzyka:**

- **Ryzyko split:** jeśli podział na references zostanie zrobiony niepoprawnie (np. wycięty krok z głównego SKILL.md), skill przestanie działać w runtime. Mitigation: każdy etap (każdy reference osobno) = osobny commit + smoke-test (ręczne uruchomienie `python3 tools/skill_audit.py skills/nightly-evolution/SKILL.md`).
- **Ryzyko CHANGELOG:** dług techniczny do utrzymania (każdy nowy release = nowy wpis). Mitigation: reguła "release commit musi aktualizować CHANGELOG w tym samym PR" (dokumentujemy w playbook `heos-new-skill.md` przy okazji).
- **Manifest deploy, knowledge graph, multi-profile** — **wszystkie odłożone do v1.5+**. ADR-009 to formalnie zamyka.

## NIE zawiera (anty-scope-creep)

v1.4 **nie obejmuje**:

- ~~`Faza 2: deploy-manifest.yaml`~~ (raport §15.4) — odłożone do v1.5
- ~~`Faza 3: 85 runtime skills → HEOS`~~ (raport §19.3) — odłożone do v1.6+
- ~~`Faza 4: knowledge graph v2.0`~~ (raport §21) — odłożone do v2.0 (warunek: ≥200 artefaktów)
- ~~`heos_core/` biblioteka parsera~~ (raport §11.3) — pozostała duplikacja jest kosmetyczna, `_heos_atomic.py` rozwiązał najważniejszy przypadek
- ~~ADR-006 (skills format policy)~~ — **zrobiony** w v1.3.2 (commit `8cda935`)
- ~~Bug w `generate_status.py` (Tools: 25 vs 22)~~ — drobiazg, robię razem z CHANGELOG jeśli w ogóle
- ~~P2-5 (6 list wykluczeń katalogów)~~ — scentralizowane w `heos_core/paths.py` należy do v1.5+
- ~~P2-3 (brak `--check` mode w `update_quality.py`)~~ — narzędzie działa z `--dry-run`, dodanie `--check` to kosmetyka

## Alternatywy rozważone

- **Opcja A — v1.4 = tylko split, CHANGELOG w v1.5.** Odrzucona: CHANGELOG jest mały (30 min) i naturalnie wpisuje się w release v1.4.
- **Opcja B — v1.4 = split + bug fix STATUS + 6 list wykluczeń.** Odrzucona: scope creep. Bug STATUS to 5-minutowa poprawka, ale nie należy do "celu v1.4". Wrzucam do CHANGELOG jako "backlog po v1.4" jeśli w ogóle.
- **Opcja C — v1.4 = tylko `Faza 2: deploy-manifest.yaml`.** Odrzucona: deploy manifest dla 5 mostów to kosmetyka. Mamy `validate_symlinks.py`, który działa. Manifest nie rozwiązuje żadnego realnego problemu.

## Kiedy rewizja

- **2027-01-26** (review_due). Sprawdzić czy v1.5 powinno być Fazą 2 (deploy manifest) czy coś innym.
- **Warunek wcześniejszej rewizji:** Jeśli pojawi się nowy skill > 500 linii (split staje się wzorcem) — może warto automatyzować.

## Lessons Learned

v1.4 zaczyna się od **tylko 2 celów**, mimo że raport specjalisty wymieniał 10+ tematów. Wynika to z dwóch obserwacji:

1. **Scope creep zabija projekty.** Każdy "no ale to mały PR" wpycha v1.4 w v1.4+1+2+...+n. Lepiej mieć 2 twarde cele z mierzalnym efektem niż 10 luźnych z commit hop.
2. **Definition of Done jest binarny.** "Split nightly-evolution" — albo plik ma < 200 linii albo nie. "Manifest deploymentu" — nie ma kryterium ukończenia.

Wzór do przyszłych wersji: każda wersja = 1-2 cele z wyraźnym DoD, reszta formalnie odłożona do następnej.

## Powiązane

- ADR-006 — Skills format policy (uzasadnia dlaczego split jest naturalną konsekwencją reguły "≥200 linii lub ma references = katalog")
- ADR-007 — Operational Evidence Model (pozwala zmierzyć runtime użycie nightly-evolution, co uzasadnia priorytet refaktoru)
- ADR-008 — Atomic Write Contract (`_heos_atomic.py` już jest, split korzysta z niego przy ewentualnej modyfikacji frontmatter)
- `skills/nightly-evolution/SKILL.md` (po split) — główny plik skilla
- `references/etap-K-knowledge-routing.md` (po split) — nowy
- `references/etap-L-error-intelligence.md` (po split) — nowy
- `references/cron-job-prompt.md` (po split) — nowy
- `references/data-sources.md` (po split) — nowy
- `CHANGELOG.md` (po v1.4) — audyt wersji
- Raport audytu specjalisty 2026-07-27, §14.1 (propozycja splitu) + §20.2 (propozycja CHANGELOG)

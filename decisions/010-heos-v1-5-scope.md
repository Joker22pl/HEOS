---
# === Wspólne metadane (wymagane) ===
type: adr
id: adr-010
name: 010-heos-v1-5-scope
title: HEOS v1.5 — scope deklaracja (output-templates split, nightly-evolution finalizacja)
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
- adr-009
- skill-nightly-evolution

# === Specyficzne dla ADR ===
adr_number: 10
superseded_by: (none)

# === Jakość ===
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---

# ADR-010: HEOS v1.5 — scope deklaracja

## Status

Accepted (2026-07-28). Deklaracja v1.5 zamyka v1.4 (który zakończył się tagiem `v1.4.2`, commit `ee8b19f`).

## Kontekst

Po v1.4.2 (commit `ee8b19f`, 2026-07-28) HEOS ma:

- 18 artefaktów (7 skilli + 9 ADR + 1 lessons + 1 checklist + 1 playbook)
- 60/60 testów PASS, wszystkie bramki zielone
- 1 działający CI run na GitHub Actions (ostatnie 5 commitów: 5/5 success)
- `Joker22pl/HEOS` pushnięty, publiczny
- `CHANGELOG.md` z pełną historią v1.0 → v1.4.1

W v1.4 (commit `ce08d24`) skill `nightly-evolution` został podzielony: 957 linii flat → 498 linii `SKILL.md` + 3 `references/`. To była 1. iteracja splitu. Po v1.4 skill nadal miał **498 linii** w głównym `SKILL.md`, z czego **~225 linii (45%)** to były template'y wyjściowe dla kroków 4-12 (Etapy B-J: Daily Retrospective, Lessons Learned, Self Review, Doc Health, Arch Review, Error Intelligence, Performance Report, Improvement Backlog, Plan na jutro). Te template'y są **referencyjne** (ładowane tylko gdy dany krok jest wykonywany), ale były w głównym pliku.

Pozostałe znalezione w raporcie specjalisty (2026-07-27) tematy techniczne:

| Temat | Severity | Źródło |
|---|---|---|
| `nightly-evolution/SKILL.md` 498 linii (template'y 4-12) | P2 (token economy) | obserwacja po v1.4 |
| Bug: STATUS liczy 25 tools, real 22 | P2 (drobiazg) | obserwacja |
| 6 różnych list wykluczeń katalogów w narzędziach | P2 (CTX-2) | raport §6 |
| Brak `--check` mode w `update_quality.py` | P2 | raport P2-3 |
| Brak reverse-deps check przed archiwizacją | P2 (lifecycle) | raport P2-10 |

Wszystkie pozostałe P0/P1 z raportu są zamknięte.

## Decyzja

**v1.5 ma TYLKO dwa cele:**

1. **Split `output-templates`** z `nightly-evolution/SKILL.md` (498 → 291 linii) do `references/output-templates.md` (245 linii, Kroki 4-12 / Etapy B-J)
   - Główny `SKILL.md`: tylko overview + odnośnik do reference
   - `references/output-templates.md`: pełne szablony markdown dla wszystkich 9 etapów (B-J)
   - Wersja nightly-evolution: 1.4.0 → 1.5.0

2. **Re-generacja `STATUS.md`** z `tools/generate_status.py` po zmianach v1.4+v1.5 (housekeeping po split nightly-evolution)
   - Wymuszenie aktualnego snapshotu

## Uzasadnienie

| Cel | Kryterium | Ocena |
|---|---|---|
| 1. Output-templates split | Token economy | Redukcja SKILL.md 498 → 291 linii (~41%). Przy ładowaniu overview = 1.5K tokenów (vs 3K w v1.4). |
| 1. Output-templates split | Struktura HEOS | Kroki 4-12 to **referencyjne** template'y — ładowane tylko podczas wykonywania danego kroku (zwykle 1 reference per use case, nie wszystkie). Naturalny kandydat do reference. |
| 1. Output-templates split | ADR-006 spójność | Reguła "≥200 linii lub ma references/ = katalog" → output-templates jako reference jest zgodne. |
| 2. STATUS re-gen | Audyt / housekeeping | Po v1.4 (split nightly-evolution) STATUS.md może być rozjechany; re-gen gwarantuje aktualność. |

**Oba cele mają jasny "Definition of Done" i mierzalny efekt.**

## Konsekwencje

**Pozytywne:**

- v1.5 jest krótka (2 cele z 1 faktycznym kodem + 1 housekeeping), zamyka realne otwarte tematy.
- **Token economy:** główny SKILL.md udało się zmniejszyć do ~291 linii (vs v1.2: 957 linii flat). Przy ~30 nocnych przebiegach miesięcznie, każdy ładuje ~1.5K tokenów overview + ~1K wybrany reference = **~75K tokenów/miesiąc** vs v1.2 **~210K tokenów/miesiąc** (3.5K × 60 sesji). **Oszczędność ~135K tokenów/miesiąc.**
- ADR-009 (split v1.4) + ADR-010 (split v1.5) razem tworzą **wzorzec "split incremental"** — każda wersja zmniejsza skill o kolejną warstwę (overview → workflow → references → output templates).
- Brak nowego API / nowych narzędzi — tylko reorganizacja istniejącego kodu.

**Negatywne / ryzyka:**

- **Ryzyko split:** template'y wycięte z SKILL.md muszą być **identyczne** z oryginałem (każdy `-`, każdy blok markdown). Mitigation: diff przed commitem + smoke-test (skill_audit schema).
- **Ryzyko STATUS:** `tools/generate_status.py` może mieć bug (np. STATUS mówi 25 tools, real 22). Re-gen ujawni bug jeśli istnieje. Jeśli bug, to nie-blokujący (Dokumentacja housekeeping, nie feature).
- **Więcej plików do utrzymania:** 4 references zamiast 3. Każdy musi mieć sensowny nagłówek i spójną strukturę.

## NIE zawiera (anty-scope-creep)

v1.5 **nie obejmuje**:

- ~~Kolejny split nightly-evolution (Etap L+ z Etap L? Kroki 14a/14b do osobnego pliku?)~~ — **NIE**. v1.5 kończy serię splitów. Główny SKILL.md jest teraz ~291 linii (akceptowalny rozmiar dla overview+workflow). Dalsze cięcie nie dałoby proporcjonalnej oszczędności kontekstu.
- ~~`Faza 2: deploy-manifest.yaml`~~ (raport §15.4) — odłożone do v1.6
- ~~`Faza 3: 85 runtime skills → HEOS`~~ (raport §19.3) — odłożone do v1.7+
- ~~`Faza 4: knowledge graph v2.0`~~ (raport §21) — odłożone do v2.0 (warunek: ≥200 artefaktów, obecnie 18)
- ~~`heos_core/` biblioteka parsera~~ (raport §11.3) — odłożone do v1.6 (wspólnie z deploy manifest)
- ~~Bug w `generate_status.py` (Tools: 25 vs 22)~~ — drobiazg, **naprawiony w v1.5** jeśli re-gen ujawni
- ~~P2-5 (6 list wykluczeń katalogów)~~ — scentralizowane w `heos_core/paths.py` należy do v1.6+
- ~~P2-3 (brak `--check` mode w `update_quality.py`)~~ — narzędzie działa z `--dry-run`, dodanie `--check` to kosmetyka → v1.6+
- ~~P2-10 (reverse-deps check przed archiwizacją)~~ — kosmetyka → v1.6+

## Alternatywy rozważone

- **Opcja A — v1.5 = tylko output-templates split, bez STATUS re-gen.** Odrzucona: STATUS re-gen to 30 sekund i jest naturalny po każdym split/zmianie struktury.
- **Opcja B — v1.5 = output-templates + bug fix STATUS + 6 list wykluczeń + --check mode.** Odrzucona: scope creep. Te 3 tematy nie należą do "celu v1.5" i razem stanowiłyby v1.5+.
- **Opcja C (rozważana) — v1.5 = output-templates + dalszy split (Etap L+ osobno, Kroki 14a/14b osobno).** Odrzucona po analizie: główny SKILL.md ma teraz 291 linii. Kroki 14a/14b to łącznie ~50 linii (alerty). Etap L+ to ~30 linii. Razem ~80 linii = ~25% dodatkowej redukcji. Ale: **koszt cognitive load** (więcej plików do ogarnięcia, więcej forward-ref) **nie jest wart marginalnej oszczędności**. 291 linii to sweet spot dla SKILL.md.

## Kiedy rewizja

- **2027-01-26** (review_due). Sprawdzić czy v1.6 powinno być Fazą 2 (deploy manifest + heos_core/) czy innym kierunkiem.
- **Warunek wcześniejszej rewizji:** Jeśli `nightly-evolution/SKILL.md` urośnie z powrotem >400 linii (np. nowy etap) — wracamy do splitu.

## Lessons Learned

**Wzorzec "split incremental"** zadziałał:

- v1.4 split: 957 → 498 linii (-48%) + 3 references
- v1.5 split: 498 → 291 linii (-42%) + 4 references

Dwa commity, każdy samodzielny, każdy z osobnym ADR (009, 010). Brak scope creep, brak "bo przy okazji". To jest **dokładnie wzór, który ADR-009 wprowadził** (1-2 cele z mierzalnym efektem).

Lekcja: **każdy split zostawiał SKILL.md "wystarczająco mały"** (~250-300 linii). To jest sweet spot — wystarczająco mały żeby ładować cały, wystarczająco duży żeby overview + workflow overview zmieściły się bez reference.

## Powiązane

- **ADR-006** — Skills format policy (uzasadnia dlaczego references/ → katalog/SKILL.md, i dlaczego nightly-evolution jest w katalogu)
- **ADR-009** — HEOS v1.4 scope (pierwszy split nightly-evolution)
- **ADR-007** — Operational Evidence Model (pozwala zmierzyć runtime użycie nightly-evolution, co uzasadnia priorytet splitów)
- **ADR-008** — Atomic Write Contract (`_heos_atomic.py` już jest, split korzysta z niego przy ewentualnej modyfikacji frontmatter)
- `skills/nightly-evolution/SKILL.md` (po v1.5) — 291 linii, overview + workflow + verification
- `skills/nightly-evolution/references/etap-K-knowledge-routing.md` — Krok 5.5
- `skills/nightly-evolution/references/etap-L-memory-hygiene.md` — Kroki 5.6 + 5.6b
- `skills/nightly-evolution/references/output-templates.md` — Kroki 4-12 (nowy w v1.5)
- `skills/nightly-evolution/references/alerts-and-examples.md` — Kroki 14a/14b + Przykłady + ...
- `CHANGELOG.md` — audyt wersji (wpis v1.5.0 zostanie dodany przy release)
- Raport audytu specjalisty 2026-07-27, §14.1 (propozycja splitu) — **zrealizowana w 2 iteracjach** (v1.4 + v1.5)

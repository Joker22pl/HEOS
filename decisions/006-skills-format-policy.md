---
# === Wspólne metadane (wymagane) ===
type: adr
id: adr-006
name: 006-skills-format-policy
title: Polityka formatu Skills — kiedy .md vs katalog
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
- authoring
related:
- adr-005
- adr-009
- adr-011
- skill-nightly-evolution
- adr-010
- skill-using-heos

# === Specyficzne dla ADR ===
adr_number: 6
superseded_by: (none)

# === Jakość ===
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---

# ADR-006: Polityka formatu skilli

## Status

Accepted (2026-07-28). Numer ustalony retroaktywnie — luka ADR-006 istniała od migracji v1.1→v1.2 (2026-07-24) i jest zamykana tym dokumentem.

## Kontekst

Po v1.2.0 w `skills/` mamy mieszane formaty:

- 5 plików `.md` płasko: `esp32-s3-micropython-blink.md`, `nightly-evolution.md`, `using-chm.md`, `using-heos.md`, `memory-hygiene.md` (ten ostatni to katalog po refaktorze 2026-07-27 — patrz poniżej)
- 2 katalogi z `SKILL.md`: `embedded-communications-debug/`, `gaja-lab-core/`, `memory-hygiene/`

Brak formalnej reguły decydującej kiedy który format. To powodujeło realne problemy:

1. **Duplikat** (v1.2): `skills/memory-hygiene.md` + `skills/memory-hygiene/SKILL.md` koegzystowały. Most w profilu wskazywał na plik, ale `memory-hygiene.md` referencjował `references/race-condition-signs.md` (katalog). Wymagało ręcznego refaktoru 2026-07-27.
2. **Niejawne oczekiwania** — autorzy nowych skillów musieli zgadywać który format wybrać.

## Decyzja

Obowiązuje następująca reguła wyboru formatu dla nowych skillów:

| Warunek | Format |
|---|---|
| `< 200 linii` ORAZ brak `references/`/Oraz brak `scripts/` | `skills/<name>.md` (flat) |
| `≥ 200 linii` LUB ma `references/` LUB ma `scripts/` | `skills/<name>/SKILL.md` (katalog) |
| Skill runtime z `data_root: ~/.hermes/...` | preferowany `skills/<name>.md` (mniejsze ryzyko w loaderze Hermesa, CP #23) |

**Loader Hermesa akceptuje oba formaty** — most w profilu może wskazywać na `<name>.md` lub `<name>/SKILL.md` (potwierdzone w HEOS-operations CP #23).

## Uzasadnienie

| Kryterium | Plik `.md` | Katalog `SKILL.md` | **Reguła hybrydowa** |
|---|---|---|---|
| Prostota dla małych skillów | ✅ | ❌ (narzut) | ✅ oba |
| Rozszerzalność (references, scripts) | ❌ | ✅ | ✅ dla dużych |
| Loader Hermesa | ✅ | ✅ | ✅ oba |
| Spójność z istniejącym kodem | ✅ 4 istniejące | ✅ 3 istniejące | ✅ nie łamie niczego |
| Audyt HEOS (`skill_audit.py`) | ✅ | ✅ | ✅ oba w `HEOS_KATALOGI` |
| Decyzyjność dla nowego autora | ❌ (trzeba zgadywać) | ❌ | ✅ jasna reguła |

Reguła prosta, jednoznaczna, nie wymaga migracji istniejących skillów.

## Konsekwencje

**Pozytywne:**

- Każdy nowy skill ma jasny format wynikający z jego rozmiaru i zawartości.
- Zero dodatkowej pracy dla małych skillów.
- Duże skille (z references) naturalnie lądują w katalogu, co jest zgodne z ich strukturą.
- Audyt HEOS (`HEOS_KATALOGI`) już poprawnie rozróżnia oba formaty.

**Negatywne / ryzyka:**

- 2 istniejące skille łamią regułę: `using-heos.md` (216 linii, brak references) i `esp32-s3-micropython-blink.md` (247 linii, brak references) — ale są "blisko granicy" i nie ma potrzeby ich migrować.
- Brak mechanizmu wymuszającego regułę (audyt nie sprawdza czy SKILL.md > 200 linii powinien być w katalogu).
- `gaja-lab-core/SKILL.md` ma tylko 307 linii ale jest katalogiem bo ma `scripts/lab_helper.py` (780 linii) — reguła "ma scripts/" go łapie poprawnie.

## Alternatywy rozważone

- **Opcja A — Wszystko jako katalog.** Spójność, ale 5 istniejących `.md` wymagałoby migracji (medium effort, niska wartość — są małe, działają jako `.md`).
- **Opcja B — Wszystko jako `.md`.** Prostota, ale koliduje z istniejącymi katalogami (3 skille z references/scripts) i naturalnym wzorcem "skill z references jest katalogiem".
- **Opcja C (odrzucona) — Reguła `> 200` bez wyjątku.** Gaja-lab-core (307 linii SKILL.md ale 1087 linii z scripts) łamałby regułę. Rozwiązaniem byłoby rozbicie SKILL.md na mniejsze części, ale to mikro-optymalizacja.

## Kiedy rewizja

- Gdy pojawi się **trzeci format** (np. `skill.yaml` z osobnym plikiem treści) — wracamy do tematu.
- Gdy audyt HEOS (`heos_lint.py`) będzie wymuszał zgodność z regułą — możemy ją doprecyzować.
- Przy review_due (2027-01-26) — sprawdzić czy granica 200 linii nadal ma sens dla nowych skillów.

## Lessons Learned

Reguła powinna być tak prosta, że jej wytłumaczenie zajmuje 3 linie. Alternatywy (A i B) były bardziej "eleganckie", ale wymagały migracji istniejącego kodu dla **czysto kosmetycznej** spójności. Wybrana reguła hybrydowa zachowuje 100% istniejącej pracy i daje jasny drogowskaz na przyszłość.

Luka numeracyjna ADR-006 istniała od 2026-07-24 do 2026-07-28 (4 dni). Pojedynczy commit zamykający lukę jest lepszy niż wstawianie ADR-007 z numerem "006" (zaburzyłoby chronologię przyjęć).

## Powiązane

- ADR-005 — Granice profili Hermes (kontekst: profile mają własne runtime Skills, HEOS jest warstwą standardów)
- ADR-002 — Hub repo + osobne repo per projekt (HEOS jest osobnym repo `Joker22pl/HEOS` od 2026-07-27)
- Raport audytu specjalisty 2026-07-27, §13 (analiza formatu skilli) — propozycja oparta na tej analizie, ale uproszczona
- CP #23 w HEOS-operations (loader Hermesa akceptuje oba formaty)

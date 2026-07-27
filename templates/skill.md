---
# === Wspólne metadane (wymagane w każdym artefakcie) ===
type: skill
id: skill-<kebab-case-name>
name: <kebab-case-identyfikator>
title: <Tytuł czytelny dla człowieka>
status: draft                              # draft | proposed | reviewed | accepted | deprecated | archived
owner: gaja                                # gaja | joker
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
review_due: YYYY-MM-DD                     # kiedy obowiązkowy przegląd
version: 0.1.0
heos_standard_version: "1.2"
tags: [<domena>, <technologia>]             # np. [embedded, esp32, micropython]
related: [<ref-do-innego-artefaktu>]         # np. [ADR-001, skill-using-heos]

# === Jakość (3-poziomowa ocena) ===
quality_schema: pending                     # pending | pass | fail
quality_technical: pending                  # pending | pass | fail
quality_operational: unmeasured             # unmeasured | fresh | proven
---

# <Tytuł Skilla>

## Cel

[1-2 zdania: co ten Skill robi i dla kogo]

## Zakres

**W zakresie:**
- [lista konkretnych zastosowań]

**Poza zakresem (patrz inne Skills):**
- [gdzie NIE używać, z odsyłaczem do powiązanego Skilla]

## Kiedy używać

- ✅ [trigger 1]
- ✅ [trigger 2]

## Kiedy nie używać

- ❌ [anti-pattern 1]
- ❌ [anti-pattern 2]

## Workflow

[Krok po kroku co zrobić. Dla złożonych — numbered list, dla prostych — code block]

## Przykłady

### Przykład 1: [nazwa sytuacji]

Sytuacja: [opis]

Wynik: [oczekiwany rezultat]

### Przykład 2: [nazwa sytuacji]

Sytuacja: [opis]

Wynik: [oczekiwany rezultat]

## Lessons Learned

[Co się sprawdziło, co nie, wnioski na przyszłość. Wymagane — brak = FAIL Schema.]

## Typowe błędy

- [błąd 1 + jak uniknąć]
- [błąd 2 + jak uniknąć]

## Debugging

| Objaw | Przyczyna | Fix |
|---|---|---|
| [objaw 1] | [przyczyna] | [rozwiązanie] |
| [objaw 2] | [przyczyna] | [rozwiązanie] |

## Biblioteki

- [nazwa 1: wersja, cel]
- [nazwa 2: wersja, cel]

## Narzędzia

- [narzędzie 1: cel]
- [narzędzie 2: cel]

## Oficjalne źródła

- [link 1: tytuł, dlaczego wiarygodne]
- [link 2: tytuł, dlaczego wiarygodne]

## Wersjonowanie

- **vX.Y** (YYYY-MM-DD) — [krótki opis zmiany]

## Checklisty

### Pre-flight
- [ ] [wymagane przed użyciem 1]
- [ ] [wymagane przed użyciem 2]

### Post-use
- [ ] [wymagane po użyciu 1]
- [ ] [wymagane po użyciu 2]

## Najlepsze praktyki

1. [zasada 1]
2. [zasada 2]

## Powiązane

- [ADR-NNN: tytuł, dlaczego powiązane]
- [skill-X: dlaczego powiązane]

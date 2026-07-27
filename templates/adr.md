---
# === Wspólne metadane (wymagane) ===
type: adr
id: adr-NNN
name: <krotki-tytul-kebab-case>
title: <Tytuł decyzji — pełne zdanie>
status: draft                              # draft | proposed | reviewed | accepted | superseded | deprecated | archived
owner: gaja
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
review_due: YYYY-MM-DD
version: 0.1.0
heos_standard_version: "1.2"
tags: [<domena>, <technologia>]
related: [<ref-do-skilla-lub-innego-adr>]

# === Specyficzne dla ADR ===
adr_number: NNN                             # wymagane, unikalne, numeryczne
superseded_by: adr-NNN                      # opcjonalne, jeśli ten ADR jest zastąpiony

# === Jakość ===
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---

# ADR-NNN: <Tytuł decyzji>

## Kontekst

[Jaki problem rozwiązujemy? Jakie tło? Linki do rozmów / issue / research.]

## Decyzja

[Co wybraliśmy — jedno zdanie, jasne.]

## Uzasadnienie

| Kryterium | Opcja A (odrzuc.) | Opcja B (odrzuc.) | **Wybrana** |
|---|---|---|---|
| Bezpieczeństwo (P0) | ... | ... | ... |
| Poprawność (P1) | ... | ... | ... |
| Jakość (P2) | ... | ... | ... |
| Skalowalność (P3) | ... | ... | ... |
| Dokumentacja | ... | ... | ... |
| Społeczność | ... | ... | ... |

## Konsekwencje

**Pozytywne:**
- [korzyść 1]
- [korzyść 2]

**Negatywne / ryzyka:**
- [ryzyko 1 + mitigation]
- [ryzyko 2 + mitigation]

## Alternatywy rozważone

- **Opcja A** — odrzucona bo [powód].
- **Opcja B** — odrzucona bo [powód].

## Kiedy rewizja

[Warunek kiedy wracamy do tematu. Przykłady:
- "Gdy pojawi się 2. użytkownik tego skilla"
- "Gdy biblioteka X przestanie być wspierana"
- "Gdy obciążenie > 1000 req/s"]

## Lessons Learned

[Co się sprawdziło w procesie decyzyjnym, co byśmy zrobili inaczej. Wymagane.]

## Powiązane

- [ADR-NNN: tytuł, relacja]
- [skill-X: nazwa, relacja]
- [link do research / rozmowy / issue]

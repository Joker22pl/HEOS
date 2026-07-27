---
type: adr
id: adr-003
name: 003-konwencja-commitow-po-polsku
title: Konwencja commitów — `[tag] opis` po polsku
adr_number: 3
status: accepted
owner: gaja
created_at: '2026-07-23'
updated_at: '2026-07-24'
review_due: '2027-01-23'
version: 1.0.0
heos_standard_version: '1.2'
tags:
- cross-cutting
related:
- adr-001
- adr-002
- adr-004
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---# ADR-003: Konwencja commitów — `[tag] opis` po polsku

| Pole | Wartość |
|---|---|
| **Status** | Accepted |
| **Data** | 2026-07-23 |
| **Autor** | Gaja (za zgodą Jokera) |
| **Dotyczy domeny** | cross-cutting (Git workflow) |

## Kontekst

Wiele projektów, wiele commitów, brak standaryzacji = chaos w `git log`. Trzeba ustalić konwencję commit messages, która:

- jest wystarczająco sztywna, by dało się filtrować log
- jest wystarczająco luźna, by nie bolało pisać
- wspiera polski (bo Joker i Gaja pracują po polsku)

## Decyzja

Format: **`[tag] krótki opis po polsku`** z kanonem 7 tagów:

| Tag | Znaczenie | Przykład |
|---|---|---|
| `[init]` | pierwszy commit szkieletu projektu | `[init] szkielet projektu` |
| `[add]` | dodanie nowej funkcjonalności / pliku | `[add] obsługa czujnika PIR` |
| `[fix]` | naprawa bugu | `[fix] OLED init dla SSD1306` |
| `[doc]` | tylko dokumentacja | `[doc] opis pinów w README` |
| `[refactor]` | zmiana struktury bez zmiany zachowania | `[refactor] wydzielam main.py od konfiguracji` |
| `[test]` | dodanie/zmiana testów | `[test] test parsowania konfiguracji pinów` |
| `[chore]` | maintenance (deps, tooling, .gitignore) | `[chore] bump ruff do 0.6` |

## Uzasadnienie

- **Filtr w `git log`:** `git log --grep="^\[fix\]"` daje wszystkie bugfixy
- **Czytelność:** tag w pierwszych 6 znakach wystarczy do ogarnięcia co commit robi
- **Spójność:** ten sam kanon w każdym repo (zasada w `WORKFLOW.md` huba)
- **Polski:** Joker mówi po polsku, pracuje po polsku — commit messages też mogą być (chyba że projekt jest publiczny dla anglojęzycznych — wtedy wyjątek)

## Konsekwencje

**Pozytywne:**
- Łatwe `git log --grep` do audytu zmian
- Widoczny typ zmiany bez czytania treści
- Spójność między projektami

**Negatywne / ryzyka:**
- Anglojęzyczny kontrybutor nie zrozumie — ale Joker pracuje solo, więc nieistotne
- Nie mieści Conventional Commits (semver + breaking changes) — ale to nie jest problem dla projektów solo

## Rozważane alternatywy

- **Conventional Commits (`feat:`, `fix:`, `BREAKING CHANGE:`)** — odrzucone: zbyt rozbudowane na solo projekty
- **Brak konwencji** — odrzucone: po 100 commitach nie da się filtrować
- **Po angielsku** — odrzucone: zwiększa koszt pisania, brak wartości dla solo developera

## Kiedy rewizja

- Gdy do projektu dołączy drugi kontrybutor → rozważyć angielski + Conventional Commits
- Gdy projekt wejdzie do fazy release management → dorzucić semver

## Lessons Learned

- **Polski w commitach działa** dla solo developera. Gdyby doszli inni kontrybutorzy, rozważ angielski.
- **Kanon 7 tagów wystarczy** — nie wymyślaj nowych tagów na siłę. `[chore]` dla wszystkiego co nie pasuje.
- **Format `[tag] opis` parsowalny przez `git log --grep="^\[fix\]"`** — przydatne do audytu zmian.
- **Format v1.0 działa, ale to nie Conventional Commits** — brak semver + breaking changes. Wystarczające dla solowych projektów, niewystarczające dla release managementu.
## Powiązane

- ADR-002 (hub repo)
- ADR-004 (cookiecutter template — wbudowuje tę konwencję w szablon)

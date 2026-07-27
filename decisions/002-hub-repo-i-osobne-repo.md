---
type: adr
id: adr-002
name: 002-hub-repo-i-osobne-repo
title: Hub repo `gaja-projekty` + osobne repo per projekt
adr_number: 2
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
- skill-nightly-evolution
- adr-004
- adr-003
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---# ADR-002: Hub repo `gaja-projekty` + osobne repo per projekt

| Pole | Wartość |
|---|---|
| **Status** | Accepted |
| **Data** | 2026-07-23 |
| **Autor** | Gaja |
| **Dotyczy domeny** | cross-cutting (`03-quality` + GitHub) |

## Kontekst

Joker buduje wiele niezależnych projektów (roboty, eksperymenty, notatki). Potrzebujemy ustalić jak organizować repozytoria na GitHubie.

## Decyzja

- **Każdy projekt = osobne repo** na koncie `Joker22pl`
- **Centralny hub** = `gaja-projekty` (ten sam profil co inne) — trzyma spis + linki + statusy
- Domyślna gałąź: `main`
- Każde nowe repo: `README.md` + `.gitignore` + `LICENSE` (MIT domyślnie) + wpis w hubie

## Uzasadnienie

| Kryterium | Monorepo | Osobne repo + hub |
|---|---|---|
| Izolacja zależności | ✅ | ✅ |
| Koszt CI / clone | wysoki (duże repo) | niski |
| Uprawnienia per projekt | trudne (subfolder w monorepo) | naturalne (per-repo) |
| Współdzielenie kodu | łatwe (import wewnętrzny) | trudniejsze (template + copy) |
| Widoczność statusów | wymaga dashboardu | tabelka w README huba |
| Overhead administracyjny | niski (1 repo) | średni (N repo) |

Hibryda: **osobne repo dla izolacji + hub dla widoczności + cookiecutter template dla współdzielenia**. Łączy zalety obu podejść.

## Konsekwencje

**Pozytywne:**
- Prosta nawigacja między projektami
- Spis z statusami 🟢/🟡/🔴/⚪ w jednym miejscu
- Można zarchiwizować projekt bez wpływu na resztę
- Jasna odpowiedzialność: każde repo ma swojego "właściciela" (Gaja dla porządku)

**Negatywne / ryzyka:**
- Współdzielony kod → trzeba kopiować lub używać template (cookiecutter)
- Więcej pracy administracyjnej przy tworzeniu nowego projektu (template to amortyzuje)

## Rozważane alternatywy

- **Monorepo** (`joker-workspace`) — odrzucone: za mało wspólnego kodu, za dużo różnych języków/licencji
- **GitHub Projects jako hub** — odrzucone: brak możliwości czytania jako README, słaba discoverability
- **Wiki + repo per projekt** — odrzucone: wiki jest trudne do wersjonowania

## Kiedy rewizja

- Jeśli pojawi się projekt wymagający współdzielonych bibliotek z innym projektem → template + submoduły
- Jeśli liczba projektów > 20 → rozważyć narzędzie typu Backstage, GitHub Projects z automacją

## Lessons Learned

- **Hub + sub-repo to sweet spot** — nie monorepo (za ciężki), nie każdy projekt osobno bez śledzenia (chaos). Hub z tabelką + linkami + statusami daje widoczność bez coupling'u.
- **Konwencja commitów musi być w WORKFLOW.md** — w innym miejscu nikt nie sprawdzi.
- **Cookiecutter > ręczne kopiowanie** — template z pre-commit + .editorconfig + LICENSE eliminuje "zapomniałem dodać .gitignore" syndrome.
- **gitleaks w pre-commit blokuje wyciek PAT** — Joker miał nawyk wysyłania tokenów na Discorda. Bramka techniczna > apel do dyscypliny.
## Powiązane

- ADR-004 (cookiecutter template)
- ADR-003 (konwencja commitów)
- `templates/cookiecutter-gaja/` (szablon nowego projektu)

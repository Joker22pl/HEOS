---
type: adr
id: adr-004
name: 004-cookiecutter-i-pre-commit
title: Cookiecutter template + pre-commit hooks (ruff, gitleaks)
adr_number: 4
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
- adr-002
- adr-003
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---# ADR-004: Cookiecutter template + pre-commit hooks (ruff, gitleaks)

| Pole | Wartość |
|---|---|
| **Status** | Accepted |
| **Data** | 2026-07-23 |
| **Autor** | Gaja |
| **Dotyczy domeny** | `03-quality` + cross-cutting |

## Kontekst

Joker ma skłonność do wysyłania sekretów przez Discorda (PAT, hasła SSH, sudo) i kopiowania tego samego setupu do każdego nowego projektu. Potrzebujemy:

1. **Bariera dla wycieku sekretów** — coś, co zatrzyma wyciek zanim commit wyląduje na GitHubie
2. **Automatyzacja setupu** — nowe repo w 30 sekund, nie 30 minut

## Decyzja

- **Cookiecutter template** `templates/cookiecutter-gaja/` w hubie `gaja-projekty`
- **Pre-commit hooks** w każdym repo (Python): `ruff`, `ruff-format`, `gitleaks`, `codespell`, `trailing-whitespace`, `end-of-file-fixer`
- **`detect-secrets`** z baseline'em dla fałszywych alarmów

## Uzasadnienie

| Kryterium | Ręczne kopiowanie | Cookiecutter + pre-commit |
|---|---|---|
| Czas tworzenia nowego repo | 30-60 min (kopiowanie + ustawianie) | 30s (`cookiecutter …`) |
| Spójność między repo | niska (zapominanie o .gitignore) | wysoka (template wymusza) |
| Wyciek sekretów | zależy od dyscypliny | zablokowany przed commitem |
| Krzywa uczenia | niska (już wiadomo) | niska (jeden pipeline) |

**Kluczowe:** `gitleaks` blokuje commita jeśli wykryje pattern typu `ghp_*` (GitHub PAT), klucze SSH, AWS keys. Joker wysłał PAT 3× w jednej sesji — to **bariera techniczna** na powtórzenie, nie tylko apel do dyscypliny.

## Konsekwencje

**Pozytywne:**
- Nowe repo = `cookiecutter gh:Joker22pl/gaja-projekty` → gotowe
- Sekrety nie wyciekają przez przypadek (gitleaks)
- Spójny format kodu (ruff)
- Mniej decyzji do podjęcia przy starcie projektu

**Negatywne / ryzyka:**
- Pre-commit może irytować przy szybkich WIP commitach (workaround: `--no-verify`)
- False positives w gitleaks → baseline trzeba aktualizować
- Cookiecutter template trzeba utrzymywać (ale to jedno miejsce)

## Rozważane alternatywy

- **Tylko `pip install pre-commit`** (bez template) — odrzucone: nie rozwiązuje problemu "jak nowe repo"
- **GitHub Actions zamiast pre-commit** — odrzucone: blokuje **po** push, nie **przed** commitem
- **Własny skrypt bash** — odrzucone: nie wersjonowany, brak standaryzacji

## Kiedy rewizja

- Gdy pojawią się projekty nie-Python (czysty C++, firmware ESP-IDF) → inny template
- Gdy cookiecutter stanie się za ciężki → rozważyć `copier` (YAML/JSON, łatwiejszy w utrzymaniu)

## Lessons Learned

- **Cookiecutter z lokalnego katalogu** działa lepiej niż z GitHub URL (brak network dependency przy tworzeniu projektu).
- **`.pre-commit-config.yaml` w template** (nie w tutorialu) — nowy projekt ma gotową bramkę od razu.
- **ruff + ruff-format > black + flake8** — szybsze, jeden tool, mniej konfiguracji.
- **gitleaks musi być w pre-commit**, nie w CI — bo CI blokuje po push (za późno, secret jest w historii).
- **`.editorconfig` eliminuje "spaces vs tabs" w dyskusjach** — trywialna, ale irytująca bez niej.
## Powiązane

- ADR-002 (hub repo)
- ADR-003 (konwencja commitów — wbudowana w template)
- Memory note: "Joker wysyła sekrety przez Discorda — refused standardowo"

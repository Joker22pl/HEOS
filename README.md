# HEOS — Hermes Engineering Operating System

**Wersja HEOS:** v1.2.1
**Status:** 📊 patrz `STATUS.md` (auto-generowany)
**CI:** [![HEOS lint](https://github.com/Joker22pl/HEOS/actions/workflows/lint.yml/badge.svg)](https://github.com/Joker22pl/HEOS/actions/workflows/lint.yml)

System standardów, procedur, ADR i Skills dla Hermesa. Repozytorium: `Joker22pl/HEOS` (osobne repo od 2026-07-27, branch `main`).

## Punkt wejścia

- **Konstytucja:** [CONSTITUTION.md](CONSTITUTION.md) — jedyne źródło zasad
- **Architektura:** [ARCHITECTURE.md](ARCHITECTURE.md) — struktura systemu
- **Status:** [STATUS.md](STATUS.md) — auto-generowany snapshot stanu
- **Registry:** [.registry.yaml](.registry.yaml) — auto-generowany indeks artefaktów

## Struktura

```
HEOS/
├── CONSTITUTION.md    ← jedyne źródło zasad
├── ARCHITECTURE.md    ← architektura techniczna
├── STATUS.md          ← auto-generowany, snapshot
├── README.md          ← ten plik
│
├── skills/            ← wszystkie Skillsy (płasko, 5 typów)
├── decisions/         ← ADR (płasko, NNN-tytuł.md)
├── lessons/           ← Lessons Learned
├── checklists/        ← Checklisty
├── playbooks/         ← Playbooki
│
├── templates/         ← 5 szablonów (skill, adr, lessons, checklist, playbook)
├── tools/             ← narzędzia (audyt, lint, generacja, migracja)
│
├── heos-migration/    ← infrastruktura migracji (snapshot plan, rollback)
└── archive/           ← snapshot v1.1 (nieaktywny)
```

## Artefakty (9 aktywnych)

| Typ | Liczba | Lokalizacja |
|---|---|---|
| Skills | 4 (2 HEOS + 2 runtime Hermes) | `skills/` |
| ADR | 5 | `decisions/` |

Pełna lista w `.registry.yaml`.

## Narzędzia (`tools/`)

| Narzędzie | Opis |
|---|---|
| `skill_audit.py` | Walidator 3-poziomowy (Schema/Technical/Operational) |
| `heos_lint.py` | Walidator cross-references, metadanych, spójności |
| `generate_registry.py` | Generuje `.registry.yaml` |
| `generate_status.py` | Generuje `STATUS.md` |
| `lifecycle_audit.py` | Audyt review_due, deprecated |
| `heos_migrate.py` | Migracja v1.1→v1.2 (plan/dry-run/rollback) |
| `update_frontmatter.py` | Aktualizuje frontmatter dla migracji |
| `migrate_files.py` | Wykonuje git mv z mapy migracji |
| `test_heos_lint.py`, `test_generate_registry.py` | Testy jednostkowe |

## Migracja (informacja)

HEOS był migrowany z v1.1 do v1.2 dnia 2026-07-24. Plan w `heos-migration/plan.md`, mapa w `heos-migration/migration-map.json`, rollback w `heos-migration/rollback.sh`. Backup v1.1 w `~/hermes-backups/heos-pre-v1.2-*.tar.gz`. Git tag `v1.1.0-pre-migration` (punkt powrotu).

## Decision Records (5 aktywnych)

| ID | Tytuł | Status |
|---|---|---|
| [adr-001](decisions/001-micropython-esp32-s3-pico.md) | MicroPython + mpremote dla ESP32-S3-PICO | Accepted |
| [adr-002](decisions/002-hub-repo-i-osobne-repo.md) | Hub repo + osobne repo per projekt | Accepted |
| [adr-003](decisions/003-konwencja-commitow-po-polsku.md) | Konwencja commitów `[tag] opis` po polsku | Accepted |
| [adr-004](decisions/004-cookiecutter-i-pre-commit.md) | Cookiecutter template + pre-commit hooks | Accepted |
| [adr-005](decisions/005-granice-profili-hermes.md) | Granice profili Hermes (gaja / gaja-it / gaja-med) | Accepted |

## Otwarte decyzje architektoniczne (ODA)

Wszystkie 10 ODA z v1.1 zostały **rozwiązane** w propozycji v1.2. Nowe ODA pojawią się w `decisions/`.

## Cron jobs

- **HEOS Weekly Audit** — co poniedziałek 9:00 UTC, generuje raport + STATUS.md + audyt lifecycle, dostarcza do tego wątku.

## Granice HEOS

- **HEOS = standardy, szablony, audytory, wzorce, registry.** NIE jest systemem zarządzania projektami, hostingiem kodu, CI/CD.
- **Profile Hermesa** (gaja, gaja-it, gaja-med) mają własne runtime Skills. HEOS nie migruje 87 Skills profilu — dostarcza standardy.
- **Projekty Jokera** (np. robot-1) żyją w osobnych repo `Joker22pl/<projekt>`. HEOS nie jest ich częścią.

## Workflow dla nowego artefaktu

1. Sprawdź czy już istnieje w `.registry.yaml`
2. Wybierz typ (skill/adr/lessons/checklist/playbook)
3. Skopiuj z `templates/<typ>.md`
4. Uzupełnij wymagane pola (12 wspólnych + specyficzne dla typu)
5. Sprawdź: `python3 tools/skill_audit.py <plik>` — musi ✅ PASS
6. Sprawdź cross-refs: `python3 tools/heos_lint.py`
7. Commit + push
8. (Opcjonalnie) Regeneruj `.registry.yaml` i `STATUS.md` ręcznie:
   ```bash
   python3 HEOS/tools/generate_registry.py
   python3 HEOS/tools/generate_status.py
   ```
   Lub poczekaj na cotygodniowy cron (poniedziałek 9:00 UTC)

## Wersjonowanie

HEOS używa SemVer: `<major>.<minor>.<patch>`. Wersja w `STATUS.md` (auto-generowana) + w `CONSTITUTION.md` (ręcznie). Tag git: `v<major>.<minor>.<patch>`.

| Wersja | Data | Zmiana |
|---|---|---|
| 1.0 | 2026-07-23 | Pierwsza wersja (manuskrypt) |
| 1.1 | 2026-07-23 | 5 ADR, skill_audit, baseline |
| 1.2 | 2026-07-24 | Architektura 2D, STATUS.md, registry, 3-poziomowa ocena, 6-etapowy lifecycle |

## Powiązane

- `~/.hermes/profiles/gaja/skills/` — runtime Skills (nie HEOS)
- `Joker22pl/gaja-projekty` — repo (gdzie żyje HEOS)
- `HEOS-v1.2-STAGE1-PLAN-v2.md` (w `~/.hermes/profiles/gaja/cache/`) — plan Etapu 1 v1.2
- `HEOS-v1.2-PROPOSAL.md` (w cache) — propozycja v1.2 (10 zmian)

---

_Last updated: 2026-07-24_

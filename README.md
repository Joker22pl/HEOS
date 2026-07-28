# HEOS — Hermes Engineering Operating System

**Wersja HEOS:** v1.5.4
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

## Artefakty (20 aktywnych)

| Typ | Liczba | Lokalizacja |
|---|---|---|
| Skills | 7 (5 HEOS cross-cutting + 2 runtime Hermes) | `skills/` |
| ADR | 10 | `decisions/` |
| Lessons Learned | 1 | `lessons/` |
| Checklisty | 1 | `checklists/` |
| Playbooki | 1 | `playbooks/` |

Pełna lista w `.registry.yaml` (auto-generowany). Status bieżący w `STATUS.md`.

## Narzędzia (`tools/`)

| Narzędzie | Opis |
|---|---|
| `skill_audit.py` | Walidator 3-poziomowy (Schema/Technical/Operational) |
| `heos_lint.py` | Walidator cross-references, metadanych, spójności |
| `check_related_symmetry.py` | Wykrywa + naprawia asymetrię cross-refs (per ADR-009) |
| `check_operational_proven.py` | Operational Evidence Model — waliduje runtime usage (per ADR-007) |
| `_heos_atomic.py` | Biblioteka atomic write (per ADR-008) |
| `generate_registry.py` | Generuje `.registry.yaml` |
| `generate_status.py` | Generuje `STATUS.md` |
| `lifecycle_audit.py` | Audyt `review_due`, `deprecated` |
| `update_frontmatter.py` | Aktualizuje frontmatter (migracja) |
| `update_quality.py` | Aktualizuje `quality_schema/technical` (atomic write per ADR-008) |
| `weekly_report.py` | Raport tygodniowy (cron poniedziałek 9:00 UTC) |
| `add_lessons_learned.py` | Dodaje nowy wpis Lessons Learned |
| `heos_migrate.py` | Migracja v1.1→v1.2 (plan/dry-run/rollback) |
| `migrate_files.py` | Wykonuje git mv z mapy migracji |
| `migrate_runtime_skills.py` | Migracja skilli runtime do HEOS |
| `validate_symlinks.py` | Waliduje mosty HEOS → profil Hermesa |
| `test_*.py` (7 plików) | Testy jednostkowe (60 testów PASS) |

## Migracja (informacja)

HEOS był migrowany z v1.1 do v1.2 dnia 2026-07-24. Plan w `heos-migration/plan.md`, mapa w `heos-migration/migration-map.json`, rollback w `heos-migration/rollback.sh`. Backup v1.1 w `~/hermes-backups/heos-pre-v1.2-*.tar.gz`. Git tag `v1.1.0-pre-migration` (punkt powrotu).

## Decision Records (11 aktywnych)

| ID | Tytuł | Status |
|---|---|---|
| [adr-001](decisions/001-micropython-esp32-s3-pico.md) | MicroPython + mpremote dla ESP32-S3-PICO | Accepted |
| [adr-002](decisions/002-hub-repo-i-osobne-repo.md) | Hub repo + osobne repo per projekt | Accepted |
| [adr-003](decisions/003-konwencja-commitow-po-polsku.md) | Konwencja commitów `[tag] opis` po polsku | Accepted |
| [adr-004](decisions/004-cookiecutter-i-pre-commit.md) | Cookiecutter template + pre-commit hooks | Accepted |
| [adr-005](decisions/005-granice-profili-hermes.md) | Granice profili Hermes (gaja / gaja-it / gaja-med) | Accepted |
| [adr-006](decisions/006-skills-format-policy.md) | Polityka formatu Skills — kiedy `.md` vs katalog | Accepted |
| [adr-007](decisions/007-operational-evidence-model.md) | Operational Evidence Model dla skilli HEOS | Accepted |
| [adr-008](decisions/008-atomic-write-contract.md) | Atomic Write Contract dla narzędzi modyfikujących HEOS | Accepted |
| [adr-009](decisions/009-heos-v1-4-scope.md) | HEOS v1.4 scope deklaracja (split nightly-evolution + CHANGELOG) | Accepted |
| [adr-010](decisions/010-heos-v1-5-scope.md) | HEOS v1.5 scope deklaracja (output-templates split + STATUS regen) | Accepted |
| [adr-011](decisions/011-private-repo-by-default.md) | Repozytoria Joker22pl/* domyślnie prywatne | Accepted |

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
3. Skopiuj z `templates/<typ>.md.template`
4. Uzupełnij wymagane pola (12 wspólnych + specyficzne dla typu)
5. Sprawdź: `python3 tools/skill_audit.py <plik>` — musi ✅ PASS
6. Sprawdź cross-refs: `python3 tools/heos_lint.py`
7. Sprawdź related symmetry: `python3 tools/check_related_symmetry.py` (per ADR-009)
8. Commit + push do `Joker22pl/HEOS`
9. (Opcjonalnie) Regeneruj `.registry.yaml` i `STATUS.md`:
   ```bash
   python3 tools/generate_registry.py
   python3 tools/generate_status.py
   ```
   Lub poczekaj na cotygodniowy cron (poniedziałek 9:00 UTC)

## Wersjonowanie

HEOS używa SemVer: `<major>.<minor>.<patch>`. Wersja w `STATUS.md` (auto-generowana) + w `CONSTITUTION.md` (ręcznie). Tag git: `v<major>.<minor>.<patch>`.

| Wersja | Data | Zmiana |
|---|---|---|
| 1.0 | 2026-07-23 | Pierwsza wersja (manuskrypt) |
| 1.1 | 2026-07-23 | 5 ADR, skill_audit, baseline |
| 1.2 | 2026-07-24 | Architektura 2D, STATUS.md, registry, 3-poziomowa ocena, 6-etapowy lifecycle |
| 1.3 | 2026-07-27 | ADR-007 (Operational Evidence), ADR-008 (Atomic Write), `check_operational_proven.py`, `_heos_atomic.py`, GitHub Actions CI, push do `Joker22pl/HEOS` |
| 1.3.1 | 2026-07-28 | Wspólny atomic helper, refactor 4 narzędzi na `atomic_write` + `transaction()`, fix silent YAML corruption w `update_quality.py`, ADR-006 (skills format policy) |
| 1.3.2 | 2026-07-28 | housekeeping — STATUS regen + sync wersji README/CONSTITUTION/ARCHITECTURE |
| 1.4.0 | 2026-07-28 | ADR-009 (v1.4 scope); nightly-evolution split 957 → 498 linii + 3 `references/` (per ADR-006); CHANGELOG.md (audyt historii); push do GitHub |
| 1.4.1 | 2026-07-28 | Patch — brak migracji |
| 1.4.2 | 2026-07-28 | Patch — pełna historia wersji w CHANGELOG.md |
| 1.5.0 | 2026-07-28 | ADR-010 (v1.5 scope); nightly-evolution split Kroki 4-12 → `output-templates.md` (~70% redukcja kontekstu); STATUS regen (20 artefaktów) |
| 1.5.1 | 2026-07-28 | Patch — ADR-010 + reverse-refs |
| 1.5.2 | 2026-07-28 | Patch — CONSTITUTION/ARCHITECTURE sync do v1.5.2 (drift fix) |
| 1.5.3 | 2026-07-28 | Patch — `.bak` cleanup + STATUS regen |
| 1.5.4 | 2026-07-28 | Patch — `generate_status.py` fix (Tools: 25→24 real) + 5 testów |
| 1.6.0 | 2026-07-28 | **ADR-011** (private repo by default) + `tools/repo_visibility.py` (audyt + zmiana widoczności) |

## Nowe repozytorium (workflow)

Per **ADR-011** wszystkie nowe repo Joker22pl/* są domyślnie prywatne. Wyjątek (np. HEOS sam jako dokumentacja dla społeczności Hermes Agent) wymaga świadomej zgody w brief.

```bash
# 1. Utwórz repo na github.com (UI) — domyślnie prywatne
# 2. Bootstrap z HEOS jako remote:
cd ~/gaja-projekty/<nowy-projekt>
git init && git add -A && git commit -m "[init] bootstrap <projekt>"
git remote add origin git@github.com:Joker22pl/<projekt>.git
git push -u origin main
```

### Audyt widoczności istniejących repo

```bash
python3 tools/repo_visibility.py --audit
```

### Zmiana widoczności na private (jednorazowa akcja Jokera)

Wymaga GitHub PAT z scope `repo`:

```bash
export GITHUB_TOKEN=ghp_...
python3 tools/repo_visibility.py --make-private --all --yes
```

Output: każde repo zmienione z public → private z audit trail.

## Powiązane

- `~/.hermes/profiles/gaja/skills/` — runtime Skills (nie HEOS)
- `Joker22pl/HEOS` — repo (osobne od 2026-07-27)
- `CONSTITUTION.md` — jedyne źródło zasad (v1.5.2)
- `ARCHITECTURE.md` — architektura techniczna (v1.5.2)
- `CHANGELOG.md` — pełna historia wersji (v1.0 → v1.5.5)
- `STATUS.md` — auto-generowany snapshot stanu (realna wersja zawsze tu)
- Raport specjalisty 2026-07-27 (P0/P1/P2 lista) — napędził rozwój v1.3 → v1.5

---

_Last updated: 2026-07-28_

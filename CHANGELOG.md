# HEOS — CHANGELOG

Pełna historia wersji HEOS. Format inspirowany [Keep a Changelog](https://keepachangelog.com/).

> **Konwencja:**
> - **Added** — nowe funkcje.
> - **Changed** — zmiany w istniejących funkcjach.
> - **Deprecated** — funkcje które wkrótce znikną.
> - **Removed** — funkcje usunięte.
> - **Fixed** — bugfixy.
> - **Security** — poprawki bezpieczeństwa.
>
> Wersje: [SemVer](https://semver.org/) `<major>.<minor>.<patch>`. Tagi git: `v<major>.<minor>.<patch>`.

---

## [v1.5.1] — 2026-07-28

### Added
- **ADR-010 — HEOS v1.5 scope deklaracja** (`decisions/010-heos-v1-5-scope.md`)
  - Anty-scope-creep continuation po ADR-009.
  - 2 cele v1.5: (1) split output-templates + (2) STATUS regen.
  - Zamknięcie backlogu: "dalsze splity nightly-evolution NIE w v1.5 (sweet spot na ~291 linii)".
  - Komit: `61826f4`.

### Changed
- **`STATUS.md`** — re-generacja po dodaniu ADR-008/009/010:
  - Artefakty: 17 → **20** (10 ADR + 7 skill + 1 lessons + 1 checklist + 1 playbook).
  - Komit: `61826f4`.

## [v1.5.0] — 2026-07-28

### Changed
- **`skills/nightly-evolution/SKILL.md` (498 linii) → 291 linii + nowy `references/output-templates.md` (245 linii)**
  - Kroki 4-12 (Etapy B-J: Daily Retrospective, Lessons Learned, Self Review, Doc Health, Arch Review, Error Intelligence, Performance Report, Improvement Backlog, Plan na jutro) — wszystkie template'y markdown wycięte do reference.
  - Struktura pliku (4 references): etap-K + etap-L + **output-templates (nowy)** + alerts-and-examples.
  - **Korzyść:** ~42% dalsza redukcja głównego SKILL.md. Sumarycznie z v1.4 split: 957 linii flat → 291 linii overview (~70% mniej).
  - Frontmatter nightly-evolution: wersja 1.4.0 → 1.5.0.
  - Komit: `b5de350`.

## [v1.4.2] — 2026-07-28

### Added
- **`CHANGELOG.md`** — audyt pełnej historii wersji HEOS (v1.0 → v1.4.1).
  - Format inspirowany Keep a Changelog (Added/Changed/Deprecated/Removed/Fixed/Security).
  - Sekcje: legenda SemVer + tagi + commity + bramki CI, tabela migracji między wersjami, linki.
  - Komit: `ee8b19f`.

## [v1.4.1] — 2026-07-28

### Changed
- **`skills/nightly-evolution` (957 linii) → `skills/nightly-evolution/SKILL.md` (498 linii) + 3 `references/`**
  - Struktura katalogu per ADR-006 (skills format policy: ma references → katalog).
  - `references/etap-K-knowledge-routing.md` (113 linii) — Krok 5.5.
  - `references/etap-L-memory-hygiene.md` (153 linii) — Krok 5.6 + 5.6b.
  - `references/alerts-and-examples.md` (239 linii) — Kroki 14a/14b + Przykłady + Typowe błędy + Checklisty + Bezpieczeństwo.
  - **Korzyść:** ~50% redukcja kontekstu przy ładowaniu głównego SKILL.md (~3.5K tokenów → ~1.7K tokenów). References ładowane tylko w odpowiednich krokach.
  - Komit: `ce08d24`.

## [v1.4.0] — 2026-07-28

### Added
- **ADR-006 — Polityka formatu skilli** (`decisions/006-skills-format-policy.md`)
  - Reguła: `<200 linii` + brak references/scripts → `skills/<name>.md` (flat); `≥200 linii` lub ma references/scripts → `skills/<name>/SKILL.md` (katalog).
  - Loader Hermesa akceptuje oba formaty (CP #23).
  - Komit: `8cda935`.
- **ADR-007 — Operational Evidence Model** (`decisions/007-operational-evidence-model.md`)
  - Lifecycle `unmeasured → candidate → proven → stale → failed`.
  - Tool `tools/check_operational_proven.py` (215 linii, 16 testów) waliduje runtime usage.
  - Komit: `c582ac5`.
- **ADR-008 — Atomic Write Contract** (`decisions/008-atomic-write-contract.md`)
  - Wspólna biblioteka `tools/_heos_atomic.py` (195 linii).
  - Helpery: `atomic_write`, `atomic_write_bytes`, `transaction` (context manager z rollback), `cleanup_old_backups`.
  - Komit: `321bc31`.
- **ADR-009 — HEOS v1.4 scope deklaracja** (`decisions/009-heos-v1-4-scope.md`)
  - Formalna granica: v1.4 = (split nightly-evolution) + (CHANGELOG), reszta odłożona do v1.5+.
  - Anty-scope-creep: deploy manifest, multi-profile, knowledge graph, heos_core/ biblioteka → v1.5+.
  - Komit: `595642e`.
- **Push HEOS do GitHuba** — `Joker22pl/HEOS` (public, branch `main`).
  - Tagi: v1.2.0 → v1.3.1 (6 commitów).
  - CI: GitHub Actions `.github/workflows/lint.yml` (68 linii, 7 kroków).
  - Komity: `321bc31`, `c582ac5`, `fa42981`, `c150700`, `af6ae85`.

### Changed
- **`tools/update_quality.py`** — przepisane na `atomic_write` + `transaction()` z rollbackiem. Eliminuje P0-3 (non-atomic write) + P0-4 (brak transakcyjności).
  - Komity: `fa42981` (silent corruption fix), `321bc31` (atomic helper).
- **6 narzędzi HEOS** zrefactorowane na `atomic_write`:
  - `update_quality.py`, `check_related_symmetry.py`, `add_lessons_learned.py`, `update_frontmatter.py`, `migrate_runtime_skills.py`, `heos_lint.py` (read-only — bez potrzeby).
- **Testy narzędzi** — 18 → **60 testów** PASS (3.3× wzrost):
  - +11 atomic (`test_heos_atomic.py`)
  - +16 operational (`test_check_operational_proven.py`)
  - +13 update_quality (`test_update_quality.py`)
  - istniejące: `test_generate_registry.py` (5), `test_heos_lint.py` (8), `test_weekly_report.py` (7).

### Fixed
- **`update_quality.py` silent corruption** — `_ustaw_quality` pisał `------\n` zamiast `---\n` w frontmatter (5 plików dotkniętych).
  - Komit: `fa42981`.
- **`skill_audit.py` catch-all** — łapał pliki spoza scope (np. `joker-deliverables/`); dodano `is_not_skill` flag i rozszerzono whitelist.
  - Komit: `f76fb43` (w sesji 2026-07-27, ale relevant dla v1.4).

## [v1.3.0] — 2026-07-27

### Added
- **Strona repo `Joker22pl/HEOS`** (osobne od monorepo `gaja-projekty`).
- **3 nowe pliki: lessons/ + checklists/ + playbooks/** (z 1 przykładem każdy, po raporcie specjalisty § 6).
  - `lessons/2026-07-27-heos-audit-fix-bug.md`
  - `checklists/heos-pre-commit-validation.md`
  - `playbooks/heos-new-skill.md`
- **3 nowe narzędzia:**
  - `tools/update_quality.py` — aktualizuje `quality_schema`/`quality_technical` na podstawie audytu.
  - `tools/check_related_symmetry.py` — wykrywa + naprawia asymetrię cross-refs.
  - `tools/validate_symlinks.py` — sprawdza mosty HEOS → profil Hermesa.
- **1 refactor:**
  - `skills/memory-hygiene.md` (674 linii + references) → `skills/memory-hygiene/SKILL.md` (674 linii) + `references/race-condition-signs.md`.

## [v1.2.0] — 2026-07-24

### Added
- **Architektura 2D** — `00-foundation/` + `01-domains/` + `02-artifacts/` (skills, adr, lessons, checklists, playbooks).
- **STATUS.md** (auto-generowany, snapshot stanu).
- **`.registry.yaml`** (auto-generowany indeks artefaktów + inverse_index).
- **3-poziomowa ocena** — Schema (7 obowiązkowych + 8 opcjonalnych pól) + Technical (code blocks, sekcje) + Operational (fresh/stale/unmeasured).
- **6-etapowy lifecycle** — draft → proposed → reviewed → accepted → deprecated → archived.
- **Migracja z v1.1 → v1.2** (commit `00f1329`, 2026-07-24):
  - 5 ADR przeniesionych z `00-foundation/decision-records/` do `decisions/`.
  - Skille przeniesione z `01-domains/*/skills/` do `skills/`.
  - Backup: `~/hermes-backups/heos-pre-v1.2-*.tar.gz`.
  - Tag `v1.1.0-pre-migration` (rollback point).

## [v1.1] — 2026-07-23

> **Uwaga:** ta wersja istniała w monorepo `gaja-projekty` (nie w osobnym `Joker22pl/HEOS`). Pełna historia w `archive/00-HEOS-CHANGELOG-v1.1.md` (326 linii, 13.7 KB).

### Added (skrót, 9 zmian)
- **Warstwa Enforcement** — automatyczne bramki (pre-commit + CI + weekly cron). Szczegóły w archiwum Zmiana #1.
- **Architektura dwuwymiarowa** — katalogi `00-foundation/`, `01-domains/`, `02-artifacts/`, `03-quality/`. Szczegóły Zmiana #2.
- **Standaryzacja Skilli** — 15-punktowy szablon (12 pól frontmatter + 3 sekcje obowiązkowe). Szczegóły Zmiana #4.
- **Lifecycle 6-etapowy** — `draft → proposed → reviewed → accepted → deprecated → archived`. Szczegóły Zmiana #5.
- **Self-review w nightly-evolution** — krok 0.5 (skill self-check) zapobiega cichym awariom. Szczegóły Zmiana #7.
- **Pierwszy skill HEOS** — `nightly-evolution.md` (240 linii).
- **Cron HEOS Weekly Audit** — co poniedziałek 9:00 UTC, generuje raport + STATUS.md + lifecycle audit.

### Changed
- Wszystkie 87 skillów profilu `gaja` zaudytowane: 0/87 PASS → baseline 0% (motywacja do v1.1).

## [v1.0] — 2026-07-23

### Added (pierwsza wersja, manuskrypt)
- **Konstytucja HEOS** — 31 zasad, 5 ról, 7 trybów, 15-punktowy szablon Skilla, 7 modułów.
- **HEOS Master Prompt** (`archive/HEOS-MASTER-PROMPT-v1.0.docx`) — manifest wartości.
- **5 ADR** (status: accepted):
  - ADR-001 — MicroPython + mpremote dla ESP32-S3-PICO
  - ADR-002 — Hub repo + osobne repo per projekt
  - ADR-003 — Konwencja commitów `[tag] opis` po polsku
  - ADR-004 — Cookiecutter template + pre-commit hooks (ruff, gitleaks)
  - ADR-005 — Granice profili Hermes (gaja / gaja-it / gaja-med)

### Known Limitations
- **Zero enforcement** — manifest wartości bez mechanizmu sprawdzającego.
- **Płaska architektura** — `00-constitution`, `01-engineering`, ..., `07-knowledge` (numeryczna hierarchia).
- **Brak lifecycle** — brak statusów dla artefaktów.
- **Brak STATUS.md** — brak snapshotu stanu.

---

## Legenda

- **Wersja SemVer:**
  - **major** (X.0.0) — breaking change w API/architekturze HEOS.
  - **minor** (0.X.0) — nowe funkcje (ADR, narzędzia, skille) bez breakage.
  - **patch** (0.0.X) — bugfixy, drobne ulepszenia, housekeeping.
- **Tagi git:** `v<major>.<minor>.<patch>` (z literą `v`).
- **Commity:** format `[tag] opis` po polsku (per ADR-003), np. `[adr] ADR-009 — scope deklaracja v1.4`.
- **Bramki (CI):** skill_audit, heos_lint, lifecycle_audit, pytest, check_related_symmetry, update_quality (idempotent).

## Migracje między wersjami

| Z | Do | Akcja |
|---|---|---|
| v1.4.0 | v1.4.1 | Nic — patch. |
| v1.3.x | v1.4.0 | Tag wskazuje na commit `595642e` (ADR-009). Brak migracji kodu. |
| v1.2.x | v1.3.0 | Skille płaskie `*.md` mogą zostać (backward compat), ale nowe ≥200 linii idą do katalogu. |
| v1.1.x | v1.2.0 | Użyj `tools/heos_migrate.py --plan` + `--execute` (z backupem). |
| v1.0.x | v1.1.0 | Ręczna migracja (brak narzędzia). Backup: `~/hermes-backups/heos-pre-v1.2-*.tar.gz`. |

## Linki

- **Repo:** https://github.com/Joker22pl/HEOS
- **CI:** https://github.com/Joker22pl/HEOS/actions/workflows/lint.yml
- **CONSTITUTION.md** — aktualne zasady (nie zmienione od v1.2).
- **ARCHITECTURE.md** — aktualna architektura.
- **STATUS.md** — auto-generowany snapshot stanu.
- **Raport specjalisty 2026-07-27** (P0/P1/P2 lista) — napędził rozwój v1.3 → v1.4.

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

## [v1.6.14] — 2026-08-01

### Fixed
- **P0.1 — `skill_audit.py` nie mógł się sam siebie audytować** (audyt HEOS 2026-08-01):
  - Domyślna ścieżka `~/.hermes/profiles/gaja/skills` powodowała "Katalog nie istnieje" pod Hermes profile (gdzie `$HOME=/home/gaja/.hermes/profiles/<name>/home`).
  - Patch: default → absolutna ścieżka `/home/gaja/.hermes/profiles/gaja/skills`. Własny audytor HEOS od teraz działa z `--quiet` bez argumentów.
  - `tools/test_skill_audit_default_path.py` — 4 testy regresji (default path is absolute, exists, no "Katalog nie istnieje", ≥1 skill found).
- **P0.2 — wersja HEOS dryfowała w 4 plikach** (CONSTITUTION=v1.5.2, README=v1.5.4, ARCHITECTURE=v1.5.2, STATUS=v1.6.13):
  - Single Source of Truth (P3 §CONSTITUTION 10) złamany.
  - `tools/sync_versions.py` — STATUS jest truth, CONSTITUTION/README/ARCHITECTURE są mirrorowane. Tryby `--check` (CI), `--sync` (naprawa), `--show` (diagnostyka). Atomic write per ADR-008.
  - `tools/test_sync_versions.py` — 5 testów regresji (drift detection, sync repair, atomic write no corruption, status has version, initial sync runs).
  - Po `--sync` wszystkie 4 pliki zsynchronizowane do v1.6.13.
- **P1.1 — README dryfowało z registry**:
  - README ręcznie mówiło "Skills 7, ADR 10, Artefakty 20" — registry ma 8/11/22.
  - `tools/generate_readme.py` — czyta `.registry.yaml`, generuje prawidłowe tabele + synchronizuje wersję z STATUS. Tryby `--check` (signals-based, ignoruje kosmetykę tytułów ADR) i `--sync` (atomic write per ADR-008).
  - `tools/test_generate_readme.py` — 7 testów (drift signals, normalize version, count updates, --check exit codes, drift detection).
- **P2.1 — 2 skille miały `quality_operational: candidate` bez runtime evidence**:
  - `embedded-communications-debug` i `memory-hygiene` — brak wpisu w `~/.hermes/skills/.usage.json`, więc rekomendacja to `unmeasured`.
  - Frontmatter → `quality_operational: unmeasured` zgodnie z `check_operational_proven.py`.
- **Test regresji — `test_rollout_gates.py::test_current_repository_version_is_latest_semver_tag`**:
  - Hardcoded `assert == "v1.6.13"` pękł przy każdym nowym tagu.
  - Naprawa: dynamiczna wartość oczekiwana = `max(tags, key=semver_key)`.

### Added
- **`tools/generate_readme.py`** — auto-regeneracja tabel artefaktów + Decision Records z `.registry.yaml`. STATUS-driven version sync. Single source of truth dla treści cytujących registry.
- **`tools/sync_versions.py`** — 3-mode version sync (--check/--sync/--show) z atomic write.
- **`tools/test_skill_audit_default_path.py`** — 4 nowe testy regresji (default path).
- **`tools/test_sync_versions.py`** — 5 nowych testów regresji (version sync).
- **`tools/test_generate_readme.py`** — 7 nowych testów regresji (README sync).
- **`lessons/2026-08-01-cross-profile-audit.md`** — Lessons Learned z cross-profile audit
  (HEOS + 5 profili: gaja, gaja-it, gaja-lab, gaja-med, gaja-robotics = 381 skilli).
  Findings: 11 mostów HEOS→profil, 370 unikalnych, 1 realny dryf (clarify-discord-fit
  w 4 profilach — starsza wersja sprzed augmentacji). ADR-005 (granice profili)
  respektowany: każdy profil ma unikalną pamięć (md5 różne). Rekomendacje P1-P3
  dla kolejnych iteracji (skill_audit --en-language, validate_symlinks subdirs).

### Changed
- **Suite testów**: 86 → **102** testów (+16 nowych). Czas: 1.1s → 4.6s.
- **Tools count**: 27 → 32 (nowe).

---

## [v1.6.0] — 2026-07-28

### Added
- **ADR-011 — Repozytoria Joker22pl/* domyślnie prywatne** (`decisions/011-private-repo-by-default.md`)
  - Polityka: nowe repo private domyślnie, świadomy override dla publicznych.
  - HEOS zostaje public (dokumentacja dla społeczności Hermes Agent) — explicite udokumentowane.
- **`tools/repo_visibility.py`** — audyt + zmiana widoczności istniejących repo
  - `--audit` (read-only, bez tokena): listuje aktualną widoczność 7 znanych repo
  - `--make-private --repo NAME` (wymaga `GITHUB_TOKEN` z scope `repo`)
  - `--make-private --all --yes` (jednorazowa akcja dla wszystkich 7)
  - Safety: bez `--yes` tylko raportuje co zrobi; bez tokena → exit 1 z komunikatem
- **`tools/test_repo_visibility.py`** — 11 testów (KNOWN_HEOS_REPOS, _api_request z/bez tokena, 404 handling, audit/make_private flow, exit codes)
- **README sekcja "Nowe repozytorium"** — workflow dla bootstrap + komendy audytu/zmiany widoczności

### Changed
- **README.md** — Decision Records: 10 → 11, dodany wiersz ADR-011
- **`decisions/009-heos-v1-4-scope.md`** — `related: +adr-011` (reverse-ref); przywrócone 3 wcześniej usunięte (adr-006/007/008) + skill-nightly-evolution po błędzie patch; usunięte błędne `adr-002`, `adr-005`, `adr-009` (self-ref) dodane przez mojego pomyłkowego patcha

### Backlog (TODO dla Jokera)
- **Jednorazowa akcja: zmiana widoczności 7 istniejących repo** (HEOS ma zostać public, 6 pozostałych — do decyzji Jokera):
  ```bash
  export GITHUB_TOKEN=ghp_...
  python3 tools/repo_visibility.py --make-private --all --yes
  ```
  Bez tokena nie zrobię — wymaga akcji Jokera (UI lub PAT).

---

## [v1.6.5] — 2026-07-29

### Fixed
- **Cross-refs cleanup po nightly-evolution v1.6.2** (`d1621df`, `f84dc3d`):
  - `decisions/011-private-repo-by-default.md` — reverse-ref do `skill-nightly-evolution` (bo nightly-evolution v1.6.3 dodał ADR-011 do related).
  - `decisions/006-skills-format-policy.md` — reverse-ref do `skill-nightly-evolution` (per format katalogowy opisany w ADR-006, nightly-evolution stosuje ten format).
  - `skills/nightly-evolution/SKILL.md` related — dodane `adr-006` (skills format policy, bo nightly-evolution jest w katalogu `SKILL.md + references/`).
  - **Weryfikacja:** `check_related_symmetry --dry-run: 0 asymetrii, exit 0`, CI green.

---

## [v1.6.3] — 2026-07-29

### Added
- **`skills/nightly-evolution/SKILL.md` — Krok 5.7 (Etap M: Runtime Health Check)** (`03c468d`)
  - Sprawdza 4 endpointy codziennie o 03:00: RPi `.178` (ping + ssh), NUC `.173:8766/healthz` (HTTP), router `.1` (ping kontrolny).
  - Sekcja `## Runtime Health` dodawana do daily report z PASS/FAIL dla każdego hosta.
  - Timeout 3-5s per host, non-blocking (+15s max do nightly run).
  - Failures NIE przerywają nightly run — tylko wpis w daily report.
  - Frontmatter: `version 1.5.0 → 1.6.2`, `related: +adr-011`.
  - Sekcja "Struktura pliku" zaktualizowana (Runtime Health inline w SKILL.md, nie w references/).
- **Korzyść:** wykrywanie downtime hostów zamiast 30h+ czekania do manual discovery. Smoke test wykazał: RPi `.178` ping fail + NUC `.173:8766/healthz` HTTP 000 (oba wykryte).

---

## [v1.6.12] — 2026-07-29

### Added
- **`skills/clarify-discord-fit/SKILL.md`** — nowy skill wymuszający Discord-fit format dla `clarify` tool:
  - `clarify` = pytanie + opcje, kontekst osobną wiadomością (Discord 2000 chars limit)
  - Severity emoji 🔴🟠🟡✅ standaryzowane
  - Max 4 opcje (Discord UI limit)
  - Pytanie max 100 chars, opcje max 40 chars
  - Montowany we wszystkich 5 profilach Hermes (gaja, gaja-it, gaja-lab, gaja-med, gaja-robotics) przez hardlink

### Fixed
- **`tools/test_weekly_report.py`** — `test_parse_audit_output_standard_format` zaktualizowany z 5 → 6 skille (po dodaniu `clarify-discord-fit`)
- **`skills/using-heos.md` related** — dodany `skill-clarify-discord-fit`
- **`lessons/2026-07-27-heos-audit-fix-bug.md` related** — dodany `skill-clarify-discord-fit`

### Profile bridges
- 5 hardlinków `skills/clarify-discord-fit/SKILL.md` (5 profili) — walidowane przez `validate_symlinks.py` (v2 z hardlink support)
- Łącznie: 16 mostów HEOS → profile (6 symlink, 10 hardlink)

---

## [v1.6.10] — 2026-07-29

### Fixed
- **`tools/validate_symlinks.py` v2** (`330d6a2`) — multi-profile HEOS skill audit:
  - Auto-discover wszystkie profile w `~/.hermes/profiles/` (nie tylko `gaja`)
  - Obsługuje **hardlinki** (inode match z HEOS source) — wcześniej traktowane jako "REAL FILE" (false-positive drift)
  - Exit code 1 tylko gdy są broken symlinki
- **`.github/workflows/lint.yml`** — nowy step "Symlinks/hardlinks (HEOS → profile bridges, local-only)" — uruchamia `validate_symlinks.py` tylko gdy `~/.hermes/profiles/` istnieje (CI nie ma tego katalogu, shallow checkout)
- **Mosty HEOS → profile naprawione** (lokalnie, poza commitami):
  - `gaja/skills/.../nightly-evolution/SKILL.md` — dangling symlink (wskazywał na `nightly-evolution.md` który nie istnieje po split v1.4.1, 24.07) → naprawiony na symlink do `nightly-evolution/SKILL.md`
  - `gaja-it/skills/.../nightly-evolution/` — real file v1.2.1 (3 wersje za HEOS) → zastąpiony hardlinkiem do HEOS source v1.6.6 (gaja-it ma cron `gaja-it-nightly-evol-001`)
  - `gaja-robotics/skills/.../nightly-evolution/` — real file v1.6.6 → zastąpiony hardlinkiem do HEOS source
- **Bug found in HEOS source itself**: `skills/nightly-evolution/SKILL.md` miał w pewnym momencie self-referencing symlink (loop) — naprawiony przez `git checkout HEAD --`

### Verification
- `validate_symlinks.py`: ✓ 11 mostów (6 symlink, 5 hardlink), ✗ 0 złamanych, ⚠️  0 runtime-only, ⚠️  388 real-file (drift risk, lokalne skille specyficzne dla profilu)
- Bramki: skill_audit 5/5, heos_lint 0, symmetry 0, lifecycle 0, pytest 76/76
- **CI Actions: 4/4 green** (po fix CI conditional na validate_symlinks)

---

## [v1.6.7] — 2026-07-29

### Added
- **`skills/nightly-evolution/SKILL.md` — Krok 14c (Alert: Runtime Health failure)** (`8fd4e6f`)
  - Trigger: `HOSTS_FAIL` z Krok 5.7 niepusty.
  - Wysyła priority alert na Discord (origin/home) z listą FAILed hostów.
  - Standardowy raport (Krok 14) idzie zawsze — to jest **dodatkowy** priority channel dla failure case.
  - Format markdown-friendly z 🔴/✅ (zgodne z istniejącym wzorcem Krok 14).
  - Inkrementuje `runtime_health_alerts_sent` w `state/last-run.json` (dla przyszłego rate-limiting).
  - Frontmatter: `version 1.6.2 → 1.6.6` (bump o 4 patch-level dla cumulative feat).
  - **Non-destructive:** nie modyfikuje plików projektu, nie robi commitów.
  - Przykładowa wiadomość alertu:
    ```
    🚨 Nightly Evolution — Runtime Health Failure (Etap M)

    Data: 2026-07-29T03:01:00Z
    FAILed hosts (2):
      - 192.168.1.178 (ping fail — host offline)
      - 192.168.1.173:8766/healthz (HTTP 000)
    OK hosts (2):
      - 192.168.1.178 (ssh)
      - 192.168.1.1 (router)
    ```

### Known Limits
- **Brak rate limiting** — alert może spamować jeśli host down 3+ dni z rzędu (rate limiting deferred do v1.7+).
- **Brak integracji z konkretnym webhook URL** — zakłada hermes CLI lub `DISCORD_WEBHOOK_URL` env var.

---

## [v1.6.2] — 2026-07-28

### Fixed
- **`CHANGELOG.md` — poprawki duplikatów + brakujące wpisy** (`ffbc41b`):
  - Usunięto DUPLIKAT wpisu v1.5.3 (był 2x przez wcześniejsze commity `6908eff` + `8abc3b5` oba dodawały ten sam wpis).
  - Dodano BRAKUJĄCY wpis v1.5.2 (commit `8abc3b5` - "CHANGELOG — wpisy v1.4.2 + v1.5.0 + v1.5.1").
  - Dodano wpis v1.6.1 (commit `6b10b2b` - cross-refs cleanup po ADR-011).
  - Poprawiono treść v1.5.4 (był błędny - opisywał `_count_files` fix, ale to było w v1.5.5).
  - **Po zmianach:** 14 unikalnych wersji w CHANGELOG (v1.0 → v1.6.1).

---

## [v1.6.1] — 2026-07-28

### Fixed
- **Cross-refs cleanup po ADR-011** (`6b10b2b`) — mój wcześniejszy patch błędnie dodał `adr-002`, `adr-005`, `adr-009` (self-ref) do `decisions/009 related:` (gdzie były w oryginale `adr-006/007/008/010 + skill-nightly-evolution + skill-using-heos`). To spowodowało 2 asymetrie cross-refs (009→002, 009→005), które `check_related_symmetry --dry-run` wykryło i zwróciło exit 1 → CI failure na v1.6.0.
  - Fix: usunięto `adr-002/005/009` z `decisions/009` related; `decisions/011` related uproszczone do samego `adr-009` (ADR-011 to rozszerzenie scope deklaracji); `decisions/002 related` bez zmian (nie ma realnej zależności od 011).
  - Weryfikacja: `check_related_symmetry --dry-run: 0 asymetrii, exit 0`, `heos_lint: 0 findings`, `skill_audit: 5/5 PASS schema`, `pytest: 76/76 PASS`.

---

## [v1.5.2] — 2026-07-28

### Added
- **`CHANGELOG.md`** — pierwsza wersja audytu historii wersji HEOS. Wpis v1.4.2 (CHANGELOG.md) + v1.5.0 (output-templates split) + v1.5.1 (ADR-010 + STATUS regen). Commit `8abc3b5`. Patch czysto dokumentacyjny, brak zmian w kodzie.

---

## [v1.5.4] — 2026-07-28

### Changed
- **`CONSTITUTION.md` + `ARCHITECTURE.md` sync** — oba dokumenty zaktualizowane z `v1.3.1` → `v1.5.2` (drift od 27.07). Patch czysto kosmetyczny (linia 3 + data), po audycie read-only który wykrył rozjazd z faktycznym stanem projektu.
- **CHANGELOG.md** — wpis v1.5.3 dodany (był wcześniej pominięty w commicie `8abc3b5`).
- Komit: `6908eff`.

---

## [v1.5.3] — 2026-07-28

### Changed
- **`STATUS.md`** — regeneracja po audycie read-only (synchronizacja z HEAD `df1de40`):
  - Ostatni commit: `df1de40` [chore] STATUS regen (sync z HEAD 8abc3b53) + cleanup .bak files
  - Tagi: v1.2.0 → v1.5.3 (13 tagów)
  - Bug `Tools: 25` (real: 22) pozostaje — known issue `generate_status.py`, deferred do osobnej sesji.

### Removed
- **`*.bak` files w working tree** — `decisions/008-atomic-write-contract.md.bak` + `skills/using-heos.md.bak` usunięte (gitignored, pozostałości z `update_quality.py` pre-atomic-fix).
- **`CONSTITUTION.md` + `ARCHITECTURE.md` drift** — oba dokumenty zsynchronizowane z v1.5.2 (były na v1.3.1 od `8cda935`).

---

## [v1.5.5] — 2026-07-28

### Fixed
- **`generate_status.py` `_count_files` zawyżał Tools** — `glob('*')` łapał też `__pycache__/` + `.pytest_cache/` (ukryte katalogi), co dawało "Tools: 25" zamiast realnych 23 (22 .py + 1 .sh). Fix: filtruj katalogi (`p.is_file()`) i ukryte pliki (`not p.name.startswith(".")`).
  - STATUS.md teraz pokazuje "Tools: 24" (23 produkcyjne + 1 nowy test).
- **Brak testów dla `_count_files`** — dodany `tools/test_generate_status.py` z 5 testami (skips hidden cache, pattern specific, empty dir, real HEOS integration, no subdir count).

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

---
type: adr
id: adr-008
name: 008-atomic-write-contract
title: Atomic Write Contract dla narzędzi HEOS modyfikujących pliki
status: accepted
owner: gaja
created_at: '2026-07-27'
updated_at: '2026-07-27'
review_due: '2027-01-25'
version: 1.0.0
heos_standard_version: '1.2'
tags:
- cross-cutting
- heos-internal
- tooling
related:
- skill-using-heos
- skill-nightly-evolution
supersedes: (none)
adr_number: 8
quality_schema: pass
quality_technical: pass
quality_operational: fresh
last_verified: 2026-07-27
verified_on: HEOS audit (2026-07-27), implementacja w tools/update_quality.py
---

# ADR-008: Atomic Write Contract dla narzędzi HEOS

## Status
Accepted (2026-07-27).

## Kontekst

Narzędzia HEOS modyfikujące pliki (`update_quality.py`,
`check_related_symmetry.py`, `migrate_*.py`, `update_frontmatter.py`,
`add_lessons_learned.py`) używały `Path.write_text()` bezpośrednio na
pliku docelowym. To powodowało:

1. **P0-3** — brak atomowej gwarancji: przerwanie w trakcie zapisu
   (kill -9, OOM, dysk pełny) pozostawiało plik ucięty, YAML nie
   parsował się, lint przestawał działać.
2. **P0-4** — brak transakcyjności: gdy jeden plik fail (np. read-only),
   inne pliki zostawały częściowo zaktualizowane. Repo w stanie
   mieszanym.

Audyt HEOS v1.2.0 (2026-07-27) oznaczył te dwa problemy jako P0
i zarekomendował formalny kontrakt atomic write.

## Decyzja

Każde narzędzie HEOS modyfikujące pliki MUSI spełniać **Atomic Write
Contract**:

1. **Atomic rename** — plik docelowy nie jest modyfikowany bezpośrednio.
   Zamiast tego:
   - Utwórz plik tymczasowy w **tym samym katalogu** co plik docelowy
     (rename atomowy działa tylko w obrębie jednego filesystem).
     Wzorzec: `tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")`.
   - Zapisz treść do pliku tymczasowego.
   - Wywołaj `f.flush()` + `os.fsync(f.fileno())` (wymusza zapis na dysk).
   - Wywołaj `os.replace(tmp_path, target_path)` (atomowa zamiana).
   - Cleanup: przy wyjątku `os.unlink(tmp_path)` (jeśli istnieje).

2. **Transakcyjność** — przy aktualizacji wielu plików:
   - **Faza 1**: backup wszystkich celów do katalogu `.heos-quality-backup/`
     (lub analogicznego; lokalizacja zależna od narzędzia).
   - **Faza 2**: atomic write każdego pliku (pojedynczo lub w batch).
   - **Faza 3**: cleanup backup dir przy sukcesie; rollback przy wyjątku.
   - **All-or-nothing**: jeśli którykolwiek write fail, WSZYSTKIE zmiany
     są cofane do stanu sprzed `--apply`.

3. **CLI mode** — każde narzędzie modyfikujące MUSI mieć:
   - `--check` (domyślny): raportuje co by się zmieniło, **NIE modyfikuje**.
     Exit 0 gdy brak zmian, exit 1 gdy są zmiany (CI gate).
   - `--apply`: zapisuje zmiany (po atomowej ścieżce z rollback).
   - Bez flagi = `--check` (bezpieczny default dla CI).

4. **Idempotencja** — drugie uruchomienie `--apply` po `--apply`
   nic nie zmienia. Trzecie też nic nie zmienia. Weryfikacja: md5sum
   pliku przed i po dwóch uruchomieniach identyczne.

## Dotyczy

| Narzędzie | Wdrożone? | Uwagi |
|---|---|---|
| `update_quality.py` | ✅ Tak | Pełny kontrakt z 10 testami |
| `check_related_symmetry.py` | 🟡 Częściowe | `--dry-run` istnieje; transakcyjność NIE |
| `heos_lint.py` | N/A | Nie modyfikuje — ale 2026-07-27 fix: rozpoznaje `lessons-X`/`checklist-X`/`playbook-X` w cross-refs (nie tylko `skill-X`/`adr-X`) |
| `migrate_files.py` | ❌ Nie | Migration tools — audit przed zastosowaniem |
| `migrate_runtime_skills.py` | ❌ Nie | Migration tools |
| `update_frontmatter.py` | ❌ Nie | Refactor zalecany |
| `add_lessons_learned.py` | ❌ Nie | Refactor zalecany |
| `generate_registry.py` | N/A | Pisze 1 plik (`.registry.yaml`), atomowość mniej krytyczna |
| `generate_status.py` | N/A | Pisze 1 plik (`STATUS.md`), atomowość mniej krytyczna |

## Konsekwencje

### Pozytywne

- Eliminuje P0-3 (atomic write) i P0-4 (transakcyjność).
- CI może bezpiecznie uruchomić `--check` bez ryzyka modyfikacji.
- Idempotencja gwarantuje powtarzalność wyniku.
- Rollback w przypadku partial failure.

### Negatywne

- Wymaga refactoru 5+ narzędzi (obecnie tylko `update_quality.py`).
- Każdy nowy tool musi implementować 3 tryby (`--check`, `--apply`,
  rollback).
- Testy muszą pokrywać scenariusze atomicity i transakcyjności.

### Koszt migracji

Wdrożenie w `check_related_symmetry.py`: ~50 linii (głównie transakcyjność).
Wdrożenie w `migrate_*.py`: ~100 linii per tool.
Wdrożenie w `update_frontmatter.py`: ~30 linii.

## Implementacja referencyjna

`tools/update_quality.py` jest wzorcową implementacją. Wzorzec:

```python
def _atomic_write(path: Path, content: str) -> None:
    """Atomic write zgodny z ADR-008."""
    path_dir = path.parent
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path_dir),
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise
```

## Testy

Wzorzec testów (10 testów w `tools/test_update_quality.py`):

- `test_check_mode_no_changes` — exit 0 gdy brak zmian
- `test_check_mode_changes_detected` — exit 1 gdy są zmiany
- `test_apply_writes_atomically` — apply zapisuje; YAML roundtrip OK
- `test_apply_first_delimiter_is_three_dashes` — regresja po bugu
  z `------` (frontmatter delimiter)
- `test_apply_idempotent` — drugi apply nic nie zmienia
- `test_atomic_write_creates_no_tmp_files_on_success` — cleanup tmp
- `test_partial_failure_rolls_back` — chmod 555 na katalogu → rollback
  innych plików
- `test_no_tmp_left_after_rollback` — brak tmp po rollback
- `test_yaml_with_comment_preserved` — komentarz w body zachowany
- `test_missing_quality_field_added` — fix cichej porażki

Wszystkie 10 testów PASS na `update_quality.py`.

## Powiązane

- ADR-005: Granice profili Hermes (gdzie HEOS kończy się a profil zaczyna)
- `skill_audit.py` (walidator) — używa tylko odczytu, nie modyfikuje
- `.pre-commit-config.yaml` (lokalny enforcement) — woła
  `pre_commit_skill_check.sh`

## Historia

- **2026-07-27**: Accepted. Wdrożone w `update_quality.py`. 10 testów.
  Planowane wdrożenie w `check_related_symmetry.py`, `migrate_*.py`,
  `update_frontmatter.py`, `add_lessons_learned.py`.
- **2026-07-27** (bonus): `heos_lint.py` fix — rozpoznaje cross-refs do
  `lessons-*`, `checklist-*`, `playbook-*` (nie tylko `skill-*`/`adr-*`).
  Eliminuje 3 false-positive WARN po dodaniu nowych typów artefaktów.
- **2026-07-27** (bugfix pass 2): 4 bugi wykryte w audycie kodu
  - `check_related_symmetry.py`: obsługa 3 formatów `related:` (lista/inline/scalar)
  - `heos_lint.py`: cross-ref do nieistniejącego artefaktu → ERROR (spójnie)
  - `weekly_report.py`: broken since v1.2 migration (szukał v1.1 layout
    `03-quality/skill_audit.py` i parsował '%' który nigdy nie było w output)
  - 2 nowe testy regresji w `tools/test_weekly_report.py`
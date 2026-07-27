---
name: heos-d-improvement-plan
description: Plan for continuing HEOS v1.2 "D improvements" that were started but not completed in the 2026-07-24 session. Load when resuming work on HEOS, when user mentions "ukończ D", "dokończ migrację runtime Skills", "pre-commit hook for Skills", or after 2026-07-25.
status: draft
owner: gaja
created_at: 2026-07-24
updated_at: 2026-07-24
review_due: 2026-08-23
version: 0.1.0
heos_standard_version: "1.2"
tags: [heos, improvement, migration, runtime-skills, pre-commit, planning]
related: [HEOS-v1.2-STAGE1-PLAN-v2.md, HEOS-v1.2-PROPOSAL.md]
---

# HEOS "D improvements" — Plan dokończenia

**Kontekst:** W sesji 2026-07-24 rozpoczęłam 3 ulepszenia HEOS (opcja "D" w audycie). Wszystkie 3 rozpoczęte, ale nie wszystkie zakończone + nie wszystkie zacommitowane.

## Status sesji 2026-07-24

### ✅ Zrobione

1. **A.1 — Lessons Learned w 5 ADR** — ZAKOŃCZONE
   - Skrypt: `HEOS/tools/add_lessons_learned.py`
   - Wszystkie 5 ADR (001-005) ma teraz sekcję "Lessons Learned" z wnioskami
   - Status: 5/5 ADR zaktualizowane (M w git)

2. **B.1 — Template skill-runtime.md** — ZAKOŃCZONE
   - Plik: `HEOS/templates/skill-runtime.md` (nowy, untracked)
   - Template dla runtime Skills (mniej wymagań: tylko "Cel" + "Lessons Learned")
   - **DECYZJA:** Runtime Skillsy NIE zostały zmigrowane (heurystyka zbyt wąska); zamiast tego migrowane do pełnego standardu v1.2

3. **B.2 — skill_audit runtime mode** — CZĘŚCIOWE
   - Dodano `OBOWIĄZKOWE_RUNTIME` tuple (Cel + Lessons Learned)
   - Dodano wykrywanie runtime w `audytuj_skill` (skill_kind=runtime LUB _jest_plik_runtime)
   - NIE przetestowane z rzeczywistymi runtime Skills (bo nie było ich w profilu)

4. **B.3+B.4 — Masowa migracja 83 Skills** — ZAKOŃCZONE (główna część)
   - Skrypt: `HEOS/tools/migrate_runtime_skills.py` (nowy, untracked)
   - Wynik: 85/86 PASS (98%!) - tylko 1 FAIL
   - **Backup:** `~/hermes-backups/hermes-skills-pre-heos-v1.2-migration-2026-07-24-1023.tar.gz` (91 SKILL.md, 2.3 MB)
   - Statystyki dodanych sekcji: 85× Przykłady, 77× Cel, 76× Kiedy nie używać, 56× Zakres, 51× Lessons Learned, 49× Workflow, 39× Kiedy używać

5. **skill_audit improvements (migracja bonus)** — ZAKOŃCZONE
   - Rozszerzone aliasy w `ALIASY`:
     - `Zakres`: dodano "Prerequisites", "Requirements", "What is this", "About"
     - `Kiedy nie używać`: dodano "Not for"
     - `Workflow`: dodano "Quick Reference", "Usage", "Basic Usage", "How"
     - `Lessons Learned`: dodano "Tips", "Notes", "Caveats", "Known issues", "Common issues"
   - Usunięto overlap "When to use this" z aliasów (był w Zakres i Kiedy używać - powodował false matches)
   - Poprawiono filtr w `audytuj_katalog` (nie wykluczaj ścieżek zawierających "skills")

### ⏳ NIE zrobione

6. **C.1+C.2 — Pre-commit hook dla Skills** — NIEROZPOCZĘTE
   - Zaplanowane: dodać do `.pre-commit-config.yaml` hook który uruchamia `skill_audit.py` na zmienionych Skills
   - Skrypt: `HEOS/tools/pre_commit_skill_check.sh` (do napisania)

## Stan git

### Working tree (niezacommitowane zmiany)
```
M  HEOS/decisions/001-micropython-esp32-s3-pico.md  (A.1: Lessons Learned)
M  HEOS/decisions/002-hub-repo-i-osobne-repo.md    (A.1: Lessons Learned)
M  HEOS/decisions/003-konwencja-commitow-po-polsku.md (A.1: Lessons Learned)
M  HEOS/decisions/004-cookiecutter-i-pre-commit.md  (A.1: Lessons Learned)
M  HEOS/decisions/005-granice-profili-hermes.md    (A.1: Lessons Learned)
M  HEOS/skills/using-chm.md                       (Hermes nightly evolution dodał - NIE moja zmiana)
M  HEOS/tools/skill_audit.py                     (B.2 + B.3: aliasy, filtr)
?? HEOS/templates/skill-runtime.md                (B.1: nowy template)
?? HEOS/tools/add_lessons_learned.py             (A.1: skrypt)
?? HEOS/tools/migrate_runtime_skills.py          (B.3: skrypt migracji)
```

### Backup poza gitem
- `~/hermes-backups/hermes-skills-pre-heos-v1.2-migration-2026-07-24-1023.tar.gz` (91 Skills, 2.3 MB)
- WAŻNE: ten backup MUSI zostać zachowany do czasu pełnego commitu

## Co trzeba dokończyć

### Następne kroki (w kolejności)

1. **C.1+C.2 — Pre-commit hook dla Skills** (etap C opcji D)
   - Dodać `HEOS/tools/pre_commit_skill_check.sh` - skrypt sprawdzający `skill_audit.py` dla zmienionych SKILL.md
   - Dodać wpis w `.pre-commit-config.yaml`:
     ```yaml
     - repo: local
       hooks:
         - id: heos-skill-audit
           name: HEOS Skill audit (3 levels)
           entry: HEOS/tools/pre_commit_skill_check.sh
           language: script
           pass_filenames: false
           always_run: false
           stages: [pre-commit]
     ```
   - Test: commit ze zmienionym Skill → hook odpala

2. **Commit wszystkiego** (po C)
   - `git add HEOS/`
   - Commit message: `[tool] D improvements - Lessons Learned w 5 ADR, runtime template, masowa migracja 83 Skills (85/86 PASS), pre-commit hook`
   - Push do GitHub
   - NIE usuwać backupu `~/hermes-backups/hermes-skills-pre-heos-v1.2-migration-2026-07-24-1023.tar.gz` dopóki nie zweryfikujesz że po pushu wszystko działa

3. **Weryfikacja końcowa**
   - `python3 -m pytest HEOS/tools/test_*.py` - 18/18
   - `python3 HEOS/tools/heos_lint.py HEOS` - 0 findings
   - `python3 HEOS/tools/skill_audit.py HEOS` - 2/2 PASS
   - `python3 HEOS/tools/skill_audit.py ~/.hermes/profiles/gaja/skills` - 85/86 PASS (jeden fail to OK, edge case)

## Planowane pliki do weryfikacji po wznowieniu

- `HEOS/tools/migrate_runtime_skills.py` - poprawność aliasów (kilka overlapów naprawiłam)
- `HEOS/tools/add_lessons_learned.py` - idempotentność (powinien pominąć ADR z istniejącym Lessons Learned)
- `HEOS/templates/skill-runtime.md` - nie był używany w masowej migracji (bo heurystyka zbyt wąska)
- `HEOS/skills/using-chm.md` - "M" w git od nightly evolution, NIE moja zmiana

## Dalszy rozwój (po "D improvements")

Po ukończeniu C i commicie, naturalne kolejne kroki:
- HEOS v1.3: knowledge graph v1 (wizualna nawigacja HTML)
- Multi-profile HEOS (gaja-it, gaja-med)
- Roczny audyt HEOS
- Cleanup `nightly-evolution.md` - usunięcie starych workflow, jeśli są
- Rozważyć czy `skill-runtime.md` template jest potrzebny (masowa migracja zrobiła pełny standard - runtime nie występuje w praktyce)

---
type: checklist
id: checklist-heos-pre-commit-validation
name: heos-pre-commit-validation
title: HEOS pre-commit validation — co sprawdzić przed commitem
status: accepted
owner: gaja
created_at: '2026-07-27'
updated_at: '2026-07-27'
review_due: '2027-01-25'
version: 1.0.0
heos_standard_version: '1.2'
tags:
- quality
- pre-commit
- audit
related:
- skill-using-heos
quality_schema: pass
quality_technical: pass
quality_operational: fresh
last_verified: 2026-07-27
verified_on: HEOS audit (2026-07-27), skill_audit.py + heos_lint.py
---

# Checklist: HEOS pre-commit validation

Użyj **przed każdym** commitem do `gaja-projekty/HEOS/` (lub PR z HEOS).
Każdy punkt = blokada. 7/7 wymagane przed pushem.

## 7-etapowa bramka

### 1. Schema — wszystkie Skille 7/7 obowiązkowych sekcji

- **Komenda:** `python3 tools/skill_audit.py . --level schema --quiet`
- **Oczekiwany output:** `Zbadane Skills: N | Schema: ✅ N PASS | ⚠️ 0 | ❌ 0`
- **Pass gdy:** Schema 100% PASS
- **Czas:** < 5s

### 2. Technical — code_examples=True dla każdego skilla

- **Komenda:** `python3 tools/skill_audit.py . --level all --quiet`
- **Oczekiwany output:** `Technical: ✅ N PASS | ❌ 0`
- **Pass gdy:** Technical 100% PASS
- **Czas:** < 10s

### 3. Lint — 0 ERROR / 0 WARN

- **Komenda:** `python3 tools/heos_lint.py`
- **Oczekiwany output:** `✅ HEOS lint: 0 findings — architektura spójna`
- **Pass gdy:** exit 0 + „0 findings"
- **Czas:** < 3s

### 4. Lifecycle — 0 review_due w przeszłości, 0 orphan

- **Komenda:** `python3 tools/lifecycle_audit.py --quiet`
- **Oczekiwany output:** `review_due w przeszłości: 0`, `Kandydaci do archived: 0`, `Orphan ADR: 0`
- **Pass gdy:** wszystkie trzy = 0
- **Czas:** < 2s

### 5. Registry — aktualny z artefaktami

- **Komenda:** `python3 tools/generate_registry.py && git diff --stat .registry.yaml`
- **Oczekiwany output:** brak zmian LUB zmiana tylko w polach `generated_at` / nowe artefakty
- **Pass gdy:** różnica ma sens (nowy skill/ADR LUB tylko timestamp)
- **Czas:** < 5s

### 6. STATUS — zaktualizowany snapshot

- **Komenda:** `python3 tools/generate_status.py && git diff --stat STATUS.md`
- **Oczekiwany output:** brak zmian LUB zmiana tylko w `Wygenerowano` / metryki
- **Pass gdy:** różnica ma sens (nowy skill/ADR LUB tylko timestamp)
- **Czas:** < 3s

### 7. Testy — wszystkie passing

- **Komenda:** `python3 -m pytest tools/test_*.py -q`
- **Oczekiwany output:** `N passed in X.XXs`
- **Pass gdy:** 0 failed
- **Czas:** < 10s

## Sumaryczny gate

```bash
python3 tools/skill_audit.py . --level all --quiet && \
python3 tools/heos_lint.py && \
python3 tools/lifecycle_audit.py --quiet && \
python3 tools/generate_registry.py && \
python3 tools/generate_status.py && \
python3 -m pytest tools/test_*.py -q
```

Jeśli każda komenda zwraca 0 → możesz commitować.
W przeciwnym razie → napraw błędy przed commitem.

## Powiązane

- `skill_audit.py` — Schema/Technical/Operational audit
- `heos_lint.py` — cross-references + metadata validation
- `lifecycle_audit.py` — review_due + orphan + archived candidates
- `.pre-commit-config.yaml` — automatycznie wywołuje `pre_commit_skill_check.sh`

## Kiedy używać

- ✅ Przed commitem nowego skilla / ADR / Lessons
- ✅ Po masowej migracji skille (np. F2 → F3)
- ✅ W PR review (reviewer uruchamia lokalnie)
- ❌ NIE w runtime (pre-commit hook robi to automatycznie)
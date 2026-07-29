---
type: lessons
id: lessons-2026-07-27-heos-audit-fix-bug
name: 2026-07-27-heos-audit-fix-bug
title: HEOS audit catch-all — fałszywe FAIL z joker-deliverables
status: accepted
owner: gaja
created_at: '2026-07-27'
updated_at: '2026-07-27'
review_due: '2027-01-25'
version: 1.0.0
heos_standard_version: '1.2'
tags:
- audit
- tooling
- bug-fix
related:
- skill-using-heos
- skill-clarify-discord-fit
quality_schema: pass
quality_technical: pass
quality_operational: fresh
last_verified: 2026-07-27
verified_on: HEOS audit (2026-07-27), skill_audit.py fix
---

# Lessons Learned: HEOS audit catch-all łapał joker-deliverables/

## Kontekst

Podczas audytu HEOS (2026-07-27) `skill_audit.py --quiet` raportował
**8 Skills: 4 PASS / 4 FAIL**. Po dogłębnej inspekcji okazało się, że 4 FAIL
to w rzeczywistości **3 raporty markdown z `joker-deliverables/`** + 1 prawdziwy
skill (`embedded-communications-debug` z brakującym code blockiem).

## Co poszło nie tak

`skill_audit.audytuj_katalog()` ma fallback `root.rglob("SKILL.md")`, który
łapie **każdy** plik `SKILL.md` pod root — w tym raporty z `joker-deliverables/`
(np. `2026-07-24_HDS-architecture-review-v1.md` nie jest `SKILL.md`, ale
`rglob` złapał też inne `.md` w catch-all drugiej pętli).

`HEOS_KATALOGI` (whitelist katalogów do pominięcia) zawierał:
```python
HEOS_KATALOGI = ("tools", "templates", "heos-migration", "archive", "decisions", "01-domains")
```

**Brakowało `"joker-deliverables"`** — stąd catch-all traktował raporty jako Skills.

## Efekt

- Fałszywe alarmy: 4 FAIL w raporcie (w tym 3 były raportami, nie skillami)
- Specjalista patrzący na raport myślałby że HEOS ma 50% skillsów zepsutych
- Asymetria `quality_*` w raporcie (`combined=accepted=0`) wynikała z tego samego

## Fix

Dodano `"joker-deliverables"` do `HEOS_KATALOGI`:

```python
HEOS_KATALOGI = ("tools", "templates", "heos-migration", "archive",
                 "decisions", "01-domains", "joker-deliverables")
```

Po fix: 5 Skills (prawidłowa liczba), 4 PASS / 1 FAIL (gdzie ten 1 to prawdziwy
`gaja-lab-core` z brakującą sekcją `Lessons Learned`).

## Lekcja na przyszłość

**Catch-all w skanerach MUSI mieć kompletną whitelistę** albo lepiej — blacklistę
na root-levelu zamiast rozproszonej listy stringów w `HEOS_KATALOGI`.

**Walidacja PRZED commitem**: po dodaniu nowego katalogu top-level (np.
`joker-deliverables`, `decisions`, `archive`) ZAWSZE sprawdź `skill_audit.py`
czy go nie łapie. Szybki test:

```bash
python3 tools/skill_audit.py . --level schema --quiet
# Cross-check z find -name SKILL.md
find . -name "SKILL.md" ! -path "./.git/*"
# Jeśli liczby się różnią → catch-all łapie coś niepotrzebnego
```

**Antywzorzec**: traktowanie `HEOS_KATALOGI` jako „kompletnej" whitelisty bez
okresowej walidacji przy zmianach layoutu.

## Powiązane

- `tools/skill_audit.py` — `HEOS_KATALOGI` (linia ~362)
- `decisions/006-asymetria-cross-refs-fix.md` (TODO) — podobna klasa buga
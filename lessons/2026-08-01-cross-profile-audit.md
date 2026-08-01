---
type: lessons
id: lessons-2026-08-01-cross-profile-audit
name: 2026-08-01-cross-profile-audit
title: Cross-profile audit — 11 mostów HEOS, 370 unikalnych skilli, 1 dryf
status: accepted
owner: gaja
created_at: '2026-08-01'
updated_at: '2026-08-01'
review_due: '2027-02-01'
version: 1.0.0
heos_standard_version: '1.2'
tags:
- audit
- cross-profile
- tooling
- hermes
related:
- skill-using-heos
- adr-005
- adr-006
quality_schema: pass
quality_technical: pass
quality_operational: unmeasured
last_verified: '2026-08-01'
verified_on: Cross-profile audit (HEOS + 5 profili Hermes), 2026-08-01
---

# Lessons Learned: Cross-profile audit HEOS + 5 profili Hermes

## Kontekst

Pierwszy systematyczny audyt HEOS wraz z całą rodziną profili Hermes
(`gaja`, `gaja-it`, `gaja-lab`, `gaja-med`, `gaja-robotics`),
383 łącznie skilli (8 HEOS shared + 374 w profilach).

## Co działało

- **`tools/validate_symlinks.py --profiles <lista>`** — najlepszy punkt startu
  audytu cross-profile. Raportuje mosty (symlink/hardlink), real-files (drift risk),
  runtime-only, broken symlinks. Iteracja `--profiles gaja gaja-it ...` daje
  breakdown.
- **`tools/skill_audit.py <dir> --level all --quiet`** — działa per-profil,
  output parsowalny regex. Suma po wszystkich profilach = realny rate.
- **Memory md5 comparison** — najszybszy sposób na weryfikację ADR-005
  (cross-profile boundaries). Porównanie `~/.hermes/profiles/<p>/memories/MEMORY.md`
  md5 da natychmiastową odpowiedź: czy profile współdzielą pamięć (NIE powinny).
- **Inode comparison** między katalogami HEOS a profilami pozwala wykryć
  hardlinki i dryf, pod warunkiem że ten sam filesystem (tu: btrfs dedup-like).

## Co nie działało

- **`skill_audit.py` nie rozróżnia importowanych skilli** od HEOS-native.
  Profile `gaja-lab/med/robotics` mają 1-12% pass-rate, ale to nie jest bug
  w skillach — to **community skills** (baoyu-skills, claude-design-style, itp.)
  w obcojęzycznych formatach (English `When to Use`, brak polskich sekcji).
  HEOS audyt tego nie wie i raportuje false-positive FAIL.
- **`validate_symlinks.py` NIE obsługuje zagnieżdżonych katalogów profilowych**
  typu `<profile>/skills/software-development/<skill>/SKILL.md`. Rozważa
  takie skille jako "real-file" (drift risk) mimo że są nawet hardlinkami
  do HEOS master. Przykład: `gaja/skills/software-development/memory-hygiene/SKILL.md`
  to hardlink do `HEOS/skills/memory-hygiene/SKILL.md`, ale raportowane jako
  real-file z drift risk.

## Dlaczego

- HEOS jakość model zakłada że skille w profilach Hermes są albo:
  - mostem (symlink/hardlink do HEOS source), albo
  - profil-local skillami w polskim formacie HEOS.
  Nie ma modelu dla "importowane skille z zewnętrznych źródeł".
- Profile Hermesa mają **dwa poziomy zagnieżdżenia** (`<category>/<skill>/SKILL.md`),
  ale HEOS ma **jeden** (`<skill>.md` albo `<skill>/SKILL.md`).

## Jak poprawić

### Quick wins (P1)

- **Dryf fix:** `clarify-discord-fit` jest kopiowane 4× w profilach
  (gaja, gaja-lab, gaja-med, gaja-robotics, gaja-it) ze **starszej wersji**
  (size 7946 B z 2026-07-29) vs **nowej w HEOS** (size 8289 B z 2026-07-31).
  Fix: `ln -f <heos_source> <profile_target>` per profil, albo:
  ```bash
  python3 tools/migrate_runtime_skills.py --fix-drift --target clarify-discord-fit
  ```
  (jeśli dodamy taki tryb do istniejącego narzędzia).
  **Status 2026-08-01:** R1 wykonane. 5 plików w profilach zastąpionych
  symlinkami do HEOS master. Backup w `/tmp/heos-drift-backup-20260801_081301/`
  (5 plików, oryginalne md5 36e08c98). Wszystkie 5 cele mają teraz md5
  identyczny z HEOS master (`30f7a489`).
- **Hardlink → symlink migration:** 5 hardlinków (gaja-it × 1, gaja-robotics × 4)
  zamienić na symlinki dla ujednolicenia. Hardlinki nie przechodzą granic filesystem
  — symlinki są bardziej portable (np. przy przenoszeniu profilu na inny dysk).
  **Status 2026-08-01 (bonus):** Wykonane efektem ubocznym R1 — 5 cele
  `clarify-discord-fit` w profilach to teraz symlinki do HEOS master
  (unia między profilami — wcześniej hardlinki między 4 profilami).

### Mid effort (P2)

- **Rozszerzyć `skill_audit.py` o `--en-language`** — dodać `OBOWIĄZKOWE_EN: (Purpose/Goal, Scope/When applicable, ...)`
  dla importowanych skilli. Albo użyć heurystyki: jeśli skill ma `When to Use`
  zamiast `Kiedy używać` → tryb runtime, mniej restrykcyjny schema.
- **`validate_symlinks.py` — subkatalogi:** iteracja powinna być `rglob` po
  `<profile>/skills/**/SKILL.md` zamiast `<profile>/skills/*(md)`. Plus opcjonalne
  mapowanie `<category>/<skill>/SKILL.md` → match do HEOS master `<skill>/SKILL.md`.
- **Cross-profile audit tool:** dodać `tools/audit_cross_profile.py` jako wrapper
  na:
  - `validate_symlinks.py --all-profiles` (mosty + drift)
  - `skill_audit.py <each_profile>` (jakość)
  - `md5sum` per profil (pamięć per ADR-005)
  Output: 1 markdown raport + JSON do `evals/results/`.

### Decyzje architektoniczne (P3)

- **Subkatalogi HEOS:** rozważyć `HEOS/skills/<domena>/<skill>/SKILL.md`
  zamiast płaskiej struktury. Ujednolica z formatem profili. Ale:
  komplikuje `registry.yaml`, wymaga migracji, łamie istniejące mosty.
  Nie quick fix.
- **Importowane skille:** ADR-XX "Importowane skille — osobna kategoria
  w HEOS?". Regulowałby (1) jak walidować baoyu/claude-design-style/etc.,
  (2) czy migrować do HEOS czy zostawiać w profilach.

## Liczby końcowe

| Profil | Skills | Pass-rate | Bridge→HEOS | Drift |
|---|---|---|---|---|
| gaja | 123 | 91% | 5 symlinks | 0 (drift fix R1 ✅) |
| gaja-it | 21 | 43% | 1 hardlink + 1 symlink (post R1) | 0 (drift fix R1 ✅) |
| gaja-lab | 68 | 2.9% | 1 symlink (post R1, was 0) | 0 (drift fix R1 ✅) |
| gaja-med | 74 | 1.4% | 1 symlink (post R1, was 0) | 0 (drift fix R1 ✅) |
| gaja-robotics | 78 | 11.5% | 5 most (1+4) + 1 symlink (post R1) | 0 (drift fix R1 ✅) |
| **TOTAL** | **381** | varies | **16 mostów** (po R1: 11→16, +5 symlinks) | **5 dryfów → 0** (R1 fixed) |

ADR-005 (cross-profile boundaries): **respektowany** — każdy profil ma
unikalną pamięć (md5 różne), auth.json per profil, brak leak.

## Czy zaktualizować Standard / Skill / ADR?

- **Skill:** brak nowego skilla — audyt to procedura, można opisać w
  `skill-using-heos` jako workflow krok-po-kroku.
- **ADR:** rozważyć **ADR-012 — Cross-profile HEOS audit policy**,
  deklarującą że `tools/audit_cross_profile.py` (propozycja wyżej) ma
  być odpalane co tydzień (cron-style).
- **Standard:** STATUS.md powinien docelowo zawierać sekcję "Cross-profile
  status" z tabelą jak powyżej.
- **Lesson:** ten dokument wypełnia standard `Lessons Learned` po audycie
  HEOS 2026-08-01.

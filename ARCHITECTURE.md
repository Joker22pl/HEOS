# HEOS — Architektura

**Wersja:** v1.3.1
**Data:** 2026-07-28

> Patrz też: `CONSTITUTION.md` (zasady) · `STATUS.md` (stan) · `archive/00-HEOS-ARCHITECTURE-v1.1.md` (poprzednia wersja)

---

## 1. Architektura dwuwymiarowa (wprowadzona w v1.1, obowiązuje w v1.2)

```
HEOS/                                          [repo root]
│
├── CONSTITUTION.md            ← jedyne źródło zasad
├── ARCHITECTURE.md            ← ten plik
├── STATUS.md                  ← auto-generowany, snapshot stanu
├── README.md                  ← punkt wejścia
│
├── skills/                    ← wszystkie Skillsy (płasko)
│   ├── esp32-s3-micropython-blink.md
│   ├── using-heos.md
│   └── ...
│
├── decisions/                 ← ADR (płasko, NNN-tytuł.md)
│   ├── 001-micropython-esp32-s3-pico.md
│   └── ...
│
├── lessons/                   ← Lessons Learned (płasko)
├── checklists/                ← Checklisty (płasko)
├── playbooks/                 ← Playbooki (płasko)
│
├── templates/                 ← szablony 5 typów
│   ├── skill.md
│   ├── adr.md
│   └── ...
│
├── tools/                     ← narzędzia enforcement + migracji
│   ├── skill_audit.py
│   ├── heos_lint.py
│   ├── generate_registry.py
│   ├── generate_status.py
│   ├── lifecycle_audit.py
│   ├── heos_migrate.py
│   ├── update_frontmatter.py
│   ├── migrate_files.py
│   └── test_*.py
│
├── heos-migration/            ← infrastruktura migracji
│   ├── migration-map.json
│   ├── rollback.sh
│   └── README.md
│
├── archive/                   ← snapshot v1.1 (nieaktywny)
│
├── .registry.yaml             ← auto-generowany indeks artefaktów
├── .gitignore
└── STATUS.md                  ← auto-generowany
```

**Dwie osie:**

- **Oś A — typ artefaktu** (skills, decisions, lessons, checklists, playbooks, templates, tools)
- **Oś B — domena** (embedded, robotics, ai-ml, infrastructure, web) → **tag** w frontmatter (nie katalog)

Domena jako **tag**, nie jako katalog. Jeden artefakt może mieć wiele tagów. Przykład: `[embedded, esp32, micropython]`.

## 2. Powiązania między modułami

### 2.1 ADR ↔ Skills (relacja wiele-do-wielu)

Każdy Skill może mieć w frontmatter pole `related: [adr-001, skill-using-heos]`. Każdy ADR może być cytowany przez wiele Skillsów/ADR-ów.

**Walidacja:** `heos_lint.py` (reguła `BROKEN_REF`).

### 2.2 Skills ↔ Domeny (tag w frontmatter)

`tags: [embedded, esp32, micropython]` w frontmatter. Katalog `skills/` jest płaski.

**Walidacja:** `heos_lint.py` (typy tagów).

### 2.3 Lessons Learned ↔ ADR (relacja opcjonalna)

Docelowo każdy `lessons-learned/YYYY-MM-DD-X.md` może cytować ADR. Niekonieczne w v1.2.

### 2.4 Skill ↔ Tools (relacja enforcement)

Narzędzia w `tools/` czytają Skillsy z `skills/` i sprawdzają zgodność z szablonem.

### 2.5 Foundation ↔ wszystko (relacja nadrzędna)

`CONSTITUTION.md` jest konstytucją — wszystkie inne moduły muszą być z nią zgodne (ręczne review przy wprowadzaniu nowych zasad).

## 3. Przepływ danych

### 3.1 Nowy Skill

```
1. Sprawdź istniejące w `skills/` (nie duplikuj)
2. Wybierz tagi (domena + technologia)
3. Napisz SKILL.md z 7 obowiązkowymi sekcjami
4. Uruchom: skill_audit.py skills/  (musi ✅ PASS)
5. (opcjonalnie) Napisz ADR jeśli decyzja architektoniczna
6. Commit + push
7. Generuj .registry.yaml (cron lub ręcznie)
```

### 3.2 Nowa decyzja architektoniczna

```
1. Sprawdź czy już jest ADR na ten temat
2. Jeśli nie, napisz ADR z szablonu (decisions/NNN-tytuł.md)
3. Użyj `related:` w frontmatter jeśli są powiązania
4. Powiązane Skills dostaną cytat przez update_frontmatter (ręcznie lub skrypt)
5. heos_lint.py waliduje cross-refs
```

### 3.3 Tygodniowy audyt (cron)

```
Poniedziałek 9:00 UTC → cron job "HEOS Weekly Audit"
  → heos_weekly_audit.py
  → generuje STATUS.md
  → raport do Discord (ten wątek)
```

## 4. Mechanizmy Enforcement (5 narzędzi)

| Narzędzie | Co sprawdza | Kiedy |
|---|---|---|
| `tools/skill_audit.py` | Schema (7 obow. + 8 opcjon.) + Technical (treść) | per PR / co tydzień |
| `tools/heos_lint.py` | Cross-references, metadane, status | per PR / co tydzień |
| `tools/generate_registry.py` | Indeks artefaktów | co tydzień |
| `tools/generate_status.py` | Snapshot stanu | co tydzień + per commit |
| `tools/lifecycle_audit.py` | review_due, deprecated | co tydzień |

**Migracja** (jednorazowo): `tools/heos_migrate.py`, `tools/migrate_files.py`.

## 5. Macierz zależności modułów

| Kto zależy od kogo | 00-foundation | skills/ | decisions/ | templates/ | tools/ |
|---|---|---|---|---|---|
| **CONSTITUTION** | — | nie | nie | nie | nie |
| **skills** | ✅ czyta | nie (sąsiad) | ✅ cytuje | ✅ używa (szablon) | ✅ waliduje |
| **decisions** | ✅ czyta | ✅ cytuje | wewnętrznie | ✅ używa | ✅ waliduje |
| **templates** | ✅ czyta | nie (szablon dla) | nie (szablon dla) | wewnętrznie | nie |
| **tools** | ✅ czyta | ✅ czyta | ✅ czyta | nie | wewnętrznie |

Kluczowe: CONSTITUTION jest nadrzędna. Tools jest najbardziej zależna (czyta wszystko).

## 6. Model danych artefaktów

Wspólne metadane (każdy artefakt):

```yaml
type: <skill|adr|lessons|checklist|playbook>
id: <unikalne>
name: <kebab-case>
title: <czytelny>
status: <draft|proposed|reviewed|accepted|deprecated|archived>
owner: <gaja|joker>
created_at: <YYYY-MM-DD>
updated_at: <YYYY-MM-DD>
review_due: <YYYY-MM-DD>
version: <semver>
heos_standard_version: <1.2>
tags: [<domena>, <technologia>]
related: [<ref-do-innego-artefaktu>]

quality_schema: <pending|pass|fail>
quality_technical: <pending|pass|fail>
quality_operational: <unmeasured|fresh|proven>
```

**Specyficzne pola:**

- **Skill:** `when_to_use`, `when_not_to_use`, `workflow`, `examples`, `lessons_learned`
- **ADR:** `adr_number` (unikalne), `context`, `decision`, `consequences`, `alternatives`, `revision_trigger`
- **Lessons:** `what_worked`, `what_didnt`, `why`, `how_to_improve`, `follow_up`
- **Checklist:** `items` (lista `{id, text, required}`)
- **Playbook:** `goal`, `prerequisites`, `steps` (lista `{id, action, command?, expected_result?}`)

## 7. Lifecycle artefaktów (6-etapowy)

```
draft
  ↓ [autor: wszystkie pola wypełnione]
proposed
  ↓ [Schema Validation ✅]
reviewed
  ↓ [Technical Validation ✅ + jawna recenzja Jokera]
accepted
  ↓ [nowa wersja / zastąpienie / review_due minął]
deprecated
  ↓ [po 90 dniach od deprecated]
archived
```

Szczegóły w `CONSTITUTION.md`.

## 8. Granice HEOS

**HEOS NIE jest:**

- Systemem zarządzania projektami (to GitHub Projects)
- Hostingiem kodu (to repo `Joker22pl/<projekt>`)
- Systemem CI/CD (to GitHub Actions)
- Bazą runtime danych (to SQLite / pliki JSON w projektach)

**HEOS JEST:**

- Systemem wiedzy (standardy, szablony, wzorce)
- Systemem enforcement (audyt, lint, generacja)
- Cross-cutting dla wszystkich projektów Jokera

## 9. Profile Hermesa

| Profil | Właściciel | Przeznaczenie | HEOS |
|---|---|---|---|
| `gaja` | Joker | Osobista asystentka — projekty, roboty, code | ✅ pełne (CONSTITUTION obowiązuje) |
| `gaja-it` | (bot) | SysAdmin/DevOps — serwer, logi, troubleshooting | 🟡 subskrybuje standardy |
| `gaja-med` | Asia (lekarka) | Wspiera Asię klinicznie | 🟡 subskrybuje (ale swoje dane) |

**Granice (ADR-005):** HEOS NIE czyta pamięci innych profili. Profile mają własne Skillsy, HEOS dostarcza standardy.

## 10. Wzorce architektoniczne

| Wzorzec | Gdzie | Po co |
|---|---|---|
| ADR (Michael Nygard) | decisions/ | Persystencja decyzji |
| Knowledge Graph (docelowo) | .registry.yaml | Relacje między Skills/ADR/Lessons |
| Audit-driven development | tools/skill_audit.py | Enforcement nie Manifest |
| Convention over Configuration | szablon Skilla, format ADR | Mniej decyzji |
| Single Source of Truth | CONSTITUTION.md, .registry.yaml | Bez dryfu |
| Lifecycle z review_due | każdy artefakt | Auto-detekcja "zapomnianych" |

## 11. Co HEOS NIE robi (YAGNI)

- Mikroserwisy / rozproszone HEOS
- AI-assisted Skill authoring
- Plugin system
- Multi-language (polski + aliasy wystarczają)
- Własny język zapytań (YAML+markdown wystarczy)

## 12. Migracja v1.1 → v1.2 — podsumowanie

| Element | Przed | Po |
|---|---|---|
| Architektura | 2D (domena × typ) | 2D (domena jako tag × typ) |
| Struktura katalogów | 21 katalogów | ~11 |
| Plików | 33 | 9 artefaktów + templates + tools + heos-migration |
| Wersjonowanie | w nazwie (v1.1) | bez wersji w nazwie (CONSTITUTION.md) |
| ADR | w decision-records/ | w decisions/ (płasko) |
| Konstytucja | HEOS-MASTER-PROMPT-v1.1.md | CONSTITUTION.md |
| Architektura | 00-HEOS-ARCHITECTURE.md | ARCHITECTURE.md |
| Snapshot v1.1 | (brak) | archive/ (zachowany) |
| 3-poziomowa ocena Skills | (brak) | Schema + Technical + Operational |
| 6-etapowy lifecycle | (brak) | draft → proposed → reviewed → accepted → deprecated → archived |
| Status w metadanych | brak | required field |

Migracja: 33 operacje (15 move + 8 archive + 10 delete). Bramka walidacji: 7/7 ✅.

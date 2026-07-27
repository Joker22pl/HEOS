---
type: playbook
id: playbook-heos-new-skill
name: heos-new-skill
title: HEOS — tworzenie nowego skilla (krok-po-kroku)
status: accepted
owner: gaja
created_at: '2026-07-27'
updated_at: '2026-07-27'
review_due: '2027-01-25'
version: 1.0.0
heos_standard_version: '1.2'
tags:
- workflow
- authoring
related:
- skill-using-heos
quality_schema: pass
quality_technical: pass
quality_operational: fresh
last_verified: 2026-07-27
verified_on: HEOS audit (2026-07-27)
---

# Playbook: tworzenie nowego skilla HEOS

> Cel: **działający skill zgodny z HEOS v1.2**, przechodzący 7-etapowy
> pre-commit gate, bez konieczności poprawek po commicie.

## Kiedy stosować

- ✅ Użytkownik potrzebuje nowego procedurę (np. „debug X", „konfiguruj Y")
- ✅ Istniejący skill jest przepełniony (>500 linii) → wydzielić subskill
- ❌ NIE dla runtime Skills profilu Hermesa (te mają inny format)

## Kroki

### 1. Wybierz lokalizację

- Plik `.md`: `skills/<name>.md` (proste skille, <200 linii)
- Katalog `SKILL.md`: `skills/<name>/SKILL.md` (złożone skille, + `references/`, `scripts/`)

**Reguła decyzyjna:**
- < 200 linii + brak references → plik
- > 200 linii LUB ma references/scripts → katalog

### 2. Skopiuj template

```bash
cp templates/skill.md skills/<name>.md       # lub skills/<name>/SKILL.md
```

Wypełnij 12 pól frontmatter HEOS v1.2:
`type`, `id`, `name`, `title`, `status: draft`, `owner`, `created_at`, `updated_at`,
`review_due: $(date -d '+6 months' +%Y-%m-%d)`, `version: 0.1.0`,
`heos_standard_version: "1.2"`, `tags`, `related`, `quality_*`.

### 3. Napisz 7 obowiązkowych sekcji

| Sekcja | Minimalna długość | Cel |
|---|---|---|
| **Cel** | 1-2 zdania | Co skill robi |
| **Zakres** | 2-5 zdań | Granice zastosowania |
| **Kiedy używać** | 5+ bulletów | Trygery / symptomy |
| **Kiedy nie używać** | 3+ bulletów | Anty-patterns |
| **Workflow** | 3+ kroki | Procedura |
| **Przykłady** | 2+ use-case'y | Z **co najmniej 1 blokiem ` ```bash `** |
| **Lessons Learned** | 3+ bullets | Wnioski z runtime |

### 4. Walidacja lokalna (7-etapowy gate)

```bash
python3 tools/skill_audit.py skills/<name>.md --level all --quiet
python3 tools/heos_lint.py
python3 tools/lifecycle_audit.py --quiet
```

Jeśli wszystkie PASS → kontynuuj. W przeciwnym razie → napraw braki.

### 5. Cross-references

Dodaj `related:` wskazujące na powiązane artefakty (HEOS lint sprawdza):

```yaml
related:
- adr-005                  # jeśli dotyczy granic profili
- skill-using-heos         # jeśli dotyczy HEOS
```

**Symetria:** Jeśli A → B, to B → A (HEOS lint tego nie sprawdza, ale dobry
practice). Użyj `tools/check_asymetry.py` (jeśli dostępne) lub ręcznie.

### 6. Most do profilu Hermesa (jeśli runtime skill)

Jeśli skill jest używany przez profil Hermesa:

```bash
SKILL_NAME=<name>
TARGET=/home/gaja/gaja-projekty/HEOS/skills/${SKILL_NAME}.md  # lub /<dir>/SKILL.md
LINK_DIR=/home/gaja/.hermes/profiles/gaja/skills/<category>/${SKILL_NAME}
mkdir -p "$LINK_DIR"
ln -sfn "$TARGET" "$LINK_DIR/SKILL.md"
```

Walidacja: `python3 -c "from tools.skills_tool import skill_view; import json; print(json.loads(skill_view('${SKILL_NAME}') or '{}').get('success'))"`

### 7. Regeneruj artefakty + commit

```bash
python3 tools/generate_registry.py
python3 tools/generate_status.py
git add skills/<name>.md .registry.yaml STATUS.md
git commit -m "[skill] <name> v0.1.0 — <krótki opis>"
```

Push po weryfikacji 7/7 gate.

## Kryteria ukończenia (Definition of Done)

- [ ] Skill w `skills/<name>.md` LUB `skills/<name>/SKILL.md`
- [ ] Frontmatter ma wszystkie 12 pól HEOS v1.2
- [ ] 7 obowiązkowych sekcji obecnych, każda z minimalną treścią
- [ ] Co najmniej 1 blok ` ```bash ` w Przykładach (Technical PASS)
- [ ] `skill_audit.py --level all` → Schema PASS + Technical PASS
- [ ] `heos_lint.py` → 0 findings
- [ ] `lifecycle_audit.py --quiet` → review_due > today
- [ ] Cross-references symetryczne (jeśli A → B to B → A)
- [ ] Most do profilu Hermesa (jeśli runtime)
- [ ] `generate_registry.py` + `generate_status.py` uruchomione
- [ ] Committed z message wg ADR-003 (`[skill] <name> v0.1.0 — <opis>`)

## Antywzorzec

- ❌ Skill bez 7 obowiązkowych sekcji (Schema FAIL)
- ❌ Skill bez code block (Technical FAIL)
- ❌ Skill bez `related:` (linter warning)
- ❌ Skill z `quality_*` = `pending` po audycie (znaczy że nie uruchomiono `update_quality.py`)
- ❌ Skill w `joker-deliverables/` lub `archive/` (poza scope)
- ❌ Skill z referencją do `id` którego nie ma (BROKEN_REF)

## Powiązane

- `templates/skill.md` — template
- `tools/skill_audit.py` — audytor
- `tools/heos_lint.py` — walidator cross-refs
- `decisions/005-granice-profili-hermes.md` — HEOS vs profil Hermesa
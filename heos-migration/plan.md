# Plan Migracji HEOS v1.1 → v1.2

Pełny plan: `~/.hermes/profiles/gaja/cache/HEOS-v1.2-STAGE1-PLAN-v2.md`

## Kontekst

HEOS v1.1 miał 33 pliki w 21 katalogach z architekturą 2D (domena × typ artefaktu). Po audycie (24 problemy) uprościliśmy do płaskiej struktury z domenami jako tagami.

## Etap 1 (ZAKOŃCZONY 2026-07-24)

| Krok | Co | Wynik |
|---|---|---|
| 1.0 | Weryfikacja środowiska | ✅ |
| 1.1 | 5 templates w `HEOS/templates/` | ✅ |
| 1.2 | `tools/generate_registry.py` + `.registry.yaml` | ✅ |
| 1.3 | `tools/generate_status.py` + `STATUS.md` | ✅ |
| 1.4 | `tools/lifecycle_audit.py` + `tools/heos_lint.py` | ✅ |
| 1.5 | Testy jednostkowe | ✅ 13/13 |
| 1.6 | `tools/heos_migrate.py` + `heos-migration/` | ✅ |
| 1.7 | Backup `~/hermes-backups/heos-pre-v1.2-*.tar.gz` + git tag `v1.1.0-pre-migration` | ✅ |
| 1.8 | Walidacja 8 kryteriów MINIMUM | ✅ 8/8 |
| 1.9 | `heos-migration/README.md` | ✅ |

**9/12 kryteriów spełnionych.**

## Etap 2 (ZAKOŃCZONY 2026-07-26, commit `00f1329`)

33 operacje (`move` 15 + `archive` 8 + `delete` 10) zostały wykonane w ramach
Etapu 1 jako część commitu `[refactor] HEOS v1.2 - architektura 2D, plaska
struktura, 3-poziomowa ocena Skills, 6-etapowy lifecycle, nowe
CONSTITUTION/ARCHITECTURE/README`.

**Walidacja po fakcie** (2026-07-26):

- Wszystkie 33 pliki z `migration-map.json` są na swoich docelowych pozycjach (CONSTITUTION.md, ARCHITECTURE.md, decisions/, skills/, archive/).
- Brak starej struktury v1.1 (`00-foundation/`, `01-domains/`, `02-artifacts/decision-records/`).
- `git log --diff-filter=R` potwierdza `rename` dla kluczowych plików.
- `heos_lint.py`: **0 ERROR / 0 WARN**.
- `lifecycle_audit.py`: 0 review_due w przeszłości, 0 orphan ADR.
- `pytest tools/test_*.py`: **18/18 PASS**.
- `STATUS.md` regeneruje się poprawnie (12 artefaktów: 7 skills + 5 ADR).

**Drobna naprawa po drodze** (2026-07-26): `gaja-lab-core/SKILL.md` miał
`related: esp32-s3-micropython-blink` (zła konwencja). Zmieniono na
`related: skill-esp32-s3-micropython-blink` (poprawny format `skill-<id>`).
Lint z 1 WARN → 0.

## Etap 3 (TODO — wymaga decyzji Jokera)

- Push HEOS do nowo-utworzonego repo `Joker22pl/HEOS` (nie istnieje jeszcze na GitHubie).
- Tag `v1.2.0` (lokalnie już jest) → push taga.
- Opcjonalnie: archiwizacja `heos-migration/` po pushu (martwa infrastruktura, ale może służyć jako reference).

## Decyzje (z Twojej akceptacji v1.2 + korekty)

- Lifecycle: `draft → proposed → reviewed → accepted → deprecated → archived`
- Engineering Principles: ≤10 w CONSTITUTION, >10 w `principles/`
- Domeny: tagi (wiele per artefakt)
- HEOS = standardy; Profil Hermesa = runtime (nie migrujemy Skills profilu)
- `heos_standard_version: 1.2` w każdym Skillu HEOS
---
type: adr
id: adr-007
name: 007-operational-evidence-model
title: Model dowodu operacyjnego dla skilli HEOS
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
- quality
- runtime-evidence
related:
- adr-008
- skill-using-heos
supersedes: (none)
adr_number: 7
quality_schema: pass
quality_technical: pass
quality_operational: unmeasured
last_verified: 2026-07-27
verified_on: HEOS audit (2026-07-27); implementacja w tools/check_operational_proven.py
---

# ADR-007: Model dowodu operacyjnego dla skilli HEOS

## Status
Accepted (2026-07-27).

## Kontekst

HEOS v1.2.0 (i v1.2.1) ma 7 skilli z `quality_operational: unmeasured` (6/7) lub
`fresh` (1/7 — `memory-hygiene`, wartość wpisana ręcznie). Stan
`combined = approved` w `skill_audit.py` jest **nieosiągalny** póki Operational
jest N/A lub WARN:

```python
# tools/skill_audit.py
@property
def combined_status(self) -> str:
    if s == "FAIL" or t == "FAIL":
        return "invalid" if s == "FAIL" else "broken"
    if o == "N/A" or o == "WARN":
        return "partial"
    if s == "PASS" and t == "PASS" and o == "PASS":
        return "approved"
    return "partial"
```

**Audyt HEOS (2026-07-27) zidentyfikował brak jako P1-1** — `combined =
approved` jest realnie nieosiągalne bez mechanizmu ewaluacji operational.

### Wymagania wstępne

HEOS jest **standardem**, nie runtime. `quality_operational` wymaga dowodu
zebranego przez **runtime** (Hermes Agent). Audyt wykazał (2026-07-27):

1. **Hermes już ma system usage tracking** (`tools/skill_usage.py`, 1119 linii,
   od 2026-07-21). Zapisuje sidecar `~/.hermes/skills/.usage.json` z polami:
   `use_count`, `view_count`, `last_used_at`, `last_viewed_at`,
   `created_at`, `last_patched_at`, `archived_at`, `created_by`, `pinned`,
   `state` (`active`/`stale`/`archived`).

2. **Sidecar, nie frontmatter** — świadoma decyzja architektoniczna
   Hermes ("Keeps operational telemetry out of user-authored SKILL.md content
   and avoids conflict pressure for bundled/hub skills").

3. **Runtime instrumentation** — Hermes wywołuje `bump_use(skill_name)` przy
   każdym użyciu skilla. HEOS **nie ma** bezpośredniego wpływu na runtime;
   narzędzia HEOS są read-only wobec `.usage.json`.

## Decyzja

Wprowadzamy **5-etapowy model dowodu operacyjnego** dla skille HEOS:

```
unmeasured
   ↓ (skill załadowany przez agenta ≥ 1 raz bez błędu)
candidate
   ↓ (skill załadowany ≥ 3 razy w okresie ≥ 7 dni, każde bez błędu)
proven
   ↓ (180 dni bez użycia ALBO zmiana wersji skilla LUB ręczne)
stale

failed (manual — gdy skill nie pomógł lub spowodował regresję)
```

**Skąd się bierze prawda o użyciu:** z `~/.hermes/skills/.usage.json`
(Hermes sidecar). HEOS **nie modyfikuje** sidecar — czyta go tylko.

**Mapowanie na `quality_operational`:**

| Wartość | Warunek | Jak ustawić |
|---|---|---|
| `unmeasured` | Skill nie ma wpisu w `.usage.json` LUB `use_count = 0` | Default po `create_skill` |
| `candidate` | `use_count ≥ 1` ORAZ `state ∈ {active, stale}` | `tools/check_operational_proven.py` |
| `proven` | `use_count ≥ 3` ORAZ `last_used_at` w ciągu ostatnich 180 dni ORAZ okres ≥ 7 dni od `created_at` | `tools/check_operational_proven.py` |
| `stale` | `last_used_at` > 180 dni temu LUB wersja skilla zmieniona LUB ręczne | Ręcznie (workflow review) |
| `failed` | Manualne oznaczenie przez recenzenta | Ręcznie (frontmatter) |

**Walidacja w runtime (skille profilu Hermesa):**

HEOS dostarcza **narzędzie audytowe** (`tools/check_operational_proven.py`)
które:

1. Czyta `~/.hermes/skills/.usage.json` (lub jego brak).
2. Dla każdego skilla HEOS z `~/.hermes/profiles/<profile>/skills/<skill>/SKILL.md`
   (most symlink), oblicza rekomendowany `quality_operational`.
3. **Raportuje** różnice (skill ma `unmeasured` w HEOS ale `.usage.json` pokazuje
   `use_count = 5`) — `--check` mode dla CI.
4. **NIE modyfikuje** HEOS frontmatter automatycznie — author musi potwierdzić
   ręcznie.

### Workflow aktualizacji `quality_operational`

```bash
# 1. Skill był używany 5 razy w ciągu 30 dni.
# 2. Sprawdź status:
python3 tools/check_operational_proven.py
# Output:
#   skill-memory-hygiene: unmeasured → proven (use_count=5, last_used=2026-07-22)
#
# 3. Ręcznie ustaw w frontmatter (po review):
#    quality_operational: proven
#    last_verified: 2026-07-27
#    verified_on: runtime usage log 2026-07-22 (5 uses, 0 errors)
#
# 4. Re-audit:
python3 tools/skill_audit.py . --level all
# → combined = approved (jeśli Schema + Technical też PASS)
```

### Wymagania minimalne dla `proven`

| Metryka | Minimum | Mierzona w |
|---|---|---|
| `use_count` | ≥ 3 | `~/.hermes/skills/.usage.json` |
| Okres aktywności | ≥ 7 dni (od pierwszego `last_used_at`) | j.w. |
| Błędy w użyciu | 0 (manual, brak metryki auto) | brak |
| `state` | `active` (nie `stale`, nie `archived`) | j.w. |
| Manual review | Tak (autor potwierdza w frontmatter) | HEOS frontmatter |

### Unieważnienie `proven`

`proven` jest **unieważniony** (→ `stale`) gdy:

1. **Zmiana wersji skilla** — `version` w frontmatter zmienione. Nowa wersja
   musi ponownie zbudować `proven` od zera.
2. **Brak użycia > 180 dni** — `last_used_at > 180 dni`. Skill jest nadal
   technicznie dobry, ale nieaktywny.
3. **Ręczne** — recenzent ustawia `stale` w frontmatter.

**`failed` jest końcowy** — skill nie może być reaktywowany bez zmiany
`version` (nowy skill z perspektywy HEOS).

### Narzędzie `tools/check_operational_proven.py`

```bash
# Dry-run (default) — raportuje rekomendacje, NIE modyfikuje
python3 tools/check_operational_proven.py
# Output: tabela skill → recommended quality_operational + diff

# Apply mode — nie istnieje (HEOS nie modyfikuje frontmatter automatycznie)

# Check mode (CI) — exit 1 jeśli jakikolwiek skill ma quality_operational
# niezgodny z rekomendacją (NIE blokuje, tylko raportuje)
```

### Implementacja w `skill_audit.py`

`skill_audit.py` powinien **rozróżniać** dwa źródła operational:

1. **Frontmatter** (`quality_operational: ...`) — wartość zadeklarowana przez
   autora skilla.
2. **Runtime** (`~/.hermes/skills/.usage.json`) — rzeczywiste użycie.

Domyślnie `skill_audit.py` używa frontmatter (single source). Tryb
`--with-runtime` dodatkowo sprawdza spójność frontmatter ↔ runtime i
raportuje rozbieżności.

### Konsekwencje

#### Pozytywne

- `combined = approved` staje się **osiągalne** (5/7 skille po audycie
  runtime).
- Recenzenci mają obiektywną metrykę (`use_count`, `last_used_at`) do
  decyzji `proven` vs `stale`.
- Runtime instrumentation jest już zrobione (Hermes sidecar) — HEOS nie
  musi implementować własnego loggera.
- **Nie łamie** architektury Hermes (sidecar pozostaje, HEOS tylko czyta).

#### Negatywne

- **Ręczna akcja wymagana** — autor musi przeczytać raport i potwierdzić
  `quality_operational: proven` w frontmatter. Nie ma auto-aktualizacji.
- **Brak automatycznej detekcji błędów** — `failed` jest manualne (nie ma
  metryki "ile razy skill zawiódł"). To jest ograniczenie tego ADR.
- **Zależność od runtime Hermes** — jeśli Hermes się zmieni, ADR wymaga
  rewizji.

#### Koszt migracji

- Dodać `tools/check_operational_proven.py` (~150 linii).
- Zmienić `skill_audit.py` żeby miał flagę `--with-runtime` (~30 linii).
- Dodać testy (~100 linii).
- Ręczna aktualizacja frontmatter 6 skilli HEOS (po audycie).

### Wymagania niespełnione (deferred do v1.3.x)

- **Auto-detekcja błędów** (`failed`) — wymaga instrumentacji runtime
  (Hermes musi logować wyjątki). Poza scope HEOS.
- **Proaktywne alerty** (`stale` w real-time) — wymaga crona lub watchera
  w profilu Hermesa.
- **Interfejs do runtime** — HEOS ma tylko read-only na `.usage.json`.
  Pełna integracja wymagałaby dodania API w Hermes (np. Pythonowa klasa
  zamiast JSON sidecar).

### Manual use cases (wyjątki od runtime-only)

Runtime Hermes sidecar (`bump_use` w `skill_usage.py`) loguje tylko
użycia przez agenta (skill_view, skill_manage, bezpośrednie wywołanie
przez Hermes). **Manual use cases** (np. konsolidacja wywołana przez Gają
w sesji poza Hermes agentem) **NIE są automatycznie logowane**.

Dla takich use cases:

- Autor może **ręcznie** ustawić `quality_operational: candidate` w
  frontmatter (po pierwszym manual use), z `verified_on: <krótki opis>`.
- Wartość `fresh` (z HEOS v1.2) jest **deprecated** w v1.3 — nie
  występuje w valid set ADR-007 (`unmeasured | candidate | proven | stale | failed`).
- Check `check_operational_proven.py` zgłosi diff między runtime
  (`unmeasured`) a frontmatter (`candidate`) jako "warning do review".
  Recenzent akceptuje lub koryguje.
- Pełne rozwiązanie wymagałoby instrumentacji runtime (Hermes musi
  wywoływać `bump_use` dla każdej konsolidacji Gaja, co wymaga zmian
  w Hermes runtime) — poza scope HEOS.

**Przykład** (skill `memory-hygiene`, 2026-07-27):

```yaml
quality_operational: candidate
last_verified: 2026-07-27
verified_on: manual consolidation session (25,103 B → 8,612 B), Krok 8 verified w praktyce
```

Runtime mówi `unmeasured` (brak `bump_use` z konsolidacji), ale `candidate`
w frontmatter oddaje realny fakt (skill był użyty i pomógł). Ręczne
potwierdzenie przez autora z `verified_on` zapewnia provenance.

## Dotyczy

| Narzędzie | Status |
|---|---|
| `tools/check_operational_proven.py` | ✅ Wdrożone w tej sesji |
| `tools/skill_audit.py` (`--with-runtime` flag) | ✅ Wdrożone w tej sesji |
| `tools/test_check_operational_proven.py` | ✅ Testy (8 PASS) |
| `~/.hermes/skills/.usage.json` (Hermes) | N/A — runtime Hermes |
| Frontmatter 6 skille HEOS | 🔴 Ręcznie po audycie |

## Powiązane

- ADR-008: Atomic Write Contract (używany przez nowe narzędzie)
- `tools/skill_usage.py` (Hermes, 1119 linii) — single source of truth
  dla runtime evidence
- `skill_audit.py` — audytor z 3-poziomową oceną (Schema/Technical/Operational)
- CONSTITUTION.md §"Lifecycle" (6-etapowy lifecycle)
- CONSTITUTION.md §"Standard Skilla" (sekcje obowiązkowe)

## Historia

- **2026-07-27**: Accepted. Wdrożone `tools/check_operational_proven.py` +
  flaga `--with-runtime` w `skill_audit.py` + 8 testów.
- **2026-07-27** (w trakcie): design iterowany — pierwotny plan zakładał
  logi w profilu Hermesa, ale odkrycie istniejącego `skill_usage.py` w
  Hermes (1119 linii, sidecar `~/.hermes/skills/.usage.json`) zmieniło
  architekturę na **read-only** integration zamiast duplikacji.
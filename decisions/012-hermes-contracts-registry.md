---
# === Wspólne metadane (wymagane) ===
type: adr
id: adr-012
name: 012-hermes-contracts-registry
title: Rejestracja namespace `hermes.*` i wspólnych kontraktów Gaja Desk
status: accepted
owner: gaja
created_at: '2026-08-03'
updated_at: '2026-08-03'
review_due: '2027-02-03'
version: 1.0.0
heos_standard_version: "1.2"
tags:
- cross-cutting
- contracts
- gaja-desk
related:
- adr-005
- adr-007
- skill-using-heos
# === Specyficzne dla ADR ===
adr_number: 12
superseded_by: (none)

# === Jakość ===
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---

# ADR-012: Rejestracja namespace `hermes.*` i wspólnych kontraktów Gaja Desk

## Status

Accepted (2026-08-03) — zaakceptowany przez Jokera. Rejestruje namespace `hermes.*`
jako oficjalną przestrzeń wspólnych kontraktów ekosystemu Hermesa. Pierwotnie
przygotowany jako propozycja projektu `gaja-desk` (`docs/heos/012-hermes-contracts-registry.md`),
przeniesiony do HEOS po akceptacji.

## Kontekst

Projekt **Gaja Desk** (lokalny Control Plane ekosystemu Hermes) musi wymieniać
zdarzenia decyzji i higieny między komponentami. Prompt główny projektu wymaga użycia
kanonicznych kontraktów:

- `hermes.agent-manifest.v1`
- `hermes.memory-entry.v1`
- `hermes.event-envelope.v1`

oraz zdefiniowania kontraktów MVP:

- `hermes.decision-request.v1`
- `hermes.decision-resolution.v1`
- `hermes.hygiene-snapshot.v1`

**Baseline GDL0 (`gaja-desk/docs/baseline/GDL0-INTEGRATION-BASELINE.md`) wykazał,
że żaden z tych kontraktów nie istnieje** w repozytoriach ekosystemu (gaja-projekty,
HEOS, HIVE, HARE, Hermes runtime) — 0 trafień na `hermes.event-envelope`,
`agent-manifest`, `memory-entry` w źródłach. Brak kanonicznego źródła = nie wolno
deklarować fikcyjnej zgodności.

## Decyzja

1. **Rejestrujemy namespace `hermes.*` w HEOS** jako oficjalną przestrzeń wspólnych
   kontraktów między komponentami ekosystemu (Hermes runtime, Gaja Desk, HARE, HIVE, HEOS, Themis).
2. **Powołujemy `hermes.event-envelope.v1` jako kanoniczną kopertę zdarzeń** — semantyczne
   odpowiedniki: `event_id`, `event_type`, `event_version`, `occurred_at`, `producer`
   (Agent Manifest v1), `subject`, `correlation_id`, `causation_id`, `payload_schema`, `payload`.
3. **Powołujemy `hermes.agent-manifest.v1`** jako opis producenta zdarzeń
   (`agent_id`, `instance_id`, wersja, zdolności do uzupełnienia w Horyzoncie 1).
4. **Powołujemy `hermes.memory-entry.v1`** jako kontrakt wpisu pamięci (przegląd/
   propozycje zmian w Horyzoncie 4) — rejestracja wyprzedzająca, wersja robocza.
5. **Kontrakty MVP Gaja Desk** (`decision-request.v1`, `decision-resolution.v1`,
   `hygiene-snapshot.v1`) pozostają `proposed` w `contracts/jsonschema/` z pełnym
   JSON Schema Draft 2020-12, przykładami valid/invalid i wektorem digestu RFC 8785.
6. **Do czasu natywnego transportu** Gaja Desk używa adaptera przejściowego
   `file-spool-v1` (ADR-0007 projektu), jawnie oznaczając, że nie jest to kanoniczny
   `event-envelope.v1`.
7. **Polityka wersjonowania:** każdy schema ID niemutowalny po wydaniu; breaking change
   tworzy `v2` z okresem dual-read/dual-write i terminem wycofania v1.

## Uzasadnienie

| Kryterium | Rejestracja w HEOS | Lokalne kontrakty w gaja-desk |
|---|---|---|
| Jedno źródło prawdy kontraktów | ✅ | ❌ duplikacja ryzyka |
| Współdzielenie przez HIVE/HARE/Themis | ✅ możliwe | ❌ wymaga importu z gaja-desk |
| Zgodność z promptem głównym (kanoniczne źródło) | ✅ | ❌ łamie GDL-ARC-007 |
| Szybkość MVP | nieco wolniej (akceptacja) | ✅ od razu |
| Ryzyko rozjazdu kontraktów | niskie | wysokie w dłuższej perspektywie |

Namespace `hermes.*` należy do ekosystemu Hermesa, nie do pojedynczego projektu.
Gaja Desk jest pierwszym konsumentem; rejestracja w HEOS chroni przed powstaniem
konkurencyjnych definicji.

## Konsekwencje

**Pozytywne:**

- Kanoniczne źródło kontraktów dla wszystkich komponentów.
- Gaja Desk może deklarować zgodność z `hermes.event-envelope.v1` zamiast adaptera przejściowego.
- Jasna polityka wersjonowania dla przyszłych zmian.
- Odblokowanie etapu GDL1 projektu gaja-desk (ADR-0005 przestaje być blokerem).

**Negatywne / ryzyka:**

- Kontrakty `proposed` nie są jeszcze globalnie zaakceptowane; implementacja producenta
  i konsumenta musi używać dokładnie tej samej przypiętej wersji.
- Rejestracja wyprzedza gotowość HARE do natywnego transportu (Horyzont 1 roadmapy gaja-desk).
- Wymaga pilnowania, by nowe komponenty nie tworzyły konkurencyjnych definicji `hermes.*`.

## NIE obejmuje (anty-scope-creep)

- ~~Pełnych definicji JSON Schema w HEOS~~ — kanoniczne definicje pozostają w
  `gaja-desk/contracts/jsonschema/` do czasu formalnego procesu publikacji kontraktów.
- ~~Wymuszenia użycia kontraktów w HARE/HIVE/Themis~~ — rejestracja jest deklaratywna;
  adopcja następuje w Horyzoncie 1.
- ~~Zmiany kontraktów Hermesa upstream~~ — jeśli upstream dostarczy własne definicje,
  przechodzimy na nie (sekcja Kiedy rewizja).

## Alternatywy rozważone

- **Brak rejestracji, kontrakty tylko lokalnie** — odrzucone: łamie GDL-ARC-007,
  grozi konkurencyjnymi definicjami w HARE/HIVE.
- **Czekanie na kontrakty Hermesa z upstream** — odrzucone: nie istnieją dziś i nie
  ma harmonogramu; Gaja Desk nie może czekać.
- **Namespace `gaja-desk.*` zamiast `hermes.*`** — częściowo przyjęte: read modele
  lokalne (`today-view`, `audit-event`, `problem`) zostają w `gaja-desk.*`; kontrakty
  między komponentami idą do `hermes.*`.

## Kiedy rewizja

- **2027-02-03** (review_due). Sprawdzić czy:
  - upstream Hermes dostarczył własne `agent-manifest`/`event-envelope` — jeśli tak,
    przejść na nie i wycofać lokalne propozycje;
  - HARE uzyskał natywny transport zdarzeń — jeśli tak, migracja z `file-spool-v1`;
  - kontrakty MVP zostały zaakceptowane poza `proposed`.

## Lessons Learned

**Namespace kontraktów międzykomponentowych powinien być rejestrowany centralnie
w HEOS od pierwszego dnia.** Gaja Desk wykrył brak `hermes.*` dopiero w baseline GDL0;
rejestracja wyprzedzająca (nawet z kontraktami `proposed`) chroni przed powstaniem
lokalnych, konkurencyjnych definicji i pozwala innym komponentom adoptować kontrakty
przez przypięcie tej samej wersji.

## Powiązane

- Projekt `gaja-desk`: `docs/adr/0005-hermes-contracts-versioning.md`
- Baseline: `gaja-desk/docs/baseline/GDL0-INTEGRATION-BASELINE.md` §3
- Kontrakty: `gaja-desk/contracts/jsonschema/` (6 schematów, status proposed)
- Roadmapa: Horyzont 1 — natywne API/events HARE, provider HIVE/HEOS

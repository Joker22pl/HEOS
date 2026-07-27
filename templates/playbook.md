---
# === Wspólne metadane (wymagane) ===
type: playbook
id: playbook-<krotki-tytul>
name: <krotki-tytul-kebab-case>
title: <Tytuł playbooka — cel proceduralny>
status: draft
owner: gaja
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
review_due: YYYY-MM-DD
version: 0.1.0
heos_standard_version: "1.2"
tags: [<kontekst>]

# === Specyficzne dla Playbook ===
goal: "Jedno zdanie: co osiągniemy po wykonaniu tego playbooka"

# === Jakość ===
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---

# Playbook: <tytuł>

**Cel:** <jeden cel proceduralny>
**Czas estymowany:** [X minut / godzin / dni]
**Wymaga:** [co user musi mieć przed startem]

## Prerequisites (przed startem)

- [wymaganie 1: np. "Python 3.11+ zainstalowany"]
- [wymaganie 2: np. "dostęp do sieci wewnętrznej"]
- [wymaganie 3: np. "backup bazy danych zrobiony"]

## Kroki

### Krok 1: <tytuł>

```bash
# komenda
```

**Oczekiwany rezultat:** [co powinno się stać]

**Co jeśli błąd:** [jak recovery]

### Krok 2: <tytuł>

```bash
# komenda
```

**Oczekiwany rezultat:** [co powinno się stać]

### Krok 3: <tytuł>

[...]

## Weryfikacja końcowa

- [ ] [kryterium sukcesu 1]
- [ ] [kryterium sukcesu 2]

## Rollback

[Jak cofnąć zmiany jeśli coś poszło nie tak. Konkretne komendy.]

## Powiązane

- [skill-X: używany w trakcie]
- [ADR-NNN: dlaczego tak robimy]
- [checklist-Y: weryfikacja po playbooku]

---
# === Wspólne metadane (wymagane w każdym artefakcie) ===
type: skill
id: skill-<kebab-case-name>
name: <kebab-case-identyfikator>
title: <Tytuł czytelny dla człowieka>
status: accepted                # accepted | deprecated | archived
owner: gaja
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
review_due: YYYY-MM-DD
version: 0.1.0
heos_standard_version: "1.2"
tags: [<domena>, <technologia>, runtime]
related: [<ref-do-innego-artefaktu>]

# === Runtime Skill specyficzne ===
skill_kind: runtime             # runtime | wzorcowy (HEOS Skill używa "wzorcowy" bez tego pola)

# === Jakość (runtime Skills — mniej wymagające) ===
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---

# <Tytuł Runtime Skilla>

## Cel

[1-2 zdania: co ten Skill robi w runtime (używany przez agenta w trakcie sesji)]

## Zakres

**W zakresie:**
- [konkretne zastosowania runtime]

**Poza zakresem:**
- [co NIE powinno używać tego skilla]

## Kiedy używać

- ✅ [trigger condition 1]
- ✅ [trigger condition 2]

## Kiedy nie używać

- ❌ [anti-pattern 1]

## Workflow (opcjonalny)

[Kroki procedury - nie obowiązkowe dla runtime Skills]

## Przykłady (opcjonalne)

```bash
# Przykład użycia
```

## Lessons Learned (wymagane dla runtime Skills)

**To jedyna obowiązkowa sekcja "wiedzy" dla runtime Skills.** Opisz:

- Co działa w runtime (jakieś wzorce, komendy, flow)
- Co nie działa (pułapki, edge cases)
- Jak rozwiązać typowe problemy

## Typowe błędy (opcjonalne)

- [błąd 1 + fix]
- [błąd 2 + fix]

## Debugging (opcjonalne)

| Objaw | Przyczyna | Fix |
|---|---|---|
| [objaw] | [przyczyna] | [fix] |

## Powiązane

- [ADR-NNN: jeśli dotyczy]
- [skill-X: jeśli powiązane]

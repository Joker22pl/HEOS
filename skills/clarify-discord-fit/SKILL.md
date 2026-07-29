---
name: clarify-discord-fit
description: Use before clarify tool call when Discord 2000 chars limit may bite. Load ONLY when preparing clarify.
type: skill
id: skill-clarify-discord-fit
title: Clarify tool — Discord-fit
status: accepted
owner: gaja
created_at: '2026-07-29'
updated_at: '2026-07-29'
review_due: '2027-01-25'
version: 1.0.0
heos_standard_version: "1.2"
tags:
- workflow
- joker
- communication
- discord
related:
- skill-using-heos
- lessons-2026-07-27-heos-audit-fix-bug
quality_schema: pass
quality_technical: pass
quality_operational: unmeasured
---

# Clarify tool — Discord-fit

> **Reguła:** `clarify` = pytanie + opcje. Kontekst (jeśli długi) = osobna wiadomość przed `clarify`.

## Cel

Wymusza wzorzec użycia `clarify` tool który mieści się w Discord 2000 chars limit i zachowuje pełną informację (pytanie + opcje + kontekst osobno). Stosuj **zawsze** przed `clarify` z 3+ opcjami lub gdy łączny raport + pytanie > 1500 chars.

## Zakres

**W zakresie:**
- Formatowanie `clarify` calls w środowisku Discord (limit 2000 chars na wiadomość)
- Splitting długich wiadomości (kontekst osobno + pytanie osobno)
- Konwencje severity (🔴🟠🟡✅) dla raportów + decision walks
- Max 4 opcje w `clarify` (Discord UI limit)

**Poza zakresem:**
- Treść samej decyzji (Co wybrać? to nie ten skill)
- Komunikacja poza Discord (Telegram, CLI, itp.)
- Decyzje gdzie jest tylko 1 opcja (użyj `pytanie tak/nie` bez `clarify`)

## Kiedy używać

- ✅ Zawsze przed `clarify` z 3+ opcjami
- ✅ Gdy raport + pytanie razem > 1500 chars (safety margin)
- ✅ Przy decision walk (>5 pozycji w raporcie)
- ✅ W sesjach z HEOS standard `related:` cross-references (zawsze raportuj decyzje przez `clarify`)

## Kiedy nie używać

- ❌ Dla pojedynczego pytania tak/nie (mieści się zawsze)
- ❌ Dla 2 opcji (mieści się zawsze)
- ❌ W trybie "non-interactive" (cron job, automated run)
- ❌ Gdy Joker mówi wprost "nie pytaj tylko rób" (per kolaboracja-joker-gaja)

## Format

### Wiadomość 1 (kontekst, opcjonalna)

Jeśli **Joker potrzebuje kontekstu** do podjęcia decyzji (>300 chars łącznie):

```markdown
[Topic emoji] [Jedno zdanie o czym jest raport/pytanie]

🔴 P0 (N):
- [item 1 — max 80 chars]
- [item 2 — max 80 chars]

🟠 P1 (N):
- [item 1 — max 80 chars]

✅ OK (N): [jeden string, max 80 chars]

Szczegóły: [ścieżka pliku / URL / "patrz dalej"]
```

**Hard limits:**
- Max 1500 chars łącznie (zostaje margines dla `clarify`)
- Każdy item: 80 chars max
- Emoji severity: 🔴🟠🟡✅ (4 poziomy)
- N = liczba items

### Wiadomość 2 (clarify — obowiązkowa)

```python
clarify(
    question="[Jedno pytanie, max 100 chars]",  # pytanie BEZ kontekstu
    choices=[
        "[Opcja 1 — max 40 chars]",   # opcja jest krótka, szczegóły w wiadomości 1
        "[Opcja 2 — max 40 chars]",
        "[Opcja 3 — max 40 chars]",
    ],
    multi_select=False
)
```

**Hard limits:**
- `question`: max 100 chars (sweet spot: 60-80)
- `choices[i]`: max 80 chars każda (sweet spot: 50-70) — powyżej 90 chars Discord renderuje obcinane
- Max 4 opcje (Discord UI ograniczenie)

**Eksperymentalne limity (28.07.2026, profil gaja):**
- pytanie 22 chars + opcja 56 chars → ✅ widoczne w całości
- pytanie 22 chars + opcja 85 chars → ✅ widoczne w całości
- pytanie 22 chars + opcja 100+ chars → ❌ obcinane przez Discord

## Przykład (A+B zastosowane)

### ❌ Złe (za długie, ucinane przez Discord):

```python
print("[5 profili sprawdzonych, P0 znalezione: RPi offline 30h+, ...")
print("[długa lista...")
print("...")
print("[pytanie: co teraz robimy?]")
clarify(question="[znowu długie pytanie z kontekstem wbudowanym]",
        choices=["A) Idź do RPi", "B) Backup repo", "C) Napraw nightly", "D) Pauza"])
# = ~5000 chars → DISCORD UCINA → widzisz początek tylko
```

### ✅ Dobre (A+B):

```python
# Wiadomość 1 (kontekst)
print("📊 Co czeka na Twoją decyzję")
print()
print("🔴 P0 (3): RPi .178 offline, NUC .173 porty martwe, 4 repo bez remote")
print("🟠 P1 (2): feature branch dirty, 2 untracked w archiwum")
print()
print("Szczegóły: ~/gaja-projekty/HEOS/docs/decision-walks/2026-07-29.md")
# ~250 chars — mieści się łatwo

# Wiadomość 2 (clarify — krótka)
clarify(
    question="Od czego zaczynamy?",
    choices=["A) RPi (fizycznie)", "B) Backup repo (PAT/UI)", "C) Napraw nightly alert", "D) Pauza HEOS"],
)
# ~150 chars — mieści się
```

## Decision: kiedy dzielić na 2 wiadomości

| Łączna długość | Strategia |
|---|---|
| < 800 chars | Jedna wiadomość (kontekst + clarify w bloku) |
| 800–1500 chars | Jedna wiadomość, ale max skrócone opcje |
| 1500–2000 chars | Split OBOWIĄZKOWY — kontekst osobno, clarify osobno |
| > 2000 chars | Split + `Szczegóły:` link do pliku (nie powtarzaj w wiadomości) |

## Konwencje

- **Severity**: 🔴 P0 (produkcja/utrata danych) / 🟠 P1 (realne blokery) / 🟡 P2 (tech debt) / ✅ OK (działa)
- **Pytanie zawsze kończy się `?`** — użytkownik wie że to pytanie, nie raport
- **Opcje mają prefix `A) B) C) D)`** — dla szybkiego reference
- **Nie umieszczaj pytań w markdown body** — pytanie ZAWSZE idzie przez `clarify` tool
- **Po wyborze Jokera: NIE pytaj "czy chcesz żebym zrobił X"** — po prostu rób (per kolaboracja-joker-gaja)

## Related

- **skill-pending-decisions-review** — wzorzec raportu który wymaga tego skilla
- **kolaboracja-joker-gaja** — "Po wyborze Jokera: NIE pytaj o potwierdzenie, po prostu rób"
- **HEOS ADR-011** — preferencje komunikacyjne dla profili Hermes

## Workflow

1. **Policz chars** — `len(pytanie) + sum(len(opcja) for opcja in choices)`. Jeśli > 400 → planuj split.
2. **Oszacuj łączną długość** — `raport + pytanie`. Jeśli > 1500 → split OBOWIĄZKOWY.
3. **Jeśli split**:
   - Wiadomość 1: kontekst z `🔴🟠🟡✅` (max 1500 chars)
   - Wiadomość 2: `clarify` z pytaniem (max 100 chars) + opcjami (max 40 chars × 4)
4. **Jeśli NIE split**: kontekst + pytanie w jednym bloku (max 1500 chars).
5. **Po wyborze Jokera**: execute natychmiast, NIE pytaj "czy na pewno?" (per kolaboracja-joker-gaja).

## Przykłady

### ✅ Dobre (split A+B):

```python
# Wiadomość 1 (kontekst, ~250 chars)
print("📊 Co czeka na Twoją decyzję")
print("🔴 P0 (3): RPi offline 30h+, NUC porty martwe, 4 repo bez remote")
print("🟠 P1 (2): feature branch dirty, 2 untracked w archiwum")
print("Szczegóły: ~/gaja-projekty/HEOS/docs/decision-walks/2026-07-29.md")

# Wiadomość 2 (clarify, ~150 chars)
clarify(
    question="Od czego zaczynamy?",
    choices=["A) RPi (fizycznie)", "B) Backup repo (PAT/UI)", "C) Pauza HEOS"],
)
```

### ❌ Złe (za długie, ucinane):

```python
print("[5 profili sprawdzonych, P0 znalezione: ...]")
print("[długa lista wszystkich issues...]")
print("[pytanie: co teraz robimy? z kontekstem]")
clarify(question="[znowu długie pytanie z kontekstem wbudowanym]",
        choices=["A) ...", "B) ...", "C) ..."])
# = ~5000 chars → DISCORD UCINA
```

## Lessons Learned

1. **Discord ucina bez ostrzeżenia** — nie ma "message truncated" info, po prostu znika reszta. Dlatego MUSISZ liczyć chars przed wysłaniem.
2. **Kontekst w `clarify question` to anti-pattern** — question powinien być krótki, kontekst powinien być osobno. Jeśli wklejasz kontekst do question, Joker musi czytać mały printscreen + ogromny przycisk.
3. **Max 4 opcje w Discord UI** — 5+ opcji powoduje scroll. Konsoliduj do 4 lub użyj "Other (type your answer)" jako 4-tej.
4. **`Szczegóły:` link do pliku** zamiast powtarzania długiej listy — Joker może otworzyć pełny raport jeśli chce szczegółów, ale krótka wiadomość mieści się w Discord.
5. **Severity emoji (🔴🟠🟡✅)** to standaryzowany wzorzec z `kolaboracja-joker-gaja` § 9 — używaj konsekwentnie.

- [ ] Przed KAŻDYM `clarify`: sprawdź `len(question) + sum(len(c) for c in choices) < 400`
- [ ] Jeśli raport + pytanie > 1500 chars: split OBOWIĄZKOWY
- [ ] Jeśli opcje > 4: konsoliduj do max 4 (lub "Other (type your answer)")
- [ ] Po wyborze Jokera: execute natychmiast, NIE pytaj "czy na pewno?"

Fail gdy: `clarify` z kontekstem >2000 chars (Discord ucina) lub opcje > 4 (UI broken).

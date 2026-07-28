# Etap L — Memory Hygiene (audyt pamięci operacyjnej)

> Wyciągnięte z `nightly-evolution.md` v1.2.1 (2026-07-25). Załadować tylko gdy nocny przebieg dociera do Kroku 5.6 (codziennie) lub 5.6b (aktywny gdy `day == 1`). Główny `SKILL.md` ma tylko overview + odnośnik tutaj.

## Krok 5.6 — Etap L: Memory Hygiene (audyt pamięci operacyjnej)

**Realizuje:** instrukcja Jokera "System samodzielnej higieny pamięci Gai" §10-12.

**Zakres:** `~/.hermes/profiles/gaja/memories/` (NIE HEOS, NIE inne profile).

**Dane wejściowe:**

```bash
MEMORY=~/.hermes/profiles/gaja/memories/MEMORY.md
INDEX=~/.hermes/profiles/gaja/memories/memory/projects-index.md
DECISIONS=~/.hermes/profiles/gaja/memories/memory/decisions.md
PENDING=~/.hermes/profiles/gaja/memories/memory/pending-review.md
CHANGELOG=~/.hermes/profiles/gaja/memories/memory/changelog.md
ARCHIVE_DIR=~/.hermes/profiles/gaja/memories/memory/archive/

# rozmiary
wc -c "$MEMORY" "$INDEX" "$DECISIONS" "$PENDING" "$CHANGELOG" 2>/dev/null

# % limitu MEMORY.md (limit 22000)
python3 -c "
import os
sz = os.path.getsize('$MEMORY')
pct = sz / 22000 * 100
print(f'MEMORY.md: {sz} B / 22000 B = {pct:.1f}%')
"

# append-only detekcja: linie zaczynające się od nowego paragrafu po §9/§10
# (szukaj wzorca: linia nie zaczyna się od '#', nie jest pusta, nie jest częścią listy)
```

**Sprawdzenia (6 punktów):**

1. **Rozmiar MEMORY.md vs progi:**
   - `< 80%` (17,600 B) → OK, brak akcji
   - `80-90%` → INFO, raportuj w daily
   - `90-95%` → WARN, zaproponuj konsolidację w `## Knowledge Routing` (typ `memory`)
   - `> 95%` → FAIL, krytyczny, wymaga ręcznej konsolidacji (zgodnie z instrukcją §3)

2. **Append-only do przeniesienia:**
   - W `MEMORY.md` szukaj linii zaczynających się od nowego tematu (np. `^[A-Z][^§#\n].{40,}` po ostatniej sekcji `## 10`).
   - Jeśli znajdziesz → wpisz w `## Memory Hygiene` jako "TODO przeniesienia do §10 Lessons z sesji" (z wklejeniem treści).
   - **NIE przenoś automatycznie** — tylko sygnalizuj.

3. **`memory/pending-review.md` wiek:**
   - Znajdź wpisy bez statusu "Decyzja:" (czyli nierozstrzygnięte).
   - Jeśli któryś ma > 7 dni → wpisz w daily jako "🟡 Stara sprawa wymaga decyzji: <tytuł>".
   - Jeśli > 14 dni → wpisz w daily jako "🔴 Krytycznie stara: <tytuł>".

4. **Duplikaty między `MEMORY.md` a `memory/decisions.md`:**
   - Dla każdej sekcji `## N` w `MEMORY.md` sprawdź czy temat nie leży też w `decisions.md` (grep po pierwszych 5 słowach nagłówka).
   - Jeśli duplikat → wpisz w daily jako "🔄 Duplikat: <MEMORY.md §X> ≡ <decisions.md §Y>".

5. **Aktywne audyty miesięczne (Krok 5.6b):**
   - Sprawdź `date +%d` — jeśli `== "01"` → wykonaj audyt miesięczny (patrz Krok 5.6b).
   - Jeśli nie → pomiń.

6. **Baseline tracking (od v1.2):**
   - Przy KAŻDYM przebiegu (nie tylko miesięcznym) zapisz do
     `state/memory-metrics.jsonl` linijkę: `{"date": "YYYY-MM-DD", "size": N, "pct": P, "append_only": N, "pending_unresolved": N, "duplicates": N}`.
   - Po 30 dniach masz wykres trendu rozmiaru MEMORY.md.
   - Plik jest append-only, nigdy nie nadpisuj.
   - Użyj: `tail -30 state/memory-metrics.jsonl` dla trendu ostatnich 30 dni.

**Co dodać do daily report (nowa sekcja `## Memory Hygiene`, po `## Knowledge Routing`):**

```markdown
## Memory Hygiene

### Stan pamięci
- MEMORY.md: <rozmiar> B / 22,000 B (<procent>%) → <OK | INFO | WARN | FAIL>
- memory/projects-index.md: <rozmiar> B
- memory/decisions.md: <rozmiar> B
- memory/pending-review.md: <rozmiar> B (<liczba> nierozstrzygniętych)
- memory/archive/: <rozmiar> B

### TODO przeniesienia (append-only)
- [ ] <treść appendu, max 200 B> — źródło: MEMORY.md linia <N>

### Stare sprawy do decyzji (> 7 dni)
- 🟡 <tytuł z pending-review.md> — dodane: <data>
- 🔴 <tytuł> — dodane: <data> (> 14 dni)

### Duplikaty wykryte
- 🔄 MEMORY.md §<X> ≡ memory/decisions.md §<Y>

### Akcja wymagana
- (jeśli FAIL > 95%) → patrz instrukcja §3: obowiązkowy audyt, przenieś szczegóły do plików pomocniczych
```

## Krok 5.6b — Etap L+: Audyt miesięczny (aktywny gdy `day == 1`)

**Realizuje:** instrukcja Jokera §12 "Audyt miesięczny".

**Trigger:** `date +%d` zwraca `"01"`.

**Dodatkowe sprawdzenia (poza Krok 5.6):**

1. **Sync `memory/projects-index.md` z `~/gaja-projekty/README.md`:**
   - Pobierz listę projektów z obu plików (grep po linkach do `Joker22pl/`).
   - Jeśli rozbieżność → wpisz w daily jako "🔄 Drift: <projekt> jest w hub ale nie w index (lub odwrotnie)".

2. **Archiwizacja projektów zakończonych:**
   - Sprawdź `~/gaja-projekty/README.md` pod kątem statusu ⚪ / "zakończony".
   - Jeśli znajdziesz → wpisz w daily jako "📦 Do archiwizacji: <projekt>".

3. **Duplikaty między `memory/`, skille, dokumentacja:**
   - Dla każdego wpisu w `decisions.md` sprawdź czy temat nie jest też w `skills/*/SKILL.md` lub `~/gaja-projekty/HEOS/`.
   - Jeśli duplikat trwały (pojawia się w 2+ miejscach) → wpisz w daily jako "🔄 Duplikat przekrojowy: <memory/decisions.md §X> ≡ <skill/.../SKILL.md §Y>".

4. **Wskaźniki do repo:**
   - Sprawdź czy wszystkie linki w `memory/projects-index.md` są aktywne (`gh repo view` lub prosty git ls-remote).
   - Jeśli martwy → wpisz w daily jako "🔗 Martwy wskaźnik: <URL>".

5. **Propozycja większych zmian:**
   - Jeśli wykryto ≥3 duplikatów, ≥2 martwe wskaźniki, lub inne poważne problemy → utwórz `reports/proposals/YYYY-MM-DD-memory-restructuring.md` z listą zmian do zatwierdzenia.

**Co dodać do daily report (rozszerzenie sekcji `## Memory Hygiene`):**

```markdown
## Memory Hygiene (audyt miesięczny)

### Sync z hub README
- ✅ Zgodne / 🔄 Drift: <lista>

### Archiwizacja
- 📦 Do archiwizacji: <lista> (przenieś do "Projekty zakończone" w index + README)

### Duplikaty przekrojowe (memory ↔ skills ↔ HEOS)
- 🔄 <lista>

### Wskaźniki do repo
- 🔗 Martwe: <lista>

### Propozycje zmian (wymagają decyzji użytkownika)
- (jeśli ≥3 duplikatów lub inne poważne problemy) → patrz `reports/proposals/...`
```

**Uwagi:**

- Audyt miesięczny może trwać dłużej niż zwykły dzienny. To OK — uruchamia się raz w miesiącu.
- NIE wykonuj żadnych mutacji (nie przenoś projektów, nie usuwaj duplikatów). Tylko raportuj.
- Propozycje z `reports/proposals/` czekają na decyzję Jokera.

## Powiązane

- `skills/memory-hygiene/SKILL.md` — klasa równoległa (manual audyt na żądanie), Etap L działa codziennie
- `nightly-evolution/SKILL.md` (główny plik) — Krok 5.6 + Krok 5.6b w workflow
- Krok 14b w głównym SKILL.md — alert krytyczny gdy MEMORY.md > 95% przez 3 kolejne przebiegi

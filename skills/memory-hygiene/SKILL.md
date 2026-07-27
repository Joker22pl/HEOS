---

name: memory-hygiene
description: Audyt pamięci operacyjnej profilu Hermes Agent gaja. Sprawdza rozmiar MEMORY.md, append-only do przeniesienia,
  wiek spraw pending-review, duplikaty między MEMORY.md a memory/, oraz synchronizację projects-index z hub README. Load
  na żądanie (nie jest automatyczny — nightly-evolution robi to samo o 1:00).
status: accepted
type: skill
id: skill-memory-hygiene
title: Memory Hygiene
owner: gaja
created_at: '2026-07-25'
updated_at: '2026-07-26'
review_due: '2027-01-23'
version: 1.4.0
heos_standard_version: "1.2"
tags:
- cross-cutting
- memory
- audit
related:
- skill-nightly-evolution
quality_schema: pass
quality_technical: pass
quality_operational: fresh
last_verified: 2026-07-27
verified_on: manual consolidation session (25,103 B → 8,612 B), Krok 8 verified w praktyce
---

# Memory Hygiene

## Cel

Standalone audyt pamięci operacyjnej profilu `gaja` na żądanie. Wykonuje ten sam algorytm co Etap L w `nightly-evolution`, ale bez czekania na nocny przebieg. Pozwala Jokerowi zweryfikować stan pamięci w środku sesji, przed dużym commitem albo po zakończeniu większej pracy. **Limit bazowy: 26,000 B** (od 2026-07-27, był 22,000 B — patrz sekcja "Limit history").

## Zakres

**W zakresie:**

- Sprawdzenie rozmiaru `~/.hermes/profiles/gaja/memories/MEMORY.md` vs limit 26,000 B (limit bazowy od 2026-07-27 — patrz sekcja "Limit history").
- Detekcja append-only wpisów (tekst dodany po ostatniej sekcji `##` bez nagłówka).
- Wiek spraw w `memory/pending-review.md` (>7 dni = 🟡, >14 dni = 🔴).
- Duplikaty między `MEMORY.md` a `memory/decisions.md`.
- (Miesięcznie) sync `memory/projects-index.md` z `~/gaja-projekty/README.md`, archiwizacja, martwe wskaźniki.

**Poza zakresem (patrz inne Skills):**

- Nocny cykliczny audyt — to robi `nightly-evolution` Etap L automatycznie.
- Mutacje plików pamięci — ten skill TYLKO raportuje. Zmiany wymagają Twojej decyzji.
- Audyt HEOS skills / innych profili — to robi `HEOS Weekly Audit` + `gaja-server-audit`.

## Kiedy używać

- ✅ Przed commitem zmian w `memory/` — sprawdź czy nie łamiesz limitu.
- ✅ Po długiej sesji z wieloma nowymi ustaleniami — weryfikuj stan.
- ✅ Przed otwarciem `pending-review.md` żeby wiedzieć co tam wisi.
- ✅ W odpowiedzi na pytanie Jokera "ile mam miejsca w pamięci?" / "czy coś wisi?".
- ✅ **Gdy MEMORY.md > 80% (> 17,600 B)** — uruchom ten skill, żeby zdecydować co kondensować (Krok 3.5).

## Kiedy nie używać

- ❌ Do cyklicznego audytu — to jest `nightly-evolution` Etap L (1:00 daily).
- ❌ Do automatycznych mutacji pamięci — ten skill nigdy nie zmienia plików.
- ❌ Do audytu HEOS lub innych profili (`gaja-it`, `gaja-med`) — granice profili (ADR-005).

## Workflow

### Krok 1 — Zebranie metryk

```bash
MEMORY=~/.hermes/profiles/gaja/memories/MEMORY.md
INDEX=~/.hermes/profiles/gaja/memories/memory/projects-index.md
DECISIONS=~/.hermes/profiles/gaja/memories/memory/decisions.md
PENDING=~/.hermes/profiles/gaja/memories/memory/pending-review.md
CHANGELOG=~/.hermes/profiles/gaja/memories/memory/changelog.md
HUB=~/gaja-projekty/README.md

# rozmiary
wc -c "$MEMORY" "$INDEX" "$DECISIONS" "$PENDING" "$CHANGELOG"
```

> **Limit ewoluował:** 22,000 B (v1.0) → 26,000 B (2026-07-27, po ręcznej konsolidacji — patrz "Limit history" na końcu skilla). Wszystkie progi poniżej przeliczone na nowy limit. Źródło prawdy: `python3 -c "import os; print(os.path.expanduser('~/.hermes/profiles/gaja/memories/MEMORY.md'))"` → czytaj limit z własnego frontmatter tego skilla, NIE hardcode'uj w skryptach.

### Krok 2 — Rozmiar MEMORY.md vs progi

Oblicz `pct = size / 26000 * 100` (limit bazowy 26,000 B od 2026-07-27). Statusy:

| Procent (limit 26 KB) | Procent (limit 22 KB — legacy) | Rozmiar | Status | Akcja |
|---|---|---|---|---|
| `< 80%` | `< 80%` | `< 20,800 B` (nowy) / `< 17,600 B` (legacy) | OK | brak |
| `80-90%` | `80-90%` | `20,800-23,400 B` (nowy) | INFO | pokaż w raporcie |
| `90-95%` | `90-95%` | `23,400-24,700 B` (nowy) | WARN | zaproponuj konsolidację (Krok 3.5/8) |
| `> 95%` | `> 95%` | `> 24,700 B` (nowy) / `> 20,900 B` (legacy) | FAIL | krytyczny, wymaga ręcznej akcji |

**Helper do odczytu limitu z frontmatter skill (sync z wersją skilla):**

```bash
LIMIT=$(python3 -c "
import re
with open(os.path.expanduser('~/.hermes/profiles/gaja/skills/software-development/memory-hygiene/SKILL.md')) as f:
    m = re.search(r'limit bazowy (\d+)', f.read())
    print(m.group(1) if m else 26000)
")
python3 -c "
import os, sys
limit = int(sys.argv[1]) if len(sys.argv) > 1 else 26000
sz = os.path.getsize(os.path.expanduser('~/.hermes/profiles/gaja/memories/MEMORY.md'))
pct = sz / limit * 100
status = 'OK' if pct < 80 else 'INFO' if pct < 90 else 'WARN' if pct < 95 else 'FAIL'
print(f'{sz} B / {limit} B = {pct:.1f}% [{status}]')
" "$LIMIT"
```

**Manual session override:** gdy Joker mówi "zabierz się za konsolidację" i limit >95%, wykonaj pełen **Krok 8 (Manual Consolidation Session)** — NIE czekaj na nocny Evolution.

### Krok 3 — Detekcja append-only (zaktualizowany 2026-07-27)

**Format MEMORY.md (kanoniczny od 2026-07-27):** sekcje oznaczone jako `## §N`
(np. `## §1`, `## §2`, … `## §16`). Każda sekcja jest samodzielnym blokiem tematycznym.
**NIE używaj** starego formatu `## Tytuł` (legacy) ani separatora `§` mid-block
(legacy 2026-07-25/26). Detektor MUSI rozpoznawać oba formaty — walidacja przejścia
dopiero po 30 dniach od pełnej migracji.

**Wzorzec detekcji (dual-format, 2026-07-27):**

```bash
# 1. Wyciągnij ostatni nagłówek sekcji — PRIORYTET: §N format
LAST_HEADER=$(grep -n "^## §" "$MEMORY" | tail -1 | cut -d: -f1)
if [ -z "$LAST_HEADER" ]; then
  # fallback na legacy format
  LAST_HEADER=$(grep -n "^## " "$MEMORY" | tail -1 | cut -d: -f1)
fi

# 2. Wyciągnij wszystko od ostatniego ## do końca pliku
tail -n +"$LAST_HEADER" "$MEMORY" > /tmp/last_section.txt

# 3. nowy format (2026-07-27+): sekcje oddzielone nagłówkami §N
#    Ostatnia sekcja = blok od ostatniego "## §N" do EOF
#    Append-only = tekst PO ostatniej sekcji BEZ nowego nagłówka §N

# 4. klasyfikuj:
#   - Jeśli ostatnia sekcja ma < 800 B → OK, nie raportuj
#   - Jeśli ostatnia sekcja ma > 800 B → sprawdź czy to "pointer sekcja"
#     (typowo §16 "Memory hygiene pointery" — lista pointerów, duża ale stabilna)
#   - Tekst poza jakąkolwiek sekcją → flaguj jako append-only
```

**Klasyfikacja bloków (po pierwszej migracji 2026-07-27):**

| Wzorzec w MEMORY.md | Typ | Akcja |
|---|---|---|
| Nagłówek `## §N (temat)` + treść | sekcja kanoniczna | nie flaguj |
| Tekst po ostatniej `## §N` bez nagłówka | append-only | przenieś do istniejącej §N lub utwórz §N+1 |
| Linie zaczynające się od `**` (bold) w append-only | prawdopodobnie lesson | przenieś do §N "Tool quirks" / §3 "Patch lessons" itp. |
| Duża sekcja pointerów (`§16 Memory hygiene pointery`) | stabilna | zostaje |

**Blacklist fraz dla legacy fallbacku (po first-run 2026-07-25):**

- "Skondensowane do ~400 B" (koniec instrukcji §10)
- "Patrz `memory/" (wskaźnik do innego pliku)
- "Nowy skill / aktualizacja" (legenda)
- "Poza zakresem" (nagłówek blokowy)

**Fallback gdy brak separatora § (legacy pliki):** oryginalna heurystyka `^[A-Z].{40,}`
+ blacklist. Wynik ZAWSZE oznaczaj jako "niejednoznaczne, sprawdź ręcznie w ostatnich
30 liniach pliku".

**Polskie znaki (potwierdzone 2026-07-27 nightly-evolution):** regex `^[A-Z].{40,}`
poprawnie matchuje linie z ą, ę, ł, ó, ż, ś, ć, ń. Wykryto 20 luźnych linii w
przebiegu 2026-07-27 (vs 11 w 2026-07-26) — append-only rośnie szybciej niż
kondensacja nadąża. Przyrost: +9 luźnych linii w 26h. Flaguj to jako sygnał że
MEMORY.md > 95% i kondensacja Krok 3.5/8 jest krytyczna. Jeśli N luźnych linii
rośnie między przebiegami o >5 → eskaluj w raporcie jako "append-only rośnie
szybciej niż konsolidacja".

**Dlaczego dual-format:** migracja 2026-07-27 (manual session Joker) z legacy
`## Tytuł + § separator` na nowy `## §N` bez separatora mid-block. Pliki historyczne
w `archive/` i backupy w `~/hermes-backups/` zachowują stary format — detektor
musi je czytać poprawnie.

### Krok 3.5 — Kondensacja dużych bloków (zaktualizowany 2026-07-27)

Gdy `MEMORY.md` rośnie > 80% limitu (> 20,800 B dla limitu 26 KB) i Krok 3 wykrywa
duże bloki (> 800 B), zamiast tylko raportować — **zaproponuj kondensację** w stylu
"1-2 zdania + wskaźnik do źródła prawdy".

**Wzorzec kondensacji (sesja 2026-07-26, 8 bloków skondensowanych, 20,540 → 12,961 B = -36.9%):**

```text
PRZED (875 B):
HDS 2026-07-25: Stage 6-7 production Pygame panel na RPi 3A+ jest
stabilny. Diagnostyczny łańcuch "is-active=active ale brak SSE w
NUC log" oznacza: PID w epoll_wait + brak TCP w ss -tnp = asyncio
task created but never scheduled (GIL held by render thread, await
stop_event.wait() blokuje event loop). Fix: render thread musi
yieldować (clock.tick albo asyncio.sleep(0)). To jest Stage 6 fix,
nie blokuje Stage 1/5 deployment. Unit file musi mieć: User=hds
(NIE panel!), SDL_VIDEODRIVER=dummy, PYTHONUNBUFFERED=1,
XDG_RUNTIME_DIR=/run/user/1000 (hardcoded, nie %U który się nie
rozwija w Environment=), PrivateDevices=no (NIE false # comment bo
systemd odrzuca trailing comment jako invalid argument).
EnvironmentFile= czyta PO [Service] Environment= — env file wygrywa.
RestartSec=3→5 bo OOM kill na RPi 3A+ pod SDL+pygame+asyncio+labwc
potrzebuje czasu na zwolnienie RAM.

PO (280 B):
HDS 2026-07-25: Stage 6-7 Pygame panel RPi 3A+ — render thread GIL
blokuje asyncio. Fix: SSE task in own thread + own event loop.
Szczegóły + unit file hardening:
→ `~/gaja-projekty/HEOS/skills/hds-canonical-architecture-and-runtime-gotchas/SKILL.md`
```

**Reguła skracania:**

1. **Pierwsze zdanie** = problem/trigger (1 linia, 50-80 znaków).
2. **Drugie zdanie** = fix/zasada (1 linia, 50-80 znaków).
3. **Trzecia linia** = wskaźnik do źródła prawdy w skillu/dokumencie.
4. **Max 4-5 linii na blok.** Jeśli nie da się skondensować → blok jest za duży dla memory, przenieś cały do skilla.

**Kiedy NIE kondensować:**

- Blok dotyczy **operator-facing** (komunikacja, format output, user preference) — zostaje jak jest, bo agent musi mieć szybki dostęp bez ładowania skilla.
- Blok dotyczy **bezpieczeństwa** (reguła "NIGDY", "BEZPIECZNIK", "PRZED") — pełna treść zostaje, bo skrót może ukryć edge case.
- Blok ma < 800 B — kondensacja nie jest warta effort.

**Walidacja po kondensacji:**

- `wc -c MEMORY.md` → < 80% limitu (17,600 B)
- Każdy wskaźnik rozwiązuje się do istniejącego pliku (`test -f <ścieżka>` dla każdego → 0 missing)

### Krok 4 — Wiek spraw pending-review

```bash
# Parsuj daty z wpisów `**Data:** YYYY-MM-DD`
# Dla każdego wpisu bez statusu "Decyzja:" oblicz wiek
# < 7 dni: nie raportuj
# 7-14 dni: 🟡 "Stara sprawa: <tytuł>"
# > 14 dni: 🔴 "Krytycznie stara: <tytuł>"
```

### Krok 5 — Duplikaty (zaktualizowany po first-run 2026-07-25)

**3 klasy overlapu** (nie tylko "duplikat / nie-duplikat"):

1. **Temat-nazwa overlap** (np. "Preferencje Jokera" pojawia się w obu plikach) —
   **zwykle OK**. Oznacza że temat jest ważny i ma dedykowane miejsce w obu.
   Klasyfikuj jako `intentional-redundancy:short-pointer`.
   - MEMORY.md trzyma skrót (1-2 zdania, max 5 bulletów).
   - `decisions.md` trzyma pełną wersję z kontekstem, datą, źródłem.
   - **To jest pożądany wzorzec** — w raporcie oznacz "ℹ️ intencjonalna redundancja".

2. **Identyczna treść** (np. ta sama lista bullet po obu stronach) — **prawdziwy duplikat**.
   Klasyfikuj jako `duplicate:identical-content`.
   - Akcja: zostaw pełniejszą wersję (zwykle `decisions.md`), w MEMORY.md wstaw krótki wskaźnik.
   - Raportuj jako `🔄 Duplikat: MEMORY §N ≡ decisions §M`.

3. **Częściowa zbieżność** (np. jedna sekcja jest podzbiorem drugiej) — **kandydat do konsolidacji**.
   Klasyfikuj jako `overlap:partial`.
   - Akcja: zależy od intencji (który plik jest source-of-truth?). Pytaj Jokera.
   - Raportuj jako `⚠️ Partial overlap: MEMORY §N ⊃ decisions §M` (lub odwrotnie).

**Wzorzec (3 kroki):**

```bash
# 1. Wyciągnij nagłówki ## z MEMORY.md + decisions.md
MEMORY_HEADERS=$(grep "^## " "$MEMORY" | sed 's/^## //')
DECISIONS_HEADERS=$(grep "^## " "$DECISIONS" | sed 's/^## //')

# 2. Topic-name overlap (faza 1 — klasyfikacja wstępna)
while IFS= read -r hdr; do
  fp=$(echo "$hdr" | awk '{print $1" "$2" "$3}' | tr '[:upper:]' '[:lower:]')
  if grep -qi "$fp" "$DECISIONS"; then
    echo "TOPIC_OVERLAP: MEMORY §'$hdr' vs decisions §<grep-matched>"
  fi
done <<< "$MEMORY_HEADERS"

# 3. Weryfikacja treści (faza 2 — klasyfikacja klasy)
# Dla każdego TOPIC_OVERLAP: weź 100 znaków treści pod nagłówkiem z obu plików
# i oblicz similarity (diff -q lub python difflib)
# similarity > 80% → duplicate:identical-content
# 30-80% → overlap:partial
# < 30% → intentional-redundancy:short-pointer
```

**Dlaczego 3 klasy (nie binarne):** first-run 2026-07-25 wykrył 3 topic-overlaps (Preferencje Jokera, Tryb pracy, Profile Hermesa). Wszystkie 3 to **intencjonalna redundancja** (krótki wskaźnik w MEMORY.md, pełna wersja w decisions.md) — ale binarna klasyfikacja "duplikat" raportowałaby je jako problemy do naprawy. To prowadziłoby do **fałszywej rekomendacji** (zostaw tylko w jednym miejscu, zamiast w obu w odpowiednich formatach).

### Krok 6 — Audyt miesięczny (tylko gdy `date +%d == "01"`)

Dodatkowe sprawdzenia:
- Sync `projects-index.md` ↔ `~/gaja-projekty/README.md` (lista projektów).
- Martwe wskaźniki (URL-e w `projects-index.md` — weryfikacja przez `gh repo view` lub curl).
- Projekty do archiwizacji (status ⚪ w hub README).
- Duplikaty przekrojowe (memory ↔ skills ↔ HEOS docs).

### Krok 7 — Wygeneruj raport

Format wyjściowy (max 30 linii):

```
🧠 Memory Hygiene — YYYY-MM-DD HH:MM

Stan:
- MEMORY.md: <rozmiar> B / 22,000 B (<pct>%) → <OK|INFO|WARN|FAIL>
- projects-index.md: <rozmiar> B
- decisions.md: <rozmiar> B
- pending-review.md: <rozmiar> B (<N> nierozstrzygniętych)
- changelog.md: <rozmiar> B
- archive/: <rozmiar> B

Problemy wykryte:
- 📝 Append-only do przeniesienia: <N> (lista max 3)
- 🟡 Stare sprawy pending-review: <lista>
- 🔄 Duplikaty MEMORY ↔ decisions: <lista>

(jeśli dzień == 01)
Audyt miesięczny:
- 🔄 Drift projects-index ↔ hub README: <lista>
- 🔗 Martwe wskaźniki: <lista>
- 📦 Do archiwizacji: <lista>

Rekomendacja:
- <1-2 zdania co zrobić (jeśli FAIL > 95%, natychmiast)>
```

## Przykłady

### Przykład 1: Szybka weryfikacja w trakcie sesji

Sytuacja: Joker pyta "ile mam miejsca w pamięci, zanim zacznę zapisywać nowy lesson?".

Wynik:

```
🧠 Memory Hygiene — 2026-07-25 16:55

Stan:
- MEMORY.md: 8,471 B / 22,000 B (38.5%) → OK
- pending-review.md: 1 nierozstrzygnięta

Rekomendacja: Miejsca dużo (~13.5 KB wolnego). Można spokojnie zapisać.
```

### Przykład 2: Wykrycie append-only

Sytuacja: nocny audyt dopisał techniczny lesson na końcu `MEMORY.md` (po §10).

Wynik:

```
🧠 Memory Hygiene — 2026-07-25 01:07

Problemy wykryte:
- 📝 Append-only do przeniesienia: 1
  - "HDS 2026-07-25: Stage 6-7 production Pygame panel..." (linia 130)
  → docelowa sekcja: §10 Lessons z sesji

Rekomendacja: Przenieść append do §10 z kondensacją do ~400 B + wskaźnik do szczegółów.
```

### Przykład 3: Audyt miesięczny wykrywa drift

Sytuacja: 2026-08-01, `projects-index.md` ma 3 projekty, `hub README` ma 4 (nowy repo).

Wynik:

```
🧠 Memory Hygiene — 2026-08-01 01:00 (audyt miesięczny)

Audyt miesięczny:
- 🔄 Drift projects-index ↔ hub README: 1
  - "Joker22pl/nowy-projekt" jest w hub ale NIE w projects-index.md

Rekomendacja: Dopisz sekcję do projects-index.md lub poczekaj na decyzję Jokera.
```

## Lessons Learned

Wnioski z pierwszej sesji użycia (2026-07-25). Tylko to, co zmienia sposób korzystania ze skilla.

1. **Standalone = reaktywny, Etap L = proaktywny.** Skill `memory-hygiene` służy do szybkich sprawdzeń w trakcie sesji. Do systematycznego audytu czekaj na nocny raport (Etap L w `nightly-evolution`). Nie duplikuj — oba narzędzia mają tę samą logikę, ale różne wyzwalacze.
2. **Nie mutuj, tylko raportuj.** Ten skill NIGDY nie zmienia plików pamięci. Mutacje wymagają Twojej decyzji (lub sesji z kontekstem). To jest różnica vs Etap L, który też nie mutuje ale jest częścią większego nocnego przebiegu.
3. **Filtr 7-pkt z instrukcji Jokera §4 to nie audyt — to filtr zapisu.** Ten skill NIE egzekwuje filtra, tylko sprawdza stan. Filtr zapisu stosuje Etap L w Knowledge Routing przy każdym nowym wpisie.
4. **Append-only detection: separator `§` jako marker** (zaktualizowany po first-run 2026-07-25).
   Oryginalna heurystyka pierwszej wersji `[A-Z].{40,}` łapała 4 false positives WEWNĄTRZ §10
   (np. "Skondensowane do ~400 B + wskaźnik do szczegółów" — wszystko pasowało, a to nie jest append).
   Nowy wzorzec: separator `§` jest kanonicznym markerem między blokami w tym profilu.
   Algorytm: tail od ostatniego `## ` → split po `§` → klasyfikuj bloki. Pierwszy blok = treść
   ostatniej sekcji (nie flaguj), kolejne = kandydaci. Blacklist fraz do fallbacku
   ("Skondensowane", "Patrz", "Nowy", "Poza").
5. **Duplikaty mają 3 klasy, nie binarną** (zaktualizowany po first-run 2026-07-25).
   First-run wykrył 3 topic-overlaps jako "🔄 Duplikat" — wszystkie okazały się
   `intentional-redundancy:short-pointer` (krótki wskaźnik w MEMORY.md + pełna wersja
   w decisions.md). To jest pożądany wzorzec, nie problem. Binarna klasyfikacja
   raportowałaby je jako "do naprawy" → fałszywa rekomendacja.
   Nowa klasyfikacja: `intentional-redundancy` / `duplicate:identical-content` / `overlap:partial`.
   Decyzja: similarity > 80% = duplikat, 30-80% = partial (pytaj), < 30% = intentional.
6. **Miesięczny audyt to NIE osobny skill.** Ten sam skill z jednym dodatkowym krokiem (Krok 6) triggerowanym przez `date +%d == "01"`. Bez sensu tworzyć `memory-hygiene-monthly` jako osobny skill — to zwiększa koszt utrzymania bez korzyści.
7. **Kondensacja: 1-2 zdania + wskaźnik do skilla** (nowy, 2026-07-26 Faza 1 closeout).
   Wzorzec: gdy MEMORY.md > 80% (> 17,600 B), duże bloki (> 800 B) trzeba skondensować.
   Schemat: (1) Pierwsze zdanie = problem/trigger. (2) Drugie zdanie = fix/zasada.
   (3) Trzecia linia = wskaźnik do źródła prawdy. Max 4-5 linii.
   Realne liczby z sesji 2026-07-26: 8 bloków (HDS Stage 6-7 fix, RPi 13h lessons,
   Hermes dashboard, patch lessons, HDS runtime facts, Skill audit pattern, Parallel
   session detect, Alias extension). Średnia oszczędność ~900 B/blok.
   Łącznie: 20,540 → 12,961 B = -7,579 B (-36.9%), z 93.4% → 58.9%.
   Wskaźnik zawsze rozwiązuje się do istniejącego pliku — `test -f` po kondensacji.
   Krok 3.5 dokumentuje pełen wzorzec + reguły kiedy NIE kondensować.
8. **`memory-metrics.jsonl` baseline pattern (2026-07-27, Etap L pkt 6).**
   Każdy przebieg dopisuje 1 linię: `{"date": "YYYY-MM-DD", "size": N, "pct": P, "append_only": N, "pending_unresolved": N, "duplicates": N}`.
   Po 7+ dniach masz trend. Wzorzec czytania: `tail -7 state/memory-metrics.jsonl | python3 -c "import json,sys; rows=[json.loads(l) for l in sys.stdin]; ..."`.
   Kluczowe sygnały: (a) rozmiar rośnie >5% w 24h → eskaluj; (b) `consecutive_memory_critical` z `state/last-run.json` przekracza 2 → raportuj jako CRONICZNE.
   Mechanizm Krok 14b alertu w `nightly-evolution` (alert po 3. kolejnych przebiegach >95%) zweryfikowany w praktyce 2026-07-27: 1→2 (po 2 przebiegach), alert Krok 14b odpali się przy 3. przebiegu.
   Kiedy `append_only` rośnie między przebiegami o >5 — to sygnał że kondensacja Krok 3.5 nie nadąża, a nie "bug w append-only detection".

9. **Manual Consolidation Session > nocny Evolution Krok 5.6 (2026-07-27).**
   Gdy Joker mówi "zabierz się za konsolidację" — NIE czekaj na nocny raport.
   Wykonaj pełen 7-etapowy workflow (Krok 8): inventory → routing → backup →
   migracja → nowy MEMORY.md → walidacja → metryki. Verified 2026-07-27:
   25,103 B → 8,612 B (-65.7%) w 25 min. Pliki: MEMORY.md (write_file),
   decisions.md (append nowych sekcji), projects-index.md (patch),
   archive/2026-07-27-batch5b-archiwizacja.md (nowy), changelog.md (append),
   memory-metrics.jsonl (append z `consolidation_event: true`).
   **Antywzorzec:** edycja per-blok bez pełnego inventory (gubi kontekst);
   pominięcie backup (utrata odwracalności); migracja danych DO decisions.md
   bez zmiany stylu; nowy MEMORY.md pisany przez append do starego (zostaje
   noise). Routing table decyzyjna w Krok 8 / "Routing decisions".

10. **Format MEMORY.md ewoluował: legacy `§` separator → kanoniczny `## §N` nagłówki
    (2026-07-27).** Trzecia odsłona formatu. Pierwszy format (v1.0): luźne bloki
    tekstu z `## Tytuł` nagłówkami i `§` separatorami mid-block. Drugi format
    (ex v1.3, pre 2026-07-27): nagłówki `##` + `§` separatory. Trzeci format
    (kanoniczny 2026-07-27): nagłówki `## §N`, BRAK separatorów mid-block, sekcje
    samodzielne. Krok 3 detection MUSI obsługiwać oba formaty do 2026-08-27
    (30 dni grace period na backupy/archiwa). Po 2026-08-27 tylko `## §N`.
    Detekcja append-only w nowym formacie: tekst PO ostatniej `## §N` BEZ
    nowego nagłówka §N+1.

11. **Limit memory evolution (2026-07-27):** 22,000 B → 26,000 B (+18%).
    Powód: nadmierne nightly raporty (Etap L + K) generowały zbyt dużo
    pointerów (do skille, decisions.md, archive/). Zwiększenie limitu dało
    bufor 4 KB na "szybkie lesson bez kondensacji", ale NIE zastępuje Krok 3.5/8.
    Antywzorzec: traktowanie większego limitu jako zachęty do niekondensowania.
    Filary: (a) limit baseline do odczytu z frontmatter (`python3 -c "...grep limit bazowy..."`),
    (b) Krok 3.5 kondensacja per-blok gdy > 80%, (c) Krok 8 manual session gdy
    > 95% LUB Joker wyraźnie komenderuje.

## Typowe błędy

- **Uruchomienie tego skilla zamiast czekania na nocny raport** — bez sensu, jeśli wiesz że Etap L działa. Skill jest do sytuacji "potrzebuję teraz", nie "audytuj regularnie".
- **Mutacja plików z poziomu skilla** — zakazane. Jeśli widzisz FAIL > 95%, przenieś decyzję do Jokera albo do osobnej sesji z kontekstem.
- **Miesięczny audyt częściej niż raz w miesiącu** — Krok 6 jest triggerowany przez datę, nie przez ręczne wywołanie. Jeśli chcesz pełen audyt teraz, użyj `date -d "+30 days"` jako testu logiki, ale nie nadpisuj stanu.

## Debugging

| Objaw | Przyczyna | Fix |
|---|---|---|
| Skill nie ładuje się przez `skill_view()` | loader cache'owany, nowa wersja widoczna od następnej sesji | restart sesji lub `hermes skills reload` |
| Rozmiar MEMORY.md > 100% | append-only z nocnego audytu nie został przeniesiony | wykonaj Krok 8 (Manual Consolidation) ręcznie |
| Duplikat false-positive | nagłówek ma ogólne słowa ("Konwencja", "Wzorzec") | czytaj oba konteksty zanim zgłosisz |
| Brak `archive/` | skill `kolaboracja-joker-gaja` nigdy nie został zainicjowany | utwórz katalog ręcznie: `mkdir -p memory/archive/` |
| Detekcja append-only = 0 | MEMORY.md w nowym formacie `## §N`, szukasz `## ` ogólnie | sprawdź czy regex ma `^## §` jako alternatywę (Krok 3 dual-format) |

### Krok 8 — Manual Consolidation Session (nowy, 2026-07-27)

**Kiedy:** Joker mówi "zabierz się za konsolidację" / "skonsoliduj pamięć" / "MEMORY.md
za duży" — NIE czekaj na nocny Evolution. Wykonaj pełen 7-etapowy workflow.

**7 etapów konsolidacji (verified 2026-07-27, MEMORY.md 25,103 B → 8,612 B):**

1. **Inventory** — `read_file` MEMORY.md całości, podziel na chunki po separatorze,
   sklasyfikuj każdy (decyzja długoterminowa / always-on lesson / fakt projektowy /
   szczegół historyczny).
2. **Routing** — tabela per chunk → 4 cele: `decisions.md` (nowa sekcja) /
   `MEMORY.md` (kompakt) / `archive/<date>-<topic>.md` / `projects-index.md`.
3. **Backup** — `cp -v MEMORY.md ~/hermes-backups/MEMORY.md.pre-consolidation-<timestamp>`
   + to samo dla `decisions.md`. Odwracalne.
4. **Migracja** — `write_file` dużych bloków do celów (decisions.md nowe sekcje
   z append; archive/ pliki ze szczegółami; projects-index.md +wpisy).
5. **Nowy MEMORY.md** — pisany od zera jako 16 sekcji `§1`-`§16`. Pierwsze
   zdanie = problem/trigger. Drugie = fix/zasada. Trzecia linia = wskaźnik
   (do skilla / decisions.md / archive). Max 4-5 linii na blok.
6. **Walidacja** — `wc -c` MEMORY.md (< 80% limitu), brak utraty wiedzy
   (każdy chunk ma pointer), brak sekretów (`grep -iE '(api[_-]?key|token)...'
   reports/`). Porównaj sumę rozmiarów chunków przed/po.
7. **Metryki + changelog** — `state/memory-metrics.jsonl` nowa linia z flagą
   `consolidation_event: true` + `reduction_pct`. Append do `memory/changelog.md`
   z datą, przyczyną, wynikami per plik.

**Walidacja rozmiaru po każdym etapie:**

| Etap | Sprawdź |
|---|---|
| 1 (Inventory) | `wc -l MEMORY.md` (rozmiar wejściowy) |
| 5 (Nowy MEMORY) | `wc -c MEMORY.md` (< 80% = 20,800 B dla limitu 26 KB) |
| 6 (Walidacja) | `wc -c MEMORY.md decisions.md projects-index.md archive/` — suma ~ równa wejściu, ale rozłożona |
| 7 (Metryki) | `cat memory-metrics.jsonl | tail -1` — nowa linia z reduction_pct |

**Routing decisions (Etap K + instrukcja Jokera §3):**

| Typ informacji | Cel | Kto zapisuje |
|---|---|---|
| Decyzja architektoniczna / wzorzec | `decisions.md` (nowa sekcja) | manual session |
| Always-on lesson (każda sesja) | `MEMORY.md §N` kompakt + pointer | manual session |
| Fakt projektowy (adres, hardware, status) | `projects-index.md` | manual session |
| Szczegół historyczny operacji | `archive/<date>-<topic>.md` | manual session |
| Decyzja do rana Jokera | `pending-review.md` | manual session |
| Procedura wielokrotnego użycia (≥3 potwierdzenia) | nowy / update skilla | **tylko propozycja w raporcie** |
| Zmiana wzorca współpracy | `decisions.md` (sekcja Preferencje) | manual session |

**Filtr (trwałość × pewność × powtórzenia), potwierdzony 2026-07-27:**

- `trwałość = jednorazowa` → `archive/` (nie zapisuj w decisions.md ani MEMORY.md)
- `trwałość = średnioterminowa` → `decisions.md` (kompakt) + szczegóły w skilla jeśli procedura
- `trwałość = długoterminowa` + `pewność HIGH` + `powtórzeń < 3` → pozostaw w raporcie (za mało danych)
- `trwałość = długoterminowa` + `pewność HIGH` + `powtórzeń ≥ 3` → `decisions.md` / nowy skill

**Antywzorzec — czego NIE robić:**

- ❌ Edycja per-blok bez pełnego inventory (gubi kontekst)
- ❌ Pominięcie backup (utrata odwracalności)
- ❌ Migracja danych DO decisions.md bez zmiany stylu (decyzje to nie "Memory hygiene pointery")
- ❌ Nowy MEMORY.md pisany przez append do starego (zostaje stary noise)
- ❌ Brak metryki po konsolidacji (nie wiesz czy wzorzec się poprawił)

**Realne metryki 2026-07-27:**

- Przed: 25,103 B / 26,000 B = 96.5% (FAIL)
- Po: 8,612 B / 26,000 B = 33.1% (OK)
- Redukcja: -65.7%
- Czas: ~25 min (inventory → backup → migracja → nowy plik → walidacja → metryki)
- Pliki zmienione: MEMORY.md (write_file), decisions.md (append), projects-index.md (patch×2), archive/2026-07-27-batch5b-archiwizacja.md (nowy), changelog.md (append), memory-metrics.jsonl (append)

**Dlaczego manual > nightly-evolution Krok 5.6:**

`nightly-evolution` Krok 5.6 **raportuje** stan (append-only do przeniesienia,
duplikaty), NIE mutuje. Czeka na Joker decyzję rano. Gdy Joker mówi "zabierz się
za konsolidację" — to jest zielone światło na Krok 8 (pełen workflow mutacji).
Nie ma sensu dzielić tego na Etap L + manual session — manual session jest
**szybszy i pełniejszy** niż nocna analiza (25 min vs 30+ min nocnego raportu).

## Narzędzia

- `wc -c` — rozmiar plików.
- `python3 -c "..."` — obliczenia % (limit 22000).
- `grep` — duplikaty (pierwsze 5 słów nagłówka jako fingerprint).
- `find` + `stat` — wiek spraw (mtime pliku jako proxy daty wpisu).
- `gh repo view` — weryfikacja aktywności URL-i w projects-index.
- `date +%d` — trigger miesięczny (gdy == "01").

**Race condition detection** — patrz `references/race-condition-signs.md`
(7 sygnałów że zewnętrzny writer pisał do `MEMORY.md` między Twoimi edycjami;
zawiera gotowe komendy detekcyjne dla każdego sygnału).

**Linked files:**
- `references/race-condition-signs.md` — gotowe komendy detekcyjne dla
  7 sygnałów race condition w `MEMORY.md`.
- `references/first-run-2026-07-25.md` — pełen raport pierwszego uruchomienia
  (2026-07-25 20:23), false positives które złapała stara heurystyka Krok 3,
  rozstrzygnięcie 3 duplikatów z Krok 5. Używaj jako wzorca przy interpretacji
  wyników audytu.
- `references/manual-consolidation-2026-07-27.md` — pełen scenariusz pierwszej
  manualnej konsolidacji Krok 8 (zrealizowanej 2026-07-27, MEMORY.md
  25,103 B → 8,612 B). Zawiera tabelę routingu 30 chunków, listę 8 zmian
  plików, 6 lekcji dla następnej sesji, audit trail z rozmiarami. **Użyj
  jako wzorca** gdy Joker powie "zabierz się za konsolidację" lub MEMORY.md
  > 95%.

## Oficjalne źródła

- Instrukcja Jokera "System samodzielnej higieny pamięci Gai" — zasady §1-16.
- HEOS CONSTITUTION.md §"Proces realizacji" — kontekst audytu.
- Skill `nightly-evolution` Etap L — cykliczna wersja tego skilla.
- Skill `komunikacja-z-joker` §31 — memory limit handling.

## Wersjonowanie

- **v1.1.0** (2026-07-25) — first-run patch.
  - Krok 3 (append-only): oryginalna heurystyka `^[A-Z].{40,}` dawała 4 false positives
    wewnątrz §10. Nowy wzorzec używa separatora `§` jako canonical marker + blacklist
    fraz ("Skondensowane", "Patrz", "Nowy", "Poza"). Algorytm: tail od ostatniego `##` →
    split po `§` → klasyfikuj bloki. Pierwszy blok = treść ostatniej sekcji (nie flaguj),
    kolejne = kandydaci.
  - Krok 5 (duplikaty): 3 klasy zamiast binarnej. `intentional-redundancy:short-pointer` (MEMORY.md
    trzyma skrót, decisions.md pełną wersję — pożądany wzorzec) / `duplicate:identical-content`
    (similarity > 80%) / `overlap:partial` (30-80%, pytaj).
  - Lessons Learned #4-5 zaktualizowane, dodane LL#6 (3-klasowa klasyfikacja overlapu).
  - Reference `first-run-2026-07-25.md` dodany — szczegóły wykryć i false positives.
- **v1.0.0** (2026-07-25) — pierwsza wersja. Audit standalone, pełen zakres (codzienny + miesięczny).
- **v1.3.0** (2026-07-26) — Krok 3.5 (kondensacja dużych bloków) + Lessons Learned #7.
  - Dodany wzorzec "1-2 zdania + wskaźnik do skilla" gdy MEMORY.md > 80%.
  - Reguła skracania: max 4-5 linii/blok, problem + fix + źródło prawdy.
  - Wyjątki: operator-facing + bezpieczeństwo (NIGDY/BEZPIECZNIK) + bloki < 800 B.
  - Walidacja: `wc -c` < 80% + `test -f` dla każdego wskaźnika.
  - Realna sesja 2026-07-26 (Faza 1 closeout): 8 bloków skondensowanych,
    20,540 → 12,961 B (-36.9%).
- **v1.3.1** (2026-07-27) — Polish chars verification + memory-metrics.jsonl pattern.
  - Krok 3: regex `^[A-Z].{40,}` potwierdzony poprawnie dla polskich znaków (ą, ę, ł, ó, ż, ś, ć, ń). Wykryto 20 luźnych linii w nightly-evolution (vs 11 poprzednio) — append-only rośnie szybciej niż kondensacja.
  - Dodana eskalacja: jeśli `append_only` rośnie o >5 między przebiegami → sygnał że kondensacja Krok 3.5 nie nadąża.
  - Lessons Learned #8: wzorzec `memory-metrics.jsonl` baseline + Krok 14b alert verification (consecutive_memory_critical 1→2).
  - last_verified: 2026-07-27 (nightly-evolution Etap L verification).
- **v1.4.0** (2026-07-27) — Manual Consolidation Session + dual-format detection + limit evolution.
  - **Limit zmieniony z 22,000 B na 26,000 B.** Powód: nightly rapporty generowały zbyt dużo
    pointerów. Nowy limit daje bufor 4 KB.
  - **Nowy Krok 8 (Manual Consolidation Session)** — pełen 7-etapowy workflow manualnej
    konsolidacji (inventory → routing → backup → migracja → nowy MEMORY → walidacja → metryki).
    Uruchamiany gdy Joker mówi "zabierz się za konsolidację" LUB MEMORY.md > 95%.
    Verified 2026-07-27: 25,103 B → 8,612 B w 25 min.
  - **Krok 3 dual-format detection** — kanoniczny nowy format MEMORY.md (2026-07-27+)
    to `## §N` nagłówki, NIE `§` separatory mid-block. Detekcja obsługuje oba formaty
    do 2026-08-27.
  - **Lessons Learned #9, #10, #11** dodane (manual session, format evolution, limit evolution).
  - **Krok 2 tabela progów:** legacy 22 KB kolumna + nowa 26 KB kolumna + helper Python
    do odczytu limitu z frontmatter skilla (sync z wersją).
  - **Krok 3.5 prog:** > 20,800 B (80% nowego limitu), nie 17,600 B.
  - **Verification:** target < 20,800 B (80% nowego limitu), nie < 16 KB.
  - Backward compat: stare progi (17,600 / 20,900 / 22,000) zachowane w tabeli jako
    "legacy" kolumna dla czytelności historycznej.

## Checklisty

### Pre-flight

- [ ] Sprawdź czy `~/.hermes/profiles/gaja/memories/` istnieje.
- [ ] Sprawdź czy `~/gaja-projekty/README.md` istnieje (dla audytu miesięcznego).

### Post-use

- [ ] Wygeneruj raport w formacie Krok 7.
- [ ] Jeśli FAIL > 95%: wyślij raport do Jokera z rekomendacją konsolidacji.
- [ ] Jeśli znaleziono append-only: zaproponuj przeniesienie do §10 (nie rób sam).

## Najlepsze praktyki

1. **Szybki check przed commitem** — `wc -c MEMORY.md`, jeśli > 90% to wstrzymaj się z nowymi wpisami.
2. **Pełen audyt tylko gdy potrzebny** — nie uruchamiaj co godzinę. Raz na sesję wystarczy.
3. **Miesięczny audyt czeka na 1. dzień miesiąca** — nie próbuj go triggerować ręcznie.
4. **Raport max 30 linii** — dłuższy to szum. Joker potrzebuje stanu + rekomendacji, nie wykładu.

## Powiązane

- **skill-nightly-evolution** — nocna wersja tego skilla (Etap L, automatycznie 1:00).
- **skill-komunikacja-z-joker** — §31 "Memory limit handling" (procedura konsolidacji).
- **HEOS CONSTITUTION** — kontekst standardów audytu.
- **ADR-005** — granice profili (ten skill NIE działa na `gaja-it` / `gaja-med`).


## Verification

- **Komenda (standalone audit):** `python3 ~/.hermes/profiles/gaja/skills/software-development/memory-hygiene/scripts/audit.py` (lub `hermes memory audit` jeśli CLI dostępne)
  - **Oczekiwany output:** raport z rozmiarem MEMORY.md, duplikatami, spraw pending
  - **Pass gdy:** rozmiar < 16 KB (target), 0 spraw >14 dni (🔴)
  - **Czas:** < 5s

- **Komenda (size check):** `wc -c ~/.hermes/profiles/gaja/memories/MEMORY.md`
  - **Oczekiwany output:** < 20,800 B (80% limitu 26 KB), > 24,700 B = krytyczny
  - **Pass gdy:** < 20,800 B (target)
  - **Czas:** < 1s

- **Komenda (pending review age):** sprawdź wiek spraw w `memory/pending-review.md`
  - **Oczekiwany output:** 0 spraw >14 dni
  - **Pass gdy:** wszystkie spraw <7 dni (🟢) lub 7-14 dni (🟡)
  - **Czas:** < 1s

- **Test integracyjny (pełen audit):**
  - **Setup:** standalone wywołanie w sesji (nie nocny cron)
  - **Kroki:**
    1. Uruchom audyt
    2. Sprawdź raport
    3. Jeśli są krytyczne (🔴) → STOP, konsoliduj
    4. Jeśli OK → kontynuuj pracę
  - **Kryterium PASS:** raport bez krytycznych + Joker zaakceptował
  - **Kryterium FAIL:** którykolwiek krytyczny → konsolidacja PRZED kontynuacją

- **Audit (miesięcznie):** sprawdź czy `memory/projects-index.md` jest zsynchronizowany z `~/gaja-projekty/README.md` (główne repo).

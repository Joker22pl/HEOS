---
name: nightly-evolution
description: Uruchamiaj przy nocnym, automatycznym przebiegu analizy własnej pracy (03:00). Generuje Daily Retrospective,
  Lessons Learned, Self Review, Documentation Health, Architecture Review, Error Intelligence, Performance Report, Improvement
  Backlog i plan na kolejny dzień. Load ONLY when the Nightly Evolution cron job fires — never load this skill ad-hoc for
  user tasks.
status: accepted
heos_version: '1.2.1'
data_root: ~/.hermes/profiles/gaja/nightly-evolution
type: skill
id: skill-nightly-evolution
title: Nightly Evolution
owner: gaja
created_at: '2026-07-24'
updated_at: '2026-07-25'
review_due: '2027-01-23'
version: 1.2.1
heos_standard_version: "1.2"
tags:
- cross-cutting
related:
- skill-using-chm
- adr-002
- adr-005
- adr-008
- skill-memory-hygiene
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---

# Nightly Evolution

## Cel

Automatyczny, ciągły proces doskonalenia pracy profilu Hermes Agent `gaja`. Co 24 godziny (03:00 czasu lokalnego serwera) analizuje okres od ostatniego poprawnego przebiegu i produkuje:

1. **Daily Retrospective** — co zrobiono, co osiągnięto, jakie decyzje podjęto, problemy, eksperymenty, otwarte sprawy.
2. **Lessons Learned** — tylko wiedza długoterminowa z dowodami i poziomem pewności.
3. **Self Review** — ocena własnej pracy (planowanie, jakość, iteracje, tokeny).
4. **Documentation Health** — duplikaty, sprzeczności, martwe odnośniki, jednoznaczność źródeł prawdy.
5. **Architecture Review** — duplikacja, złożoność, zależności, odpowiedzialności (bez wdrażania zmian).
6. **Error Intelligence** — istotne błędy z symptomami, przyczynami, dowodami, prewencją.
7. **Performance Report** — PASS/WARN/FAIL, modele, tokeny, koszt, czas.
8. **Self Improvement Backlog** — lista usprawnień do akceptacji.
9. **Plan na kolejny dzień** — 3 zadania, 3 ryzyka, 3 decyzje, 3 usprawnienia.

## Zakres

**W zakresie:**
- Analiza historii sesji (`state.db`), logów (`~/.hermes/profiles/gaja/logs/`), pamięci (`memories/`).
- Analiza zmian w profilu Hermesa i HEOS od ostatniego przebiegu.
- Czytanie dokumentacji (README, ADR, SKILL.md), wykrywanie dokumentów martwych/sprzecznych.
- Zapis raportów do katalogu danych skilla.

**Poza zakresem (bez zgody użytkownika):**
- Usuwanie plików, modyfikacja SOUL.md, konfiguracji modeli, sekretów, .env.
- Instalacja pakietów, aktualizacja Hermesa, push/merge, zmiana HEOS.
- Wdrażanie RFC, zmiany architektoniczne, zmiany standardów.
- Tworzenie kolejnych zadań cron w trakcie nocnego przebiegu.

## Kiedy używać

- ✅ Zadanie cron `Nightly Evolution` (0 1 * * *) właśnie się uruchomiło.
- ✅ Użytkownik ręcznie poprosił o pełną retrospektywę (poza cyklem) i explicite wskazał ten skill.

## Kiedy nie używać

- ❌ Zwykłe zadanie użytkownika — to jest narzędzie wyłącznie nocne/retrospektywne, nie ogólne.
- ❌ Pierwszy przebieg tuż po instalacji, gdy użytkownik nie zaakceptował jeszcze wyniku.
- ❌ Profil `gaja-it` lub `gaja-med` — granice profili (ADR-005), Nightly Evolution jest w profilu `gaja`.

## Workflow

### Krok 0 — Odczytaj stan

Ścieżka: `$DATA = ~/.hermes/profiles/gaja/nightly-evolution`

```bash
cat "$DATA/state/last-run.json"
```

- `last_successful_run` → od tego czasu zaczyna się okno analizy.
- Jeśli `null` lub brak pliku → okno = ostatnie 24 godziny.
- Zapisz `started_at` do pliku roboczego (NIE do `last-run.json` — to atomowy stan tylko po sukcesie).

### Krok 0.5 — Self-check: czy skill sam się ładuje

**Obowiązkowy.** Bez tego nocny cron może cicho przejść z `Skill not found` i nie wykonać żadnej pracy.

```python
import json
from tools.skills_tool import skill_view  # hermes-agent
out = json.loads(skill_view("nightly-evolution"))
if not out.get("success"):
    # NIE przechodź dalej. NIE aktualizuj last_successful_run.
    # Wyślij alert użytkownikowi (krok 14a) i zakończ.
    abort_with_alert(...)
```

Kroki:
1. Wywołaj `skill_view("nightly-evolution")`.
2. Jeśli `success=False`:
   - Zapisz krótki raport do `reports/errors/YYYY-MM-DD-skill-missing.md` z powodem (`error` field).
   - Inkrementuj `consecutive_failures` w `state/last-run.json`.
   - **NIE aktualizuj** `last_successful_run` (atomowa zasada z Krok 13).
   - **NIE uruchamiaj** kroków 1–13.
   - Wyślij alert do kanału `origin` z instrukcją dla użytkownika (krok 14a).
3. Jeśli `success=True` → kontynuuj do Krok 1.

**Dlaczego:** Historia zna przypadek (2026-07-24 03:00 UTC) gdzie symlink HEOS→loader stał się martwy po migracji HEOS v1.1→v1.2, skill przestał się ładować, cron przeszedł dalej z ostrzeżeniem, użytkownik dowiedział się dopiero rano. Ten krok to zamyka.

### Krok 1 — Ustal okno analizy

```
window_start = last_successful_run  (lub now - 24h przy pierwszym uruchomieniu)
window_end   = now
```

### Krok 2 — Zebranie źródeł (tylko w oknie)

Korzystaj z `session_search` (FTS5, szybkie) + `search_files`/`read_file` do odczytania:

| Źródło | Co wyciągnąć |
|---|---|
| `state.db` (FTS5) | tematy sesji, błędy, decyzje w oknie |
| `~/.hermes/profiles/gaja/logs/gateway.log` | błędy gatewaya, ostrzeżenia |
| `~/.hermes/profiles/gaja/memories/*.md` | nowe wpisy pamięci |
| `~/.hermes/profiles/gaja/skills/**` (mtime w oknie) | zmienione skille |
| `~/gaja-projekty/HEOS/**` (mtime w oknie) | zmiany HEOS |
| `~/.hermes/profiles/gaja/cron/jobs.json` (mtime) | nowe/zatrzymane crony |

**Nie czytaj całej historii projektu.** Tylko okno.

### Krok 3 — Etap A: Zakres analizy

Już wykonany w kroku 1. Zapisz w raporcie daty okna.

### Krok 4 — Etap B: Daily Retrospective → `reports/daily/YYYY-MM-DD-summary.md`

Struktura (każdy punkt obowiązkowy, ale treść może być "brak" jeśli faktycznie nic):

```markdown
# Daily Retrospective — YYYY-MM-DD

Okno: <window_start> → <window_end> (UTC)

## Co wykonano
- ...

## Cele osiągnięte
- ...

## Decyzje podjęte
- ...

## Problemy / błędy
- ...

## Eksperymenty
- ...

## Odrzucone pomysły
- ...

## Pozostaje otwarte
- ...

## Wymaga decyzji użytkownika
- ...
```

### Krok 5 — Etap C: Lessons Learned (długoterminowe)

Wybierz TYLKO wnioski z wartością długoterminową. Dla każdego:

```
- Wniosek: ...
- Źródło/dowód: <plik:linia lub daily-summary>
- Pewność: ★☆☆☆☆ do ★★★★★ (uzasadnij jednym zdaniem)
- Trwałość: długoterminowa | średnioterminowa | jednorazowa
- Proponowane miejsce: <skill | ADR | README | pamięć>
- Rekomendacja: zachować | odrzucić | sprawdzić | zaproponować jako standard
```

**Nie zapisuj hipotez jako faktów.** Brak dowodu = brak wpisu.

Dodaj `## Lessons Learned` do raportu daily.

### Krok 5.5 — Etap K: Knowledge Routing (klasyfikacja i routing wiedzy)

**Uwaga: ten krok musi WYZNACZYĆ trasę zapisu, zanim cokolwiek zostanie zapisane na stałe.** Bez niego nocny audyt ryzykuje duplikowanie (pamięć + skill), zaśmiecanie pamięci faktami projektowymi albo pozostawianie procedur wyłącznie w raporcie.

Dla każdego kandydata z okna (Lessons Learned, powtarzający się błąd, skuteczna procedura, problem narzędzia, kandydat na skill, nowy trwały fakt) wypełnij rekord klasyfikacji:

```
- Informacja: <jedno zdanie streszczające>
- Typ: pamiec | skill | skill-update | project-doc | tracker | audit-log | session-only
- Dowód: <plik:linia | daily-summary | log:linia>
- Trwałość: jednorazowa | średnioterminowa | długoterminowa
- Pewność: HIGH | MEDIUM | LOW
- Kontekst: <profil gaja | projekt X | HEOS | ogólne>
- Docelowa ścieżka: <np. memories/<topic>.md | skills/<skill>/SKILL.md | ~/gaja-projekty/<proj>/docs/... | state/improvement-backlog.md>
- Akcja: zapisz | zaproponuj | pozostaw-w-raporcie | odrzuc
- Uzasadnienie: <1-2 zdania dlaczego taki typ>
```

#### Tabela routingu (reguła domyślna)

| Rodzaj informacji | Miejsce zapisu | Kto zapisuje |
|---|---|---|
| Trwały fakt o użytkowniku / środowisku / preferencji | pamięć profilu (`memory` tool) | **automatycznie** przez rapport, ale zapis do pamięci **wymaga sekcji z rekomendacją** — decyzja Jokera rano |
| Procedura wielokrotnego użycia (≥3 potwierdzenia) | nowy skill lub update skilla | **tylko propozycja** w backlogu (typ `new-skill` / `skill-update`) |
| Wzorzec architektoniczny / decyzja z konsekwencjami >1 tydzień | ADR | **tylko propozycja** w `reports/proposals/` |
| Dokumentacja projektu (fakty, limity, zależności) | pliki repozytorium projektu | **tylko propozycja** w backlogu (typ `project-doc`) |
| Tymczasowy stan zadania / decyzja do jutra | sekcja "Plan na jutro" w daily | **automatycznie** w raporcie |
| Log techniczny / event / metryka | `daily/`, `errors/`, `performance/` | **automatycznie** |
| Powtarzający się błąd z obejściem | `state/improvement-backlog.md` (typ `error-fix`) | **automatycznie** |
| Jednorazowa rozmowa / contextless | pozostaje w sesji | **nic** — nie zapisuj |

#### Dozwolone akcje automatyczne (bez zgody Jokera)

- Zapis do `reports/daily/<dziś>-summary.md`
- Zapis do `reports/errors/`
- Zapis do `reports/performance/`
- Append do `state/improvement-backlog.md` (status OPEN)
- Append do `state/last-run.json`

#### Zakaz automatycznego zapisu (wymaga akceptacji Jokera)

- Zapis do `memories/` (pamięć profilu)
- Tworzenie / modyfikacja jakiegokolwiek skilla
- Tworzenie / modyfikacja ADR
- Zmiany w dokumentacji projektu (`~/gaja-projekty/<proj>/...`)
- Zmiany w repozytorium HEOS
- Zmiany w `SOUL.md`, `USER.md`, `config.yaml`, `.env`
- Zmiany w trackerach projektowych (Jira, Linear, kanban)
- Commit / push / merge

#### Co dodać do daily report (nowa sekcja `## Knowledge Routing`)

```markdown
## Knowledge Routing

### Routing podsumowanie
- Do pamięci (wymaga akceptacji): N
- Kandydaci na nowe skille: N
- Kandydaci do poprawy skilli: N
- Dokumentacja projektowa (wymaga akceptacji): N
- Tracker / plan na jutro: N  ← już raportowany, tu tylko count
- Log audytowy: N  ← już raportowany, tu tylko count
- Pozostaje w sesji: N

### Kandydaci do akceptacji (wymagają Jokera rano)

#### Pamięć (trwały fakt)
- [ ] <Informacja> — typ: USER | ENV | PREF — dowód: <ścieżka> — pewność: HIGH

#### Nowe skille
- [ ] <Procedura> — typ: new-skill — powtórzeń: 3 — dowód: <lista sesji>

#### Poprawa istniejących
- [ ] <Skill X> — typ: skill-update — przyczyna: <np. niejasny Krok 3>

#### Dokumentacja projektu
- [ ] <Projekt Y> — typ: project-doc — ścieżka docelowa: <...> — uzasadnienie
```

#### Dlaczego ten krok jest potrzebny

Przed Etapem K nocny przebieg raportował, ale **nie rozstrzygał**, co z każdą informacją zrobić. To prowadziło do:

- duplikowania (ten sam wniosek w pamięci i skillu),
- zaśmiecania pamięci faktami projektowymi (np. aritmetika enkodera w pamięci ogólnej),
- procedur pozostających wyłącznie w raporcie i nigdy nie trafiających do skilla,
- backlogu zamiast właściwego artefaktu (ADR / skill / doc).

Etap K rozwiązuje to jawną decyzją: **typ → ścieżka → akcja → wymaga akceptacji (tak/nie)**.

#### Pułapka: klasyfikacja pod presją aktywności

Projekt intensywnie używany (np. IMP2) w ciągu dnia wygeneruje 5-10 kandydatów do skilla. Nie wszystkie są krytyczne. Filtr:

- `trwałość = jednorazowa` → `session-only` (nie zapisuj)
- `trwałość = średnioterminowa` → `audit-log` (zapisz w raporcie, nie w pamięci)
- `trwałość = długoterminowa` + `pewność = HIGH` + `powtórzeń ≥ 3` → `skill` lub `ADR`
- `trwałość = długoterminowa` + `pewność = HIGH` + `powtórzeń < 3` → `pozostaw-w-raporcie` (za mało danych)
- `trwałość = długoterminowa` + `pewność = MEDIUM` → `zaproponuj` (wymaga akceptacji)

Bez tego filtra 50% projektów dostanie skill, który potem nikt nie używa.

**Konsumpcja w kolejnych krokach:** Po Etapie K (Krok 5.5) codzienny raport MUSI zawierać przyrostek `## Knowledge Routing` (wzór powyżej). Wpisy w backlogu (Krok 11) dziedziczą `Typ` z rekordów Etapu K. Krok 14 (Discord) posiada sekcję `🧭 Knowledge Routing`.

### Krok 5.6 — Etap L: Memory Hygiene (audyt pamięci operacyjnej)

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

**Sprawdzenia (5 punktów):**

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

6. **Baseline tracking (NOWE w v1.2):**
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

### Krok 5.6b — Etap L+: Audyt miesięczny (aktywny gdy `day == 1`)

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

### Krok 6 — Etap D: Self Review → `## Self Review` w daily

```
- Trafność planowania: HIGH|MEDIUM|LOW (uzasadnienie)
- Jakość wykonania: HIGH|MEDIUM|LOW
- Iteracje: <liczba> — czy były zbędne?
- Błędy/nieudane próby: <lista>
- Niepotrzebne użycie narzędzi: <lista>
- Tokeny/koszt: <wartość lub "brak danych">
- Co uprościć: <lista>
```

### Krok 7 — Etap E: Documentation Health → `## Documentation Health` w daily

Sprawdź zmienione pliki w oknie:

| Problem | Dowód |
|---|---|
| Duplikat informacji | <plik:sekcja> vs <plik:sekcja> |
| Sprzeczne instrukcje | <plik A mówi X, plik B mówi ¬X> |
| Martwe odnośniki | <ścieżka/URL nie istnieje> |
| Tymczasowe traktowane jako obowiązujące | <ścieżka> |
| Stan w dokumentach architektonicznych | <np. "TODO" w HEOS-MASTER-PROMPT> |
| Wiele źródeł prawdy dla jednego standardu | <np. 3 pliki definiują konwencję commitów> |

**Nie usuwaj ani nie przepisuj dokumentów.** Tylko raportuj.

### Krok 8 — Etap F: Architecture Review → `## Architecture Review` w daily + opcjonalnie `reports/proposals/`

```
- Duplikacja: <lista>
- Nadmierna złożoność: <lista>
- Błędne zależności: <lista>
- Niespójne odpowiedzialności: <lista>
- Możliwości uproszczenia: <lista>
- Brakujące testy/walidacja: <lista>
```

Każda **większa** zmiana architektury → osobna propozycja:

`reports/proposals/YYYY-MM-DD-<krotka-nazwa>.md` z polami:

```
- Problem
- Dowody
- Proponowana zmiana
- Korzyści
- Ryzyka
- Koszt wdrożenia (S|M|L|XL)
- Kryteria akceptacji
- Plan wycofania
```

Propozycje **nie są wdrażane** — czekają na akceptację użytkownika.

### Krok 9 — Etap G: Error Intelligence → `reports/errors/YYYY-MM-DD-errors.md`

Dla każdego istotnego błędu w oknie:

```
- Błąd: <krótki opis>
- Objaw: ...
- Prawdopodobna przyczyna: ...
- Potwierdzone dowody: <log:linia, plik:linia>
- Zastosowane rozwiązanie: ...
- Prewencja: ...
- Występował wcześniej: tak/nie, dowód
```

**Nie raportuj tego samego błędu wielokrotnie** — grupuj lub wskaż "patrz <daily-...>".

### Krok 10 — Etap H: Performance Report → `reports/performance/YYYY-MM-DD.md`

```
# Performance — YYYY-MM-DD

Okno: <window_start> → <window_end>

- Zadań (sesji): N
- PASS: x | WARN: y | FAIL: z
- Modele: <lista>
- Tokeny wejściowe: N (lub "brak danych")
- Tokeny wyjściowe: N (lub "brak danych")
- Koszt: $X (lub "brak danych")
- Czas wykonania (suma): Nh Mm
- Najdroższe zadanie: <nazwa/ID>
- Najwięcej iteracji: <nazwa/ID>
```

**Nie szacuj** — jeśli danych brak, wpisz `brak danych`.

### Krok 11 — Etap I: Self Improvement Backlog → `state/improvement-backlog.md`

Dla każdego kandydata z Etapu K (Knowledge Routing) oraz każdego problemu z daily (B, D, E, F, G):

1. Sprawdź czy już istnieje w backlogu (grep po tytule lub ID).
2. Jeśli tak → zaktualizuj istniejący wpis (data, status, notatka).
3. Jeśli nie → dodaj nowy wpis z ID `IMP-YYYY-NNN`.

**Pole `Typ` jest obowiązkowe** — wynika z Etapu K i determinuje domyślną akcję wykonawczą po akceptacji:

| Typ | Akcja po akceptacji | Wymaga decyzji w Etap K |
|---|---|---|
| `new-skill` | Utworzenie nowego skilla | ✅ |
| `skill-update` | Patch istniejącego skilla | ✅ |
| `adr` | Utworzenie nowego ADR | ✅ |
| `adr-update` | Patch istniejącego ADR | ✅ |
| `project-doc` | Edycja plików w `~/gaja-projekty/<proj>/...` | ✅ |
| `heos-doc` | Edycja w `~/gaja-projekty/HEOS/...` | ✅ |
| `memory` | Zapis do `memories/<topic>.md` | ✅ |
| `tracker` | Zmiana w trackerze projektowym | ✅ |
| `error-fix` | Patch kodu / configu rozwiązujący błąd | ✅ |
| `process-improvement` | Tylko zmiana w sposobie pracy (skill/profil/Joker) | ✅ |

Format wpisu:

```
- [IMP-YYYY-NNN] <tytuł>
- Data dodania: YYYY-MM-DD
- Źródło: daily-YYYY-MM-DD | Etap K Knowledge Routing
- Typ: <z tabeli powyżej>
- Opis problemu: ...
- Dowód: <ścieżka/sekcja>
- Proponowane rozwiązanie: ...
- Wpływ: HIGH|MEDIUM|LOW
- Koszt wdrożenia: S|M|L|XL
- Ryzyko: HIGH|MEDIUM|LOW
- Priorytet: P0|P1|P2|P3
- Status: OPEN | ACCEPTED | IN_PROGRESS | DONE | REJECTED
- Powiązania: <ADR-NNN | skill-name | daily-YYYY-MM-DD>
```

### Krok 12 — Etap J: Plan na kolejny dzień → `## Plan` w daily

```
## Plan na <YYYY-MM-DD+1>

### 3 najważniejsze zadania
1. ...
2. ...
3. ...

### 3 najważniejsze ryzyka
1. ...
2. ...
3. ...

### 3 decyzje wymagane od użytkownika
1. ...
2. ...
3. ...

### 3 usprawnienia (best ROI)
1. ...
2. ...
3. ...
```

### Krok 13 — Atomowy zapis stanu (tylko po pełnym sukcesie)

```bash
# względna ścieżka do $DATA/state/last-run.json
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
python3 - <<EOF
import json, pathlib
p = pathlib.Path("$DATA/state/last-run.json")
d = json.loads(p.read_text())
d["last_successful_run"] = "$NOW"
d["last_run_started_at"] = "$STARTED"
d["last_run_finished_at"] = "$NOW"
d["last_run_status"] = "ok"
d["last_run_window_start"] = "$WIN_START"
d["last_run_window_end"]   = "$WIN_END"
d["last_run_artifacts"]    = $ARTIFACTS_JSON
d["consecutive_failures"]  = 0
p.write_text(json.dumps(d, indent=2, ensure_ascii=False))
EOF
```

**Nie aktualizuj `last_successful_run` przy częściowym sukcesie.** Jeśli cokolwiek w krokach 4–12 się nie powiedzie → oznacz `consecutive_failures += 1` i NIE przesuwaj okna.

### Krok 14 — Raport dla użytkownika

Wyślij przez kanał dostarczania (origin lub home) zwięzłą wiadomość (max 30 linii):

```
🌙 Nightly Evolution — YYYY-MM-DD
Okno: <start> → <end>
PASS: x | WARN: y | FAIL: z

📋 Top 3 wnioski:
1. ...
2. ...
3. ...

⚠️ Ostrzeżenia:
- ...

💡 Propozycje (wymagają akceptacji):
- ...

🧭 Knowledge Routing (wymaga akceptacji rano):
- Pamięć: N kandydatów → sekcja "Knowledge Routing" w daily
- Nowe skille: N kandydatów → backlog (typ new-skill)
- Poprawa skilli: N kandydatów → backlog (typ skill-update)
- Dokumentacja: N kandydatów → backlog (typ project-doc)

🧠 Memory Hygiene (nowa sekcja, codziennie):
- MEMORY.md: <rozmiar> B / 22,000 B (<procent>%) → <OK|INFO|WARN|FAIL>
- 📊 Zmiana od ostatniej nocy: <diff> B (<+N lub -N>)
- Append-only do przeniesienia: N
- Stare sprawy pending-review > 7 dni: N (🟡), > 14 dni: N (🔴)
- Duplikaty MEMORY ↔ decisions: N
- (jeśli day == 1) → audyt miesięczny wykonany: tak/nie

📈 Trend (z memory-metrics.jsonl, ostatnie 7 dni):
- Min: <min>% | Max: <max>% | Avg: <avg>% | Trend: ↗️/↘️/→

❓ Decyzje wymagające Jokera:
- ...

Pliki: <krótka lista ścieżek>
```

### Krok 14a — Alert: skill sam się nie ładuje

Wywoływany **wyłącznie** gdy Krok 0.5 zakończył się z `success=False`. Zamiast standardowego raportu (Krok 14) wyślij krótką informację:

```
🚨 Nightly Evolution — skill not loadable

Przebieg 2026-07-24 03:00 UTC zakończył się bez wykonania procedury.
Powód: skill 'nightly-evolution' nie ładuje się przez `skill_view()`.

Error: <treść pola error>

Wymagana akcja:
1. Sprawdź symlink: `ls -la ~/.hermes/profiles/gaja/skills/<cat>/nightly-evolution/`
2. Sprawdź target: `cat <ścieżka z symlink>`
3. Jeśli HEOS się przemigrował (v1.1 → v1.2), zaktualizuj symlink:
   `cd ~/.hermes/profiles/gaja/skills/software-development/nightly-evolution && rm SKILL.md && ln -s /home/gaja/gaja-projekty/HEOS/skills/nightly-evolution.md SKILL.md`
4. Uruchom ponownie: `hermes cron run fec9c748bb19`

Raport: state/last-run.json → consecutive_failures zwiększony.
```

**NIE wykonuj** kroków 1–14 przy skill-missing. Inkrementuj tylko `consecutive_failures` i wyślij alert.

### Krok 14b — Alert: pamięć w stanie krytycznym (> 95% przez 3 kolejne przebiegi)

**Cel:** wykryć chroniczny stan krytyczny pamięci (nie jednorazowy skok).

**Logika:**

1. Przy każdym przebiegu sprawdź `wc -c` `~/.hermes/profiles/gaja/memories/MEMORY.md`.
2. Jeśli `%` > 95% (tj. > 20,900 B) → sprawdź `state/last-run.json` pole `consecutive_memory_critical`.
3. Jeśli pole == null lub < 2 → ustaw na `consecutive_failures + 1` (albo 1 jeśli null), ale **NIE wysyłaj alertu** (to może być jednorazowy spike po długiej sesji).
4. Jeśli pole >= 2 (czyli 3. kolejny przebieg z pamięcią > 95%) → **wyślij alert krytyczny** + zresetuj `consecutive_memory_critical` do 0.

**Treść alertu:**

```
🚨 Memory Hygiene — stan krytyczny (chroniczny)

MEMORY.md: <rozmiar> B / 22,000 B (<procent>%) przez 3 kolejne przebiegi.

To oznacza, że codzienne przebiegi nie wystarczają do utrzymania pamięci
w zdrowym stanie. Wymagana ręczna konsolidacja.

Co zrobić (zgodnie z instrukcją §3):
1. Przeczytaj `~/.hermes/profiles/gaja/memories/MEMORY.md` sekcje §1-§10.
2. Znajdź wpisy, które nie przechodzą filtra 7-punktowego (instrukcja §4).
3. Przenieś szczegóły projektów do:
   - `~/gaja-projekty/<proj>-arch/docs/`
   - `memory/projects-index.md`
4. Przenieś procedury wykonywalne do skilli.
5. Zostaw w `MEMORY.md` tylko trwałe ustalenia przekrojowe.
6. Po konsolidacji: `hermes cron run fec9c748bb19` żeby zweryfikować.

Następny przebieg zweryfikuje stan.
```

**Uwagi:**
- Alert krytyczny NIE blokuje przebiegu (Etap L i tak działa).
- `consecutive_memory_critical` jest oddzielne od `consecutive_failures` (to drugie = awarie, to pierwsze = stan pamięci).
- Po udanej konsolidacji (następny przebieg z pamięcią < 90%) → `consecutive_memory_critical` automatycznie nie jest inkrementowany.

## Przykłady

### Przykład 1: Pierwszy przebieg po instalacji

Sytuacja: `last_successful_run: null`. Okno = ostatnie 24h.

Wynik:
- `reports/daily/2026-07-24-summary.md` — krótka retrospektywa (może być niewiele jeśli mało sesji).
- `state/last-run.json` → `last_successful_run: 2026-07-24T03:18:00Z`.

### Przykład 2: Wykrycie martwego odnośnika w HEOS

Sytuacja: `HEOS/00-foundation/00-HEOS-OVERVIEW.md` linkuje do `01-domains/ai-ml/standards/SKILL.md`, który nie istnieje.

Wynik: wpis w Documentation Health z dowodem + wpis w backlogu `IMP-2026-NNN` z priorytetem P2, status OPEN.

### Przykład 3: Powtarzający się błąd

Sytuacja: 3× w ciągu dnia ten sam `cronjob.create` zwraca `attribute_error: 'NoneType' object has no attribute 'get'`.

Wynik: Error Intelligence → jeden wpis (nie trzy) z `Występował wcześniej: tak, 3× tego dnia`, plus backlog `IMP-YYYY-NNN` z prewencją.

### Przykład 5: Aktywny projekt (Etap K w praktyce)

Sytuacja: 4-dniowa sesja IMP2, w oknie 6 kandydatów na skill, 2 trwałe fakty o środowisku, 1 problem narzędzia.

Etap K klasyfikuje:

```
- Informacja: BNO085 wymaga I2C clock stretch, nie wspiera 400kHz
- Typ: project-doc | Trwałość: długoterminowa | Pewność: HIGH | Kontekst: projekt imp2-arch
- Docelowa ścieżka: ~/gaja-projekty/imp2-arch/docs/imu-limitations.md
- Akcja: zaproponuj (wymaga akceptacji)

- Informacja: Procedura flash ESP32 przez USB-CDC wymaga resetu w 1s oknie
- Typ: new-skill | Trwałość: długoterminowa | Pewność: HIGH | Kontekst: ogólne
- Powtórzeń: 4 (sesje 2026-07-20, 21, 22, 24)
- Docelowa ścieżka: skills/hardware/esp32-s3-flash/SKILL.md
- Akcja: zaproponuj

- Informacja: Joker przy krytycznym review chce ADR-y jeden-po-drugim z TL;DR
- Typ: memory | Trwałość: długoterminowa | Pewność: HIGH | Kontekst: profil gaja
- Docelowa ścieżka: memories/MEMORY.md (update istniejącego wpisu o preferencjach)
- Akcja: zaproponuj

- Informacja: micro-ROS UDP nie działa stabilnie (issue #732)
- Typ: adr | Trwałość: długoterminowa | Pewność: HIGH | Kontekst: projekt imp2-arch
- Docelowa ścieżka: ~/gaja-projekty/imp2-arch/decisions/0012-micro-ros-transport.md
- Akcja: zaproponuj

- Informacja: Dziś tooling: micro-ROS tools brak pakietu w apt
- Typ: session-only | Trwałość: jednorazowa | Pewność: HIGH
- Akcja: odrzuć (locka w toolchain to nie jest kandydat do pamięci)

- Informacja: 3× w tym tygodniu ten sam błąd import w Pythonie 3.13 (FileFinder)
- Typ: error-fix | Trwałość: długoterminowa | Pewność: HIGH | Kontekst: ogólne
- Docelowa ścieżka: backlog (typ error-fix), później skill/patch hermes-panel
- Akcja: zapisz automatycznie w backlogu (bo to problem narzędzia, nie decyzja arch.)
```

Po Etapie K: 4 kandydatów do akceptacji (memory, new-skill, adr, project-doc), 1 zapis automatyczny (backlog error-fix), 1 odrzucony.

Sekcja `## Knowledge Routing` w daily pokazuje listę 4 kandydatów z checkboxami. Joker rano robi `git apply` / `memory add` / `skill create` dla zaakceptowanych. Status danego IMP-YYYY-NNN zmienia się z OPEN → ACCEPTED → IN_PROGRESS → DONE.

### Przykład 6: Cicha noc (brak istotnej aktywności)

Sytuacja: okno ma tylko 1 krótką sesję CLI, 0 błędów, 0 zmian w HEOS/skills/memory.

Wynik:
- Krótki daily (max 5 linii): "Brak istotnych zmian. 1 sesja CLI, 0 błędów."
- BEZ sztucznych usprawnień.
- BEZ pełnego skanowania repo.
- Daily kończy się "**Plan na jutro**: nic do zaplanowania — czekam na aktywność."

## Typowe błędy

1. **Analiza całej historii** — tylko okno od `last_successful_run`. Pełny skan = marnowanie tokenów.
2. **Aktualizacja `last_successful_run` po częściowym sukcesie** — wtedy kolejne przebiegi nie widzą problemów. Najpierw pełny sukces, potem zapis.
3. **Wnioski bez dowodów** — "myślę że X" nie jest Lessons Learned. Wymagana ścieżka/linia albo brak wpisu.
4. **Szacowanie kosztów** — nie. `brak danych` lub konkretna liczba.
5. **Propozycje architektury wdrażane automatycznie** — zakazane. Tylko `reports/proposals/`.
6. **Sekrety w raportach** — natychmiast usunąć (PAT, tokeny, hasła, klucze API). Redakcja wsteczna → potwierdzić usunięcie w daily.
7. **Tworzenie cronów w trakcie nocnego przebiegu** — zakazane.
8. **Forsowny styl** — w raporcie dla użytkownika nie twierdzić że "wszystko świetnie" jeśli są WARN/FAIL. Uczciwie.

## Debugging

| Objaw | Przyczyna | Fix |
|---|---|---|
| `last-run.json` ma `last_successful_run` ale raporty puste | poprzedni przebieg nie doszedł do kroku 14 | sprawdź logi cron; ręcznie oznacz `consecutive_failures += 1` jeśli nie chcesz retry |
| Raporty są z wczoraj, dzisiaj brak | scheduler nie odpalił (gateway wyłączony?) | `hermes cron status` + `hermes gateway status` |
| Bardzo długi przebieg | pełny skan repo | zweryfikuj czy kroki 2–12 używają `last_successful_run` jako granicy |
| Backlog rośnie bez akceptacji | użytkownik nie czyta raportów | dashboard widoczny w raporcie dla użytkownika |

## Narzędzia

- `session_search` (FTS5 w `state.db`) — szybkie przeszukiwanie sesji.
- `search_files` (ripgrep) — przeszukiwanie HEOS/skills/memory.
- `read_file` — odczyt konkretnych plików.
- `terminal` — tylko do odczytu (`cat`, `git log`, `git diff --stat`), bez mutacji.
- `hermes cron status` — diagnostyka schedulera.

## Oficjalne źródła

- HEOS Master Prompt v1.1: `~/gaja-projekty/HEOS/00-foundation/HEOS-MASTER-PROMPT-v1.1.md`
- HEOS Using Skill: `~/gaja-projekty/HEOS/02-artifacts/skills/using-heos/SKILL.md`
- HEOS Skill Audit: `python3 ~/gaja-projekty/HEOS/03-quality/skill_audit.py <ścieżka>`
- Hermes Cron docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron
- ADR-002 (hub repo) i ADR-005 (granice profili)

## Wersjonowanie

- **v1.0** (2026-07-23) — pierwsza wersja, zainstalowana przez Jokera w profilu `gaja`.
- 14-etapowy workflow (A–J + Krok 0 + 13 + 14).
- Katalog danych: `~/.hermes/profiles/gaja/nightly-evolution/`.
- Cron: `Nightly Evolution`, `0 1 * * *`, workdir `~/gaja-projekty/HEOS`, delivery `origin`.
- **v1.1** (2026-07-24) — Knowledge Routing (Etap K).
- Dodany Krok 5.5 (Etap K) — klasyfikacja i routing wiedzy PRZED zapisem na stałe.
- Tabela routingu: rodzaj informacji → miejsce zapisu → kto zapisuje.
- Sekcja `## Knowledge Routing` w daily report z kandydatami do akceptacji.
- Format backlogu rozszerzony o pole `Typ` (10 wartości: `new-skill`, `skill-update`, `adr`, `adr-update`, `project-doc`, `heos-doc`, `memory`, `tracker`, `error-fix`, `process-improvement`).
- Statusy backlogu: `OPEN | ACCEPTED | IN_PROGRESS | DONE | REJECTED` (zamiast stałego `OPEN`).
- Krok 14 (Discord) zawiera dedykowaną sekcję `🧭 Knowledge Routing`.
- Bez zmian w: Krok 0.5 (self-check), Krok 13 (atomowy zapis), katalog danych, cron config.
- **v1.2.1** (2026-07-25) — Memory Hygiene v1.2.1 (incremental).
- Skill `memory-hygiene` v1.0.0 (nowy, class-level, standalone audyt pamięci na żądanie).
- Etap L: dodany pkt 6 "Baseline tracking" → `state/memory-metrics.jsonl` (append-only
    trend rozmiaru MEMORY.md, duplikatów, append-only, pending).
- Krok 14 (Discord): dodana sekcja `📊 Zmiana od ostatniej nocy` + `📈 Trend (7 dni)`.
- Reference: `skills/memory-hygiene/references/race-condition-signs.md` (7 sygnałów).
- Bez zmian w: Krok 0.5, Etap A-K+L+, katalog danych, cron config, harmonogram.

- **v1.2** (2026-07-25) — Etap L Memory Hygiene (audyt mojej pamięci operacyjnej).
- Dodany Krok 5.6 (Etap L) — codzienny audyt `~/.hermes/profiles/gaja/memories/`:
    rozmiar MEMORY.md, append-only do przeniesienia, sprawdzenie pending-review,
    wykrycie duplikatów między MEMORY.md a `memory/`.
- Dodany Krok 5.6b (Etap L+) — **audyt miesięczny** aktywowany gdy `day == 1`:
    pełen przegląd struktury memory/, wskaźników do repo, archiwizacja projektów
    zamkniętych, sync `memory/projects-index.md` z `~/gaja-projekty/README.md`.
- Sekcja `## Memory Hygiene` w daily (nowa, po `## Knowledge Routing`).
- Sekcja `🧠 Memory Hygiene` w raporcie Discord (Krok 14).
- Realizuje instrukcję Jokera "System samodzielnej higieny pamięci Gai" §10-12.
- Bez zmian w: Krok 0.5, Etap A-K, katalog danych, cron config, harmonogram.
- Krok 14b (alert) — gdy MEMORY.md > 95% limitu (22,000 B) przez 3 kolejne
    przebiegi, wysyłany jest alert do użytkownika (bo to jest stan krytyczny
    wymagający ręcznej konsolidacji).

## Checklisty

### Pre-run (automatyczny, w cronie)

- [ ] `state/last-run.json` istnieje i jest poprawnym JSON-em.
- [ ] Katalogi `reports/{daily,performance,errors,proposals}` istnieją.
- [ ] `hermes cron status` OK.

### Post-run (automatyczny)

- [ ] Plik `reports/daily/<dziś>-summary.md` istnieje.
- [ ] Plik `reports/performance/<dziś>.md` istnieje (może być "brak danych").
- [ ] Plik `reports/errors/<dziś>-errors.md` istnieje (może być pusty).
- [ ] `state/last-run.json` ma `last_run_status: ok` i zaktualizowane `last_successful_run`.
- [ ] Raport dostarczony na Discord (origin lub home).

### Pierwszy ręczny test (po instalacji)

- [ ] Skill ładuje się bez błędu (`skill_view(name="nightly-evolution")`).
- [ ] `state/last-run.json` ma `last_successful_run` po teście.
- [ ] Raport daily zawiera wszystkie 9 sekcji (A–J).
- [ ] Discord delivery OK.

## Najlepsze praktyki

1. **Okno analizy, nie pełna historia** — to jest nocny audyt, nie migracja bazy danych.
2. **Atomowy zapis stanu** — `last-run.json` to jedyne źródło prawdy o postępie. Połówkowy zapis = ukryte błędy.
3. **Bez sekretów w raportach** — nawet hashe nie, bo kolidują z audit trail. Lepiej `redagowane wstecznie`.
4. **Propozycje jako deliverables, nie zmiany** — Nightly Evolution nie wdraża, tylko raportuje.
5. **Uczciwość ponad optymizm** — `FAIL` to `FAIL`. Nie relabeluj.
6. **Jeden przebieg dziennie, nie więcej** — `repeat: ∞` z harmonogramem `0 1 * * *` to wystarczająca kadencja dla CI/doskonalenia.

## Bezpieczeństwo

**Nigdy bez akceptacji użytkownika:**
- Usuwanie plików (w tym raportów/propozycji po odrzuceniu).
- Modyfikacja `SOUL.md`, `config.yaml`, `.env`.
- Instalacja pakietów (`pip`, `npm`, `apt`).
- `git push`, `git merge`, `gh pr merge`.
- Tworzenie/modyfikacja zadań cron w trakcie nocnego przebiegu.

**Zawsze redact przed zapisem:**
- Tokeny, klucze API, hasła, PAT, SSH klucze.
- Nawet fragmenty kluczy (`sk-proj-…abc123`) — nie, nie, nie.

**Nigdy w raportach:**
- Wyjście `cat .env`, `printenv`, `env` (nawet częściowe).
- Fragmenty `auth.json`, `models_dev_cache.json`.

Jeśli wykryjesz sekret w wygenerowanym raporcie → nadpisz plik wersją zredagowaną i dopisz do daily: "Redakcja wsteczna: usunięto sekret z <ścieżka>".

## Lessons Learned

Wnioski zebrane z pierwszej instalacji (2026-07-23) i późniejszych przebiegów. Tylko to, co zmienia sposób pracy agenta.

1. **Okno analizy, nie cała historia** — pełny skan `state.db` lub repo przy każdym przebiegu = zmarnowane tokeny. `last_successful_run` jako granica okna jest **najważniejszą** optymalizacją tego skilla. Pierwszy przebieg (bez granicy) jest wyjątkiem, ale i tak powinien ograniczać się do ostatnich 24h.
2. **Atomowy zapis stanu jest warunkiem poprawności** — jeśli przebieg się uda w 80%, a `last_successful_run` się przesunie, kolejny przebieg straci 20% kontekstu. Dlatego zapis stanu MUSI być ostatnim krokiem po pełnym sukcesie.
3. **`brak danych` > fałszywe szacunki** — heurystyka "chyba kosztowało to około $X" zaniża wiarygodność całego raportu. Jeśli nie ma twardej liczby, napisz to wprost.
4. **Propozycje to deliverables, nie zmiany** — instynkt agenta po napisaniu `## Propozycja` to "wdrożyć to". Ten skill musi aktywnie zabraniać: propozycja ląduje w `reports/proposals/`, nigdy w kodzie/profilu. Inaczej nocny audyt zamieni się w nocne mutacje.
5. **Sekrety w raportach = pożar** — `cat .env`, `printenv`, `auth.json`, fragmenty kluczy API. Jedna chwila nieuwagi i `reports/daily/2026-07-24-summary.md` zawiera PAT, który Discord cache'uje przez `~/.hermes/profiles/gaja/cache/documents/`. Prewencja > leczenie: redact przed zapisem, wstecznie jeśli trzeba.
6. **Skill w HEOS, dane w profilu Hermesa** — to jest granica HEOS↔runtime. HEOS jest read-only dla nocnego procesu; wszystko co się zmienia, idzie do `~/.hermes/profiles/gaja/nightly-evolution/`. Bez tego HEOS zamieni się w śmietnik draftów.
7. **Cron z `origin` delivery respektuje thread użytkownika** — raport idzie tam, gdzie Joker zlecił instalację. To jest istotne dla niego (wątek `1529999134013264049`), nie domyślny kanał "ogólny".
8. **Raportowanie ≠ klasyfikacja** — nocny audyt v1.0 raportował wyniki, ale **nie decydował**, co z informacją zrobić. Efekt: duplikowanie (pamięć + skill), zaśmiecanie pamięci faktami projektowymi, procedury pozostające wyłącznie w raporcie. Etap K (v1.1) zamyka to jawną decyzją **typ → ścieżka → akcja → wymaga akceptacji (tak/nie)** dla każdego kandydata. Bez tego kroku Nocny Evolution = audytor który nie wykonuje triage.
9. **Filtr powtórzeń ma sens** — `powtórzeń ≥ 3` to minimum żeby procedura była kandydatem na skill. Bez tego filtra 50% projektów dostanie skill, który potem nikt nie używa. Filtr `trwałość × pewność × powtórzenia` jest konieczny, inaczej Etap K zamieni się w śmietnik "nowych skilli".
10. **Backlog musi mieć `Typ` jeśli ma być actionable** — samo `Status: OPEN` nie wystarczy. Bez `Typ` nie wiadomo, czy po akceptacji napisać skill, ADR, czy tylko commit w pamięci. Etap K jest źródłem `Typ` dla każdego wpisu.

## Powiązane

- **ADR-002** — hub repo + osobne repo per projekt (kontekst HEOS).
- **ADR-005** — granice profili Hermes (ten skill jest tylko w `gaja`).
- HEOS Master Prompt v1.1 — konstytucja (sekcja "Proces realizacji").
- HEOS Weekly Audit (skill `hermes-agent` + cron) — tygodniowy audyt HEOS Skills. Nightly Evolution jest codziennym odpowiednikiem dla runtime.

## Verification

Po zakończeniu nocnego przebiegu sprawdź czy raport jest kompletny:

- [ ] **Plik wygenerowany** — `~/.hermes/profiles/gaja/nightly-evolution/reports/daily/YYYY-MM-DD-summary.md` istnieje (data = bieżąca)
- [ ] **Wszystkie 8 etapów obecne** — A (Daily Retrospective), B (Lessons Learned), C (Self Review), D (Documentation Health), E (Architecture Review), F (Error Intelligence), G (Performance Report), H (Improvement Backlog). Brak którejkolwiek = raport niekompletny.
- [ ] **Brak sekretów** — `grep -iE '(api[_-]?key|token|password|bearer)\s*[:=]\s*["\x27]?[A-Za-z0-9_-]{16,}' reports/daily/YYYY-MM-DD-summary.md` zwraca 0. Jedyny sposób na weryfikację przed Discord cache.
- [ ] **Propozycje w dedykowanym katalogu** — `ls reports/proposals/ | wc -l` > 0 jeśli cokolwiek zaproponowano. Propozycje NIE są w summary.
- [ ] **Backlog z `Typ`** — każdy wpis w Improvement Backlog ma `Typ: skill | memory | adr | commit` (v1.1 triage). Brak Typ = wpis nie jest actionable.
- [ ] **Log bez crash** — `journalctl -u hermes-cron --since "8h ago" | grep -iE 'evolution|nightly' | grep -iE 'error|traceback'` → 0 wyników. Cron job nie może crashować w środku nocy.
- [ ] **Delivery zgodna z origin** — raport dotarł do właściwego wątku (Discord / Home / local) zgodnie z konfiguracją cron job. Nie do domyślnego kanału.
- [ ] **Czas trwania < 30 min** — log powinien pokazywać czas startu i końca. Jeśli >30 min nocny cron nachodzi na dzień = zmniejsz scope lub zwięź treść.

Fail gdy: brak pliku, brak etapu, znaleziono sekrety, lub cron nie zakończył się przed 6:00.

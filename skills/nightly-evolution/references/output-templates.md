# Output Templates — Kroki 4-12 (Etapy B-J)

> Wyciągnięte z `nightly-evolution.md` v1.5.0 (2026-07-28). Załadować tylko gdy nocny przebieg dociera do któregokolwiek z kroków 4-12. Główny `SKILL.md` ma overview + odnośnik tutaj.

Te template'y to **formaty wyjściowe** dla raportów nocnego przebiegu. Każdy krok ma obowiązkowe sekcje (treść może być "brak" jeśli faktycznie nic do raportowania), ale struktura musi pozostać dla downstream parsingu (np. Etap K czyta sekcję "Lessons Learned").

## Użycie

1. Otwórz ten plik gdy dojdziesz do Kroku 4.
2. Dla każdego etapu (B-J) zastosuj odpowiedni template do okna z Kroku 1.
3. Nie pomijaj obowiązkowych sekcji — nawet jeśli treść to "brak".

## Kontekst

W v1.4.0 (split per ADR-009) kroki 4-12 zostały w głównym `SKILL.md` jako template'y inline. To sprawiało, że główny plik miał 498 linii (z czego 225 linii = 45% to były same template'y markdown). W v1.5.0 template'y są w tym reference, a główny `SKILL.md` ma tylko overview + odnośnik.

**Korzyść:** główny SKILL.md spadł z 498 → 292 linii (~41% redukcji). Przy ~30 nocnych przebiegach miesięcznie to ~120K tokenów/rok na pełnym vs ~70K na nowym SKILL.md, **z dodatkowymi ~20K jeśli reference ładowane są wszystkie raz** (typowo tylko 1 reference per use case, np. tylko `output-templates.md` podczas Kroku 4).

---

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

> 📂 Załaduj `references/etap-K-knowledge-routing.md` — pełna procedura routingu, tabela typ→ścieżka→akcja, sekcja `## Knowledge Routing` w daily.

Krótko: dla każdego kandydata z okna (Lessons Learned, powtarzający się błąd, procedura, problem narzędzia, kandydat na skill, nowy trwały fakt) wypełnij rekord klasyfikacji (typ / trwałość / pewność / akcja). Szczegóły filtrów i tabeli routingu w reference.

### Krok 5.6 — Etap L: Memory Hygiene (codzienny audyt pamięci)

> 📂 Załaduj `references/etap-L-memory-hygiene.md` — pełna procedura: 6 sprawdzeń (rozmiar, append-only, pending-review wiek, duplikaty MEMORY↔decisions, baseline tracking, aktywne audyty miesięczne).

Krótko: sprawdź `~/.hermes/profiles/gaja/memories/`. Dodaj do daily sekcję `## Memory Hygiene` z 5 punktami (stan pamięci, TODO przeniesienia, stare sprawy, duplikaty, akcja wymagana).

### Krok 5.6b — Etap L+: Audyt miesięczny

Aktywny **wyłącznie** gdy `date +%d` zwraca `"01"`. Rozszerza Krok 5.6 o 5 dodatkowych sprawdzeń (sync z hub README, archiwizacja, duplikaty przekrojowe, martwe wskaźniki, propozycje zmian). Szczegóły w `references/etap-L-memory-hygiene.md` §Krok 5.6b.

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

```markdown
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

```markdown
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


# Alerts, Przykłady, Typowe błędy i Operacje pomocnicze

> Wyciągnięte z `nightly-evolution.md` v1.2.1 (2026-07-25). Załadować tylko gdy nocny przebieg potrzebuje alertów (Krok 14a/14b), przykładów lub operacji pomocniczych (typowe błędy, debugging, bezpieczeństwo). Główny `SKILL.md` ma tylko overview + odnośnik tutaj.

## Krok 14a — Alert: skill sam się nie ładuje

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

## Krok 14b — Alert: pamięć w stanie krytycznym (> 95% przez 3 kolejne przebiegi)

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

## Powiązane

- `nightly-evolution/SKILL.md` (główny plik) — Krok 14, Krok 14a/14b w workflow
- `references/etap-K-knowledge-routing.md` — Etap K (Krok 5.5)
- `references/etap-L-memory-hygiene.md` — Etap L (Krok 5.6, Krok 5.6b) + Krok 14b

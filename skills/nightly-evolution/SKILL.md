---
name: nightly-evolution
description: Uruchamiaj przy nocnym, automatycznym przebiegu analizy własnej pracy (03:00). Generuje Daily Retrospective,
  Lessons Learned, Self Review, Documentation Health, Architecture Review, Error Intelligence, Performance Report, Improvement
  Backlog i plan na kolejny dzień. Load ONLY when the Nightly Evolution cron job fires — never load this skill ad-hoc for
  user tasks.
status: accepted
heos_version: '1.4.0'
data_root: ~/.hermes/profiles/gaja/nightly-evolution
type: skill
id: skill-nightly-evolution
title: Nightly Evolution
owner: gaja
created_at: '2026-07-24'
updated_at: '2026-07-28'
review_due: '2027-01-23'
version: 1.4.0
heos_standard_version: "1.2"
tags:
- cross-cutting
related:
- skill-using-chm
- adr-002
- adr-005
- adr-008
- adr-009
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

**Poza zakres (bez zgody użytkownika):**

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

## Struktura pliku

Od wersji 1.4.0 (split per ADR-009) skill ma strukturę katalogową:

```
skills/nightly-evolution/
├── SKILL.md                          ← ten plik (overview + workflow + verification, ~250 linii)
└── references/
    ├── etap-K-knowledge-routing.md   ← Krok 5.5 (Knowledge Routing, ~100 linii)
    ├── etap-L-memory-hygiene.md      ← Krok 5.6 + 5.6b (Memory Hygiene, ~140 linii)
    └── alerts-and-examples.md        ← Kroki 14a/14b + Przykłady 1-6 + Typowe błędy + Debugging + Checklisty + Bezpieczeństwo, ~330 linii
```

**Zasada:** ładuj `SKILL.md` zawsze. Ładuj `references/<plik>` tylko w krokach, które go używają. To zmniejsza zużycie kontekstu o ~70% vs poprzedni flat `nightly-evolution.md` (957 linii).

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

> 📂 Załaduj `references/alerts-and-examples.md` §"Krok 14a" — treść alertu + 4 kroki naprawy.

Krótko: przy `success=False` z Krok 0.5 → inkrementuj `consecutive_failures`, wyślij alert do `origin`, zakończ.

### Krok 14b — Alert: pamięć w stanie krytycznym

> 📂 Załaduj `references/alerts-and-examples.md` §"Krok 14b" — logika 3 kolejnych przebiegów > 95% + treść alertu.

Krótko: sprawdź `consecutive_memory_critical` w `state/last-run.json`. Jeśli >= 2 (3. kolejny przebieg > 95%) → wyślij alert krytyczny + zresetuj.

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
- **ADR-008** — Atomic Write Contract (`_heos_atomic.py`, dziedziczony przez `update_quality.py`).
- **ADR-009** — HEOS v1.4 scope (uzasadnia split tego skilla).
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

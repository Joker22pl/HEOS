# Etap K — Knowledge Routing (klasyfikacja i routing wiedzy)

> Wyciągnięte z `nightly-evolution.md` v1.2.1 (2026-07-25). Załadować tylko gdy nocny przebieg dociera do Krok 5.5. Główny `SKILL.md` ma tylko overview + odnośnik tutaj.

## Krok 5.5 — Etap K: Knowledge Routing (klasyfikacja i routing wiedzy)

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

### Tabela routingu (reguła domyślna)

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

### Dozwolone akcje automatyczne (bez zgody Jokera)

- Zapis do `reports/daily/<dziś>-summary.md`
- Zapis do `reports/errors/`
- Zapis do `reports/performance/`
- Append do `state/improvement-backlog.md` (status OPEN)
- Append do `state/last-run.json`

### Zakaz automatycznego zapisu (wymaga akceptacji Jokera)

- Zapis do `memories/` (pamięć profilu)
- Tworzenie / modyfikacja jakiegokolwiek skilla
- Tworzenie / modyfikacja ADR
- Zmiany w dokumentacji projektu (`~/gaja-projekty/<proj>/...`)
- Zmiany w repozytorium HEOS
- Zmiany w `SOUL.md`, `USER.md`, `config.yaml`, `.env`
- Zmiany w trackerach projektowych (Jira, Linear, kanban)
- Commit / push / merge

### Co dodać do daily report (nowa sekcja `## Knowledge Routing`)

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

### Dlaczego ten krok jest potrzebny

Przed Etapem K nocny przebieg raportował, ale **nie rozstrzygał**, co z każdą informacją zrobić. To prowadziło do:

- duplikowania (ten sam wniosek w pamięci i skillu),
- zaśmiecania pamięci faktami projektowymi (np. aritmetika enkodera w pamięci ogólnej),
- procedur pozostających wyłącznie w raporcie i nigdy nie trafiających do skilla,
- backlogu zamiast właściwego artefaktu (ADR / skill / doc).

Etap K rozwiązuje to jawną decyzją: **typ → ścieżka → akcja → wymaga akceptacji (tak/nie)**.

### Pułapka: klasyfikacja pod presją aktywności

Projekt intensywnie używany (np. IMP2) w ciągu dnia wygeneruje 5-10 kandydatów do skilla. Nie wszystkie są krytyczne. Filtr:

- `trwałość = jednorazowa` → `session-only` (nie zapisuj)
- `trwałość = średnioterminowa` → `audit-log` (zapisz w raporcie, nie w pamięci)
- `trwałość = długoterminowa` + `pewność = HIGH` + `powtórzeń ≥ 3` → `skill` lub `ADR`
- `trwałość = długoterminowa` + `pewność = HIGH` + `powtórzeń < 3` → `pozostaw-w-raporcie` (za mało danych)
- `trwałość = długoterminowa` + `pewność = MEDIUM` → `zaproponuj` (wymaga akceptacji)

Bez tego filtra 50% projektów dostanie skill, który potem nikt nie używa.

**Konsumpcja w kolejnych krokach:** Po Etapie K (Krok 5.5) codzienny raport MUSI zawierać przyrostek `## Knowledge Routing` (wzór powyżej). Wpisy w backlogu (Krok 11) dziedziczą `Typ` z rekordów Etapu K. Krok 14 (Discord) posiada sekcję `🧭 Knowledge Routing`.

## Powiązane

- `skills/memory-hygiene/SKILL.md` — ten sam typ audytu na żądanie (manual), Etap L działa codziennie
- `nightly-evolution/SKILL.md` (główny plik) — Krok 5 + Krok 5.5 w workflow
- ADR-002, ADR-005 — kontekst granic (HEOS vs profil `gaja`)

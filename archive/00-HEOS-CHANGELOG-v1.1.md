# HEOS — Changelog i Uzasadnienie Zmian v1.0 → v1.1

**Wersja:** 1.1
**Data:** 2026-07-23
**Źródło zmian:** Krytyczna analiza RFA (`~/.hermes/profiles/gaja/cache/heos_rfa_review_v1.0.md`)

---

## Podsumowanie

HEOS v1.0 → v1.1 to **9 zmian** podzielonych na 3 kategorie:

| Kategoria | Liczba | Charakter |
|---|---|---|
| 🔴 Krytyczne (muszą być) | 3 | Architektura, egzekucja |
| 🟡 Ważne (powinny być) | 3 | Standaryzacja, lifecycle |
| 🟢 Kosmetyczne (nice-to-have) | 3 | Czytelność, porządek |

**Wynik netto:** HEOS v1.0 był **manifestem wartości**. HEOS v1.1 jest **systemem operacyjnym z egzekucją**.

---

## Zmiana #1 (🔴 Krytyczna): Warstwa Enforcement

### Co było w v1.0
> "Każde zadanie realizuj według schematu: Analiza → Plan → Implementacja → Testy → Walidacja → Dokumentacja → Self Review → Lessons Learned."
>
> "Zadanie jest zakończone dopiero gdy działa, jest przetestowane, udokumentowane, oceniono ryzyka, wykonano Self Review i zapisano Lessons Learned."

### Co jest w v1.1
Dodana **warstwa Enforcement** z automatycznymi bramkami:

| Poziom | Mechanizm | Częstotliwość |
|---|---|---|
| P0 (Bezpieczeństwo) | `pre-commit` (gitleaks, detect-secrets) | przed każdym commitem |
| P1 (Poprawność) | `skill_audit.py --strict` w CI | per PR |
| P2 (Jakość) | `skill_audit.py` (raport) | co 7 dni (cron) |
| P3 (Skalowalność) | ręcznie (code review) | per ADR |
| P4 (Optymalizacja) | ręcznie (profiling) | ad hoc |

Narzędzia:
- `03-quality/skill_audit.py` — walidator 15-punktowego szablonu
- `03-quality/heos_lint.py` — walidator cross-references
- `03-quality/heos_weekly_audit.py` — raport tygodniowy + Discord
- Cron job (co 7 dni, poniedziałek 9:00 UTC)

### Uzasadnienie

**v1.0 problem:** dokument ma 31 zasad, 5 ról, 7 trybów, 15-punktowy szablon Skilla, 7 modułów — ale **zero mechanizmu, który sprawdza, czy te zasady są faktycznie stosowane**.

**Dowód empiryczny (2026-07-23):** Pierwszy audyt 87 istniejących Skillsów w profilu Hermesa dał **0/87 PASS, 87/87 FAIL**. To dowodzi że **HEOS v1.0 był martwym manifestem** — zasady istniały, ale nikt ich nie egzekwował.

**v1.1 rozwiązanie:** automatyczne bramki (cron + CI + pre-commit) sprawiają że **nie da się zignorować** szablonu Skilla. Baseline 0% → metryka postępu.

**Cytat z analizy krytycznej:**
> "Bez automatycznego gate'a dokument zamieni się w manifest, który piszesz, czytasz raz, i ignorujesz."

---

## Zmiana #2 (🔴 Krytyczna): Architektura dwuwymiarowa

### Co było w v1.0
```
00-constitution
01-engineering
02-development
03-robotics
04-ai
05-playbooks
06-quality
07-knowledge
```

Płaska, jednowymiarowa, numeryczna hierarchia.

### Co jest w v1.1
```
00-foundation/      (Konstytucja, EP-*, P0–P4)
01-domains/         (embedded, robotics, ai-ml, infrastructure, web)
02-artifacts/       (skills, decision-records, playbooks, checklists, lessons-learned)
03-quality/         (skill_audit, heos_lint, weekly_audit, reports)
04-knowledge-graph/ (registry, cross-cutting indeksy)
```

Dwuwymiarowa: **domena wiedzy (B)** × **typ artefaktu (A)**.

### Uzasadnienie

**v1.0 problem 1:** Płaska numeracja nie skaluje się. Po 10 modułach zaczyna się renumeracja (wstawienie czegoś między 03 a 04 = zmiana wszystkich następnych).

**v1.0 problem 2:** Pozorna separacja domen. `engineering` vs `development` vs `robotics` to **perspektywy tego samego projektu**, nie rozłączne domeny. Trzymanie ich osobno wymusza albo **duplikację** (ten sam koncept w dwóch miejscach) albo **sztuczne kryteria** (co gdzie leży).

**v1.0 problem 3:** `05-playbooks` wchodziło w `01-engineering`. Playbook to **typ dokumentu**, nie domena. Mieszanie domen z typami dokumentów w jednej osi to antywzorzec.

**v1.1 rozwiązanie:** dwie osie. Skill dot. robotyki → `01-domains/robotics/skills/` + wpis w `02-artifacts/skills/registry.yaml` (wskaźnik, bez duplikacji). Jeden koncept = jedno miejsce autorytatywne + wskaźniki w innych miejscach.

**Cytat z analizy krytycznej:**
> "Skill dot. robotyki trafia do `01-domains/robotics/skills/` i jest zarejestrowany w `02-artifacts/skills/registry.yaml` jako wskaźnik. Bez duplikacji treści."

---

## Zmiana #3 (🔴 Krytyczna): Decision Records (ADR)

### Co było w v1.0
> "Przy wielu możliwych rozwiązaniach przygotuj porównanie uwzględniające bezpieczeństwo, niezawodność, koszt, wydajność, możliwość rozbudowy, dokumentację i aktywność społeczności, a następnie uzasadnij rekomendację."

### Co jest w v1.1
Dodany moduł `02-artifacts/decision-records/` z szablonem ADR (Michael Nygard, 2011):
- **Status** (Proposed | Accepted | Superseded | Deprecated)
- **Kontekst** (co rozwiązujemy)
- **Decyzja** (co wybraliśmy)
- **Uzasadnienie** (tabelka porównawcza)
- **Konsekwencje** (pozytywne + negatywne/ryzyka)
- **Alternatywy** (odrzucone)
- **Kiedy rewizja** (warunek powrotu)
- **Powiązane** (ADR-NNN, Skills)

Plus 5 przykładowych ADR z naszej historii:
- ADR-001: MicroPython dla ESP32-S3-PICO
- ADR-002: Hub repo + osobne repo per projekt
- ADR-003: Konwencja commitów po polsku
- ADR-004: Cookiecutter + pre-commit
- ADR-005: Granice profili Hermes

### Uzasadnienie

**v1.0 problem:** dokument wspomina o "frameworku decyzji" (7 kryteriów) ale **nie ma persystencji tych decyzji**. Za pół roku nie będziesz pamiętał, dlaczego wybrałeś MicroPython zamiast Arduino.

**v1.1 rozwiązanie:** ADR to standard branżowy (Michael Nygard, 2011 — https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions). Bez niego każda decyzja to "pamięć miękka" — ginie przy rotacji kontekstu lub nowym agencie.

**Bonus:** 5 ADR z naszej historii (z 23-07-2026) daje **natychmiastową wartość** — wszystkie decyzje z ostatnich sesji są teraz udokumentowane i przeszukiwalne.

---

## Zmiana #4 (🟡 Ważna): Standard Skilla — 7 obowiązkowych + 8 opcjonalnych

### Co było w v1.0
Standard Skilla miał **15 obowiązkowych pól**:
> Cel, Zakres, Kiedy używać, Kiedy nie używać, Workflow, Checklistę przed i po, Najlepsze praktyki, Typowe błędy, Debugging, Biblioteki, Narzędzia, Przykłady, Oficjalne źródła, Lessons Learned i Wersjonowanie.

### Co jest w v1.1
**7 obowiązkowych** + **8 opcjonalnych** (z fallbackiem "see also: skills/X"):

| Obowiązkowe (7) | Opcjonalne (8) |
|---|---|
| Cel | Typowe błędy |
| Zakres | Debugging |
| Kiedy używać | Biblioteki |
| Kiedy nie używać | Narzędzia |
| Workflow | Oficjalne źródła |
| Przykłady | Wersjonowanie |
| Lessons Learned | Checklisty |
| | Najlepsze praktyki |

### Uzasadnienie

**v1.0 problem:** 15 pól = bariera wejścia. 5 z nich zawsze puste lub kopiowane z innego Skilla (bo nikt nie chce pisać 15 sekcji za każdym razem).

**Dowód empiryczny:** Pierwszy audyt 87 Skillsów w profilu Hermesa:
- **0/87 miało wszystkie 15** obowiązkowych
- 87/87 miało `Przykłady` (zwykle 1 kawałek kodu)
- 60/87 miało `Workflow` (często aliasowane jako "How to use")
- 18/87 miało `Lessons Learned` (często puste)

**v1.1 rozwiązanie:** 7 obowiązkowych to **realistyczny próg** — każdy dobry Skill je ma. 8 opcjonalnych z fallbackiem "see also" eliminuje kopiowanie.

**Statystyka po zmianie:** Pierwszy Skill w HEOS (esp32-s3-micropython-blink) napisany od zera z nowym standardem = **7/7 obowiązkowych + 7/8 opcjonalnych** za pierwszym razem. To dowodzi że próg jest osiągalny.

---

## Zmiana #5 (🟡 Ważna): Mechanizm deprecation

### Co było w v1.0
> "Każdy moduł ma być wersjonowany i rozwijany niezależnie."

Brak słowa o **wycofywaniu** wiedzy.

### Co jest w v1.1
Każdy Skill ma w frontmatter pole:
```yaml
status: active | deprecated | superseded
superseded_by: skills/new-skill-name  # opcjonalne
```

**Zasada:** Skill `deprecated` pozostaje w katalogu (dla historii), ale jest pomijany w `skill_view()` i oznaczony w raportach. `superseded_by` wskazuje następce.

**Cron raport tygodniowy** może (TODO) automatycznie raportować ile Skillsów jest `deprecated` vs `active`.

### Uzasadnienie

**v1.0 problem:** Po 3 latach HEOS pełen Skillsów do bibliotek które umarły (np. ORM-y które są martwe). Knowledge rot to **cichy zabójca systemów wiedzy**.

**v1.1 rozwiązanie:** jawny status + ścieżka do następcy. Knowledge graph (przyszłość) może automatycznie przekierowywać deprecated → successor.

---

## Zmiana #6 (🟡 Ważna): Role vs Tryby rozdzielone

### Co było w v1.0
Sekcja "Role" zawierała 5 ról + 7 trybów razem:
> "Korzystaj wyłącznie z pięciu ról: Chief Architect, Software Engineer, Robotics Engineer, QA & Reviewer, Documentation Engineer. Dobieraj role automatycznie do zadania i jasno określaj ich odpowiedzialność."
>
> "Obsługuj tryby: Architect, Research, Code, Reviewer, Debugger, Documentation, Teacher. Wybieraj odpowiedni tryb automatycznie."

### Co jest w v1.1
Rozdzielone na dwie sekcje:

**Persony (kim jestem) — 5:**
- Chief Architect, Software Engineer, Robotics Engineer, QA & Reviewer, Documentation Engineer

**Aktywności (co robię) — 7:**
- Architect, Research, Code, Reviewer, Debugger, Documentation, Teacher

Przykład kombinacji: "Robotics Engineer in Debugger mode" = debuguję problem z hardwarem.

### Uzasadnienie

**v1.0 problem:** "rola" i "tryb" były wymieszane. "Architect" to jednocześnie rola (Chief Architect) i tryb (Architect mode). Przy zadaniu "zbuduj robota" — jestem Robotics Engineer (rola) w trybie Code? Architect? Obie odpowiedzi działały, ale nie było jasne.

**v1.1 rozwiązanie:** Person × Activity = precyzyjne określenie. Jak typy MIME — `image/png`, `text/plain` — orthogonally composable.

---

## Zmiana #7 (🟢 Kosmetyczna): "Nie twórz całego systemu jednocześnie" jako krok 0

### Co było w v1.0
> "Nie twórz całego systemu jednocześnie.
> Najpierw: 1. Przeanalizuj... 2. Zaproponuj... 3. Zaproponuj roadmapę... 4. Wskaż ulepszenia... 5. Dopiero po akceptacji rozpocznij tworzenie..."

To było na **końcu** dokumentu, jako "Cel operacyjny".

### Co jest w v1.1
Numer **0** w "Cel operacyjny", nie werset na końcu.

### Uzasadnienie

Zasada "nie rób wszystkiego naraz" to **najważniejsza reguła** przy budowie systemu. v1.0 ją ukrywał jako werset. v1.1 robi ją **pierwszym krokiem** — explicit reminder.

---

## Zmiana #8 (🟢 Kosmetyczna): "Poziom pewności" z uzasadnieniem

### Co było w v1.0
> "Oceniaj ważne rekomendacje w skali od ★☆☆☆☆ do ★★★★★."

### Co jest w v1.1
Dodane: **obowiązek uzasadnienia oceny jednym zdaniem**. Plus tabela interpretacji.

### Uzasadnienie

Bez uzasadnienia "★★★★★" to pusta etykieta. Z uzasadnieniem to audytowalny claim.

---

## Zmiana #9 (🟢 Kosmetyczna): Sekcja migracji v1.0 → v1.1

### Co było w v1.0
Nic (v1.0 było pierwszą wersją).

### Co jest w v1.1
Dodana sekcja "Migracja z v1.0" z tabelką elementów i akcji. Stary dokument (DOCX) zachowany w `00-foundation/archive-...`.

### Uzasadnienie

Zasada **non-breaking change** — stare Skillsy nie muszą być migrowane od razu. `skill_audit.py` ma aliasy dla wariantów nazw sekcji (np. "When to use" = "Kiedy używać"). Pełna migracja to projekt na tygodnie.

---

## Czego NIE zmieniono (i dlaczego)

### Hierarchia P0–P4 (Bezpieczeństwo > Poprawność > Jakość > Skalowalność > Optymalizacja)
Bez zmian. To rzadkość w dokumentach tego typu i bardzo zdrowy fundament. Nie ruszać.

### Proces Analiza → Plan → Impl → Test → Walidacja → Dokumentacja → Self Review → Lessons Learned
Bez zmian. Solidny cykl. Zostaje.

### Kolejność źródeł wiedzy (Research)
Bez zmian. Trafna. Zostaje.

### Definition of Done
Bez zmian. Lista 6-punktowa zostaje. Każdy element jest sprawdzalny.

### 10 zasad fundamentalnych
Bez zmian. Są w v1.1 verbatim, w tej samej kolejności.

### Standard projektu (struktura README/CHANGELOG/TODO/docs/...)
Bez zmian. Działa. Nie ma powodu ruszać.

---

## Macierz: v1.0 vs v1.1

| Element | v1.0 | v1.1 | Zmiana |
|---|---|---|---|
| Warstwa Enforcement | ❌ brak | ✅ 3 narzędzia + cron | 🔴 nowa |
| Architektura modułów | płaska 8-elementowa | dwuwymiarowa 5-sekcyjna | 🔴 przebudowa |
| ADR | ❌ brak | ✅ 5 ADR + template | 🔴 nowa |
| Standard Skilla | 15 obowiązkowych | 7 obowiązkowych + 8 opcjonalnych | 🟡 uproszczenie |
| Deprecation Skills | ❌ brak | ✅ status w frontmatter | 🟡 nowa |
| Role vs Tryby | wymieszane | rozdzielone (Person × Activity) | 🟢 porządek |
| "Nie twórz od razu" | werset na końcu | krok 0 | 🟢 prominence |
| Poziom pewności | ★–★★★★★ | ★–★★★★★ + uzasadnienie | 🟢 doprecyzowanie |
| Sekcja migracji | n/a | tabela akcji | 🟢 meta |
| Hierarchia P0–P4 | ✅ | ✅ | bez zmian |
| Proces realizacji | ✅ | ✅ | bez zmian |
| 10 zasad fundamentalnych | ✅ | ✅ | bez zmian |
| Definition of Done | ✅ | ✅ | bez zmian |
| Standard projektu | ✅ | ✅ | bez zmian |

---

## Metryka wpływu zmian

| Metryka | Przed v1.1 | Po v1.1 | Zmiana |
|---|---|---|---|
| Liczba mechanizmów egzekucji | 0 | 3 (+ cron) | +∞ |
| Skills w HEOS spełniające standard | 0/87 | 0/87 (87 to profil Hermesa) | — |
| Skills w HEOS pisane od zera wg standardu | — | 2/2 PASS | 100% |
| ADR udokumentowane | 0 | 5 | +5 |
| Cross-references walidowane automatycznie | ❌ | ✅ heos_lint.py | +1 |
| Cotygodniowy audyt | ❌ | ✅ cron | +1 |

---

*Patrz też: `00-HEOS-ARCHITECTURE.md` (powiązania), `00-HEOS-OPEN-DECISIONS.md` (co jeszcze nie wiemy).*
*Źródło krytycznej analizy: `~/.hermes/profiles/gaja/cache/heos_rfa_review_v1.0.md`*

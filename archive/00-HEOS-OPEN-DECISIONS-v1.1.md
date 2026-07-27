# HEOS — Otwarte Decyzje Architektoniczne

**Data:** 2026-07-23
**Cel:** Lista rzeczy które **wymagają jeszcze wyboru lub dopracowania** przed pełnym użyciem HEOS w produkcji.

Każda decyzja ma:
- **Status** (Open / Decided / Deferred)
- **Priorytet** (P0–P3)
- **Opcje** do rozważenia
- **Rekomendację** Gaja (z uzasadnieniem)
- **Decydenta** (Joker / Gaja / obaj)

---

## ODA-1: Multi-profile HEOS (gaja vs gaja-it vs gaja-med)

| Pole | Wartość |
|---|---|
| **Status** | Open |
| **Priorytet** | P3 (niski — nikt nie woła o to teraz) |
| **Blokuje** | Nic krytycznego |

### Kontekst

HEOS jest w profilu `gaja` (Jokera). Profile `gaja-it` (bot narzędziowy) i `gaja-med` (Asia, lekarka) istnieją ale nie mają HEOS. Pytanie: czy każdy profil ma **własny HEOS** czy **jeden współdzielony**?

### Opcje

**A) Jeden HEOS współdzielony dla wszystkich profili**
- ✅ Mniej duplikacji
- ✅ Spójne standardy
- ❌ Łamie granice profili (ADR-005)
- ❌ HEOS dla Asji (dane medyczne) + HEOS dla Jokera (roboty) to **dwa różne światy**

**B) Każdy profil ma własny HEOS (osobne repo lub osobne foldery)**
- ✅ Granice profili zachowane
- ✅ Każdy HEOS może mieć inne domeny
- ❌ Duplikacja struktury
- ❌ Trudniej utrzymać spójność

**C) HEOS jest w `gaja`, inne profile konsumują read-only**
- ✅ Jedno źródło prawdy
- ✅ Inne profile nie zapisują (zero ryzyka konfliktu)
- ❌ Konsumpcja read-only to hack

**D) HEOS w `gaja-projekty` (repo), profile importują przez git submodule**
- ✅ Reużywalność
- ✅ Każdy profil może mieć własne rozszerzenia
- ❌ Submodules to ból (głównie git)

### Rekomendacja Gaja

**B (każdy profil ma własny HEOS)**, ale z **wspólnym rdzeniem**.

Struktura:
```
gaja/HEOS/         # pełny HEOS
gaja-it/HEOS/      # subset (np. tylko infrastructure, no robotics)
gaja-med/HEOS/     # inny subset (np. tylko ai-ml, clinical-guidelines)
```

Wspólny rdzeń (`00-foundation/`, narzędzia `03-quality/`) jest współdzielony **przez kopiowanie** przy setupie profilu. Aktualizacje rdzenia to **świadomy ruch** Jokera.

### Decydent

Joker (kiedy będzie chciał ruszyć ten temat).

### Blokuje

Nie. Na dziś HEOS jest w `gaja` i tam zostaje. Multi-profile to F4 w roadmapie.

---

## ODA-2: Czy Skillsy profilu Hermesa migrują do HEOS?

| Pole | Wartość |
|---|---|
| **Status** | Open |
| **Priorytet** | P2 (średni — wpływa na F2 roadmapy) |
| **Blokuje** | F2 metryki (50% PASS) |

### Kontekst

87 Skillsów w `~/.hermes/profiles/gaja/skills/` to **Skillsy frameworka Hermes** — pisane dla modelu AI, automatycznie ładowane. HEOS ma własne 2 Skillsy w `01-domains/embedded/skills/`. Pytanie: czy te 87 to **część HEOS** czy **osobna rzecz**?

### Opcje

**A) Migruj wszystkie 87 do HEOS**
- ✅ Jedno miejsce
- ❌ Duplikacja z profilem Hermesa
- ❌ Hermes ma własny lifecycle dla Skills (auto-load)

**B) Zostaw w profilu, HEOS tylko audytuje**
- ✅ Profile Hermesa zarządzane przez Hermes
- ✅ HEOS ma audyt (`skill_audit.py`) ale nie zarządza
- ❌ Dwa źródła prawdy o standardzie Skilla

**C) Hybryd: wzorcowe Skillsy w HEOS, kopie/override w profilu**
- ✅ Wzorce w HEOS, per-profile customization
- ❌ Submodule / symlink complexity

### Rekomendacja Gaja

**B (zostaw w profilu, HEOS audytuje)**. Powody:
1. Hermes Agent ma swój lifecycle Skillsów — nie chcemy go łamać
2. HEOS to **standard** — audyt + rekomendacje, nie hosting
3. Profile-specific customization (np. `gaja-med` ma Skillsy medyczne) nie powinny być w HEOS Jokera

W praktyce: HEOS pisze **wzorcowe** Skillsy dla nowych technologii. Profile mają swoje Skillsy które **odnoszą się do wzorców** przez `related-adrs` (jeśli dotyczy) albo po prostu spełniają ten sam standard.

### Decydent

Joker (decyzja wpływa na to jak rośnie HEOS).

### Blokuje

F2 metryki — jeśli wybierzemy A, mamy 89 Skillsów do audytu zamiast 2. Jeśli B (rekomendowane), zostajemy przy 2 HEOS + 87 profilowych.

---

## ODA-3: Engineering Principles — osobny katalog czy sekcja w 00-foundation?

| Pole | Wartość |
|---|---|
| **Status** | Open |
| **Priorytet** | P2 |
| **Blokuje** | F4 (zaplanowane EP-001 do EP-005) |

### Kontekst

HEOS v1.1 wspomina o "katalogu trwałych zasad EP-001, EP-002...". Ale **gdzie** one mają żyć? Trzy opcje:

### Opcje

**A) `00-foundation/engineering-principles/EP-NNN.md` (osobny katalog)**
- ✅ Jasna lokalizacja
- ✅ Skalowalne (po 50 EP nie zaśmiecają foundation)
- ❌ Dodatkowy katalog

**B) Sekcja w `HEOS-MASTER-PROMPT-v1.1.md`**
- ✅ Wszystko w jednym pliku
- ❌ Plik rośnie do 50KB+ przy 20 EP
- ❌ Ciężko diffować

**C) `02-artifacts/principles/` (traktowane jak artefakty)**
- ✅ Spójne z resztą (decyzje ADR mają podobny kształt)
- ❌ Principles ≠ decisions (Principles to nadrzędne zasady, ADR to decyzje)

### Rekomendacja Gaja

**A (osobny katalog)**. Powody:
1. EP to **nadrzędne** od ADR — nie pasują do `02-artifacts/` który jest dla artefaktów
2. Sekcja w foundation plik by rosła niekontrolowanie
3. Osobny katalog pozwala na per-EP PR review

Struktura:
```
00-foundation/
├── HEOS-MASTER-PROMPT-v1.1.md
├── engineering-principles/
│   ├── README.md                 # rejestr EP
│   ├── EP-001-priority-hierarchy.md
│   ├── EP-002-evidence-over-opinion.md
│   └── ...
```

### Decydent

Gaja (przy pisaniu pierwszego EP, zaplanowane w F2).

---

## ODA-4: registry.yaml — plik czy baza danych?

| Pole | Wartość |
|---|---|
| **Status** | Open |
| **Priorytet** | P1 |
| **Blokuje** | F3 (registry.yaml) |

### Kontekst

`04-knowledge-graph/` ma być indeksem cross-cutting. Pierwszy pomysł: `registry.yaml`. Ale czy YAML jest właściwym wyborem?

### Opcje

**A) `registry.yaml` (ręcznie edytowany)**
- ✅ Prosty
- ✅ Diffowalny w git
- ❌ Ręczna synchronizacja z frontmatter Skills/ADR

**B) `registry.yaml` (automatycznie generowany z frontmatter)**
- ✅ Single source of truth (frontmatter)
- ✅ Zawsze aktualny
- ❌ Narzędzie do generacji (TODO)

**C) SQLite (`registry.db`)**
- ✅ Szybkie zapytania
- ❌ Binarny, nie diffowalny w git
- ❌ Overengineering dla 50-100 Skills

**D) JSON + schema**
- ✅ Walidowalny
- ❌ Mniej czytelny niż YAML

### Rekomendacja Gaja

**B (auto-generowany z frontmatter)**. Powody:
1. Frontmatter to **single source of truth** (już istnieje, wszyscy go wypełniają)
2. Ręczny YAML się zdezaktualizuje po tygodniu
3. SQLite to overkill dla <200 Skills

Realizacja (F3):
```bash
python3 HEOS/03-quality/registry_gen.py > HEOS/04-knowledge-graph/registry.yaml
```

Ten skrypt czyta wszystkie SKILL.md i ADR, generuje YAML z:
- wszystkimi Skillami + ich domeną + related-adrs
- wszystkimi ADR + statusem
- inverse index: ADR → Skills które go cytują (do wykrywania orphanów)

### Decydent

Gaja (przy implementacji w F3).

---

## ODA-5: Kiedy tworzyć nową domenę (vs dodawać do istniejącej)?

| Pole | Wartość |
|---|---|
| **Status** | Open |
| **Priorytet** | P2 |
| **Blokuje** | Nic, ale wpływa na kiedy rosną `01-domains/` |

### Kontekst

Mamy 5 domen predefiniowanych: `embedded`, `robotics`, `ai-ml`, `infrastructure`, `web`. Kiedy dodawać nową?

### Propozycja kryteriów

Domena X jest potrzebna jeśli **≥2 z 3**:
1. **≥3 Skillsy** które nie pasują do istniejących domen
2. **Inny audience** (np. backend developer vs hardware engineer)
3. **Inny lifecycle** (np. dane medyczne mają compliance wymagania, inne domeny nie)

### Przykłady

| Kandydat | Spełnia kryteria? | Rekomendacja |
|---|---|---|
| `audio-processing` | ❌ 0 Skills, audience ogólny | Nie (dodajemy Skillsy do `ai-ml/`) |
| `blockchain` | ❌ 0 Skills | Nie (na razie) |
| `clinical-data` (dla gaja-med) | ✅ audience inny, lifecycle inny | Tak (dla profilu gaja-med) |
| `mobile-dev` | ❌ 1 Skill (React Native), audience bliski do `web/` | Nie (dodajemy do `web/`) |
| `3d-printing` | 🟡 1 Skill, ale hardware | Może (dyskusja) |

### Rekomendacja Gaja

Kryteria **≥2 z 3** + **concrete need** (realny use-case w ciągu miesiąca). Bez tego — nowa domena to YAGNI.

### Decydent

Gaja (automatycznie) + Joker (review gdy pojawi się kandydat).

---

## ODA-6: Jak wersjonować HEOS (SemVer vs własny)?

| Pole | Wartość |
|---|---|
| **Status** | Open |
| **Priorytet** | P3 |
| **Blokuje** | Nic |

### Kontekst

HEOS v1.0 → v1.1. Czy to **patch** (1.0.1) **minor** (1.1.0) **major** (2.0.0)?

### Opcje

**A) Strict SemVer (1.0.0, 1.1.0, 2.0.0)**
- ✅ Standard
- ❌ 1.0 → 1.1 to dziś minor, ale 9 zmian to dużo — czy to nie major?

**B) "Wersja prostota" (v1, v2, v3)**
- ✅ Prosty
- ❌ Nie mówi co się zmieniło

**C) Data-based (2026-Q3, 2026-Q4)**
- ✅ Zawsze aktualne
- ❌ Trudno porównywać wersje

### Rekomendacja Gaja

**A (SemVer) z pragmatyczną interpretacją**:
- **Major (X.0.0)**: zmiana architektury (np. z 2D na 3D)
- **Minor (1.X.0)**: nowe moduły, ADR, narzędzia (to co zrobiliśmy 1.0 → 1.1)
- **Patch (1.1.X)**: bugfixy, drobne poprawki, dodatkowe aliasy

Tym samym **1.0 → 1.1 to minor** (nowe moduły, ADR, enforcement). Jeśli kiedyś zmienimy architekturę na 3-wymiarową, to **2.0.0**.

### Decydent

Gaja (przy każdym release).

---

## ODA-7: Czy HEOS powinien mieć własny release process (CHANGELOG.md, GitHub Releases)?

| Pole | Wartość |
|---|---|
| **Status** | Open |
| **Priorytet** | P3 |
| **Blokuje** | Nic |

### Kontekst

HEOS jest w `Joker22pl/gaja-projekty` razem z innymi rzeczami. Nie ma własnego release process.

### Opcje

**A) HEOS w osobnym repo (`Joker22pl/heos`)**
- ✅ Własne Releases, Issues, Discussions
- ✅ SemVer
- ❌ Duplikacja git remote

**B) HEOS w `gaja-projekty`, z CHANGELOG.md w `HEOS/`**
- ✅ Wszystko w jednym miejscu
- ✅ Lokalny CHANGELOG
- ❌ Brak GitHub Releases

**C) HEOS w `gaja-projekty` + skrypt `release.py` który taguje**
- ✅ GitHub Releases automatycznie
- ❌ Tooling overhead

### Rekomendacja Gaja

**B (na teraz), A (gdy HEOS będzie dzielony z innymi)**. Na dziś HEOS jest osobisty Jokera — wystarczy CHANGELOG.md. Gdyby HEOS miał być współdzielony (open-source, forkowany), wtedy A.

### Decydent

Joker (gdy będzie chciał dzielić się HEOS).

---

## ODA-8: Jak radzić sobie z deprecated Skills które są aktywnie używane?

| Pole | Wartość |
|---|---|
| **Status** | Open |
| **Priorytet** | P1 (zaplanowane w F3) |
| **Blokuje** | Lifecycle Skills |

### Kontekst

Skill `old-orm-guide` jest `deprecated` (status w frontmatter), ale **stary kod w projektach** nadal go używa. Co robimy?

### Opcje

**A) Hard fail — jeśli Skill `deprecated`, `skill_view()` rzuca wyjątek**
- ✅ Wymusza migrację
- ❌ Łamie stary kod

**B) Soft warn — `skill_view()` zwraca Skill + warning "deprecated, use X instead"**
- ✅ Nie łamie
- ✅ Edukuje
- ❌ Wymaga manualnej migracji (dryf)

**C) Auto-redirect — `skill_view()` zwraca successor jeśli Skill jest `superseded_by: skills/X`**
- ✅ Transparent
- ❌ Ukrywa problem (stary kod nie wie że powinien się zmienić)

**D) Dual — emituj oba Skills (deprecated + successor) z ostrzeżeniem**
- ✅ Maksymalnie edukuje
- ❌ Szum w kontekście

### Rekomendacja Gaja

**B (soft warn) domyślnie + A (hard fail) opcjonalnie per projekt**. Powody:
1. HEOS ma być **pomocny**, nie restrykcyjny
2. Stary kod nie powinien się nagle łamać
3. Ale **w nowych projektach** (po F3) można włączyć strict mode

Realizacja: `skill_audit.py --strict` zwraca exit 1 na deprecated (dla CI nowych projektów).

### Decydent

Gaja (przy implementacji w F3).

---

## ODA-9: Multi-language (angielski vs polski) — czy HEOS ma dwa warianty?

| Pole | Wartość |
|---|---|
| **Status** | Open |
| **Priorytet** | P3 |
| **Blokuje** | Nic |

### Kontekst

HEOS v1.1 jest po polsku (Konstytucja). Ale Skillsy profilu Hermesa są po angielsku ("When to use", "Workflow"). Czy HEOS ma wersję angielską?

### Opcje

**A) Polski tylko** (obecny stan)
- ✅ Spójne z konwencją commitów (ADR-003)
- ❌ Nie dla anglojęzycznych

**B) Angielski tylko**
- ✅ Standard międzynarodowy
- ❌ Polski user (Joker) traci wygodę

**C) Oba — pl/ + en/ warianty w parallel**
- ✅ Maksymalna dostępność
- ❌ Duplikacja, ryzyko dryfu

**D) Polski + angielski inline (np. "Cel / Purpose", "Workflow", ...)
- ✅ Kompaktowe
- ❌ Mniej czytelne

### Rekomendacja Gaja

**A (polski) dla HEOS + aliasy w `skill_audit.py` dla angielskich nazw sekcji** (już zrobione). Powody:
1. HEOS jest osobisty Jokera — nie potrzebuje angielskiej wersji
2. Gdyby kiedyś otworzyć na zewn ątrz, **wtedy** C (osobne pliki en/)
3. Aliasy w audycie (już działają: "When to use" = "Kiedy używać") to tani kompromis

### Decydent

Joker (gdyby chciał otworzyć HEOS).

---

## ODA-10: Jak mierzyć "wiedzę HEOS" (jest naprawdę użyteczny)?

| Pole | Wartość |
|---|---|
| **Status** | Open |
| **Priorytet** | P2 |
| **Blokuje** | F4 (roczny audyt) |

### Kontekst

Mamy metryki ilościowe (ile Skills, ile ADR, ile % PASS). Ale nie mierzymy **jakości użytkowania** — czy HEOS naprawdę pomaga, czy to tylko metryki dla metryk.

### Propozycje metryk (kandydatki)

| Metryka | Jak mierzyć | Interpretacja |
|---|---|---|
| Skill re-use rate | Ile razy Skill X był faktycznie załadowany vs istnieje | Nieużywane Skillsy = knowledge rot |
| ADR compliance | Czy decyzje są faktycznie zgodne z napisanymi ADR | HEOS jako manifest vs realne zachowanie |
| Time saved | Estymowany czas zaoszczędzony dzięki HEOS (vs bez) | ROI HEOS |
| Lessons Learned → Skill promotion | Ile Lessons stało się Skillami | Czy Lessons są użyte |
| Cross-domain reuse | Czy Skill z domeny A jest cytowany w domenie B | Czy wiedza się rozprzestrzenia |

### Rekomendacja Gaja

Zacząć od **Skill re-use rate** (najprostsza do zmierzenia) + **ADR compliance** (manualna ankieta raz na kwartał). Reszta w F4.

### Decydent

Gaja (instrumentacja w F3/F4).

---

## Podsumowanie otwartych decyzji

| ID | Temat | Priorytet | Decydent | Faza |
|---|---|---|---|---|
| ODA-1 | Multi-profile HEOS | P3 | Joker | F4 |
| ODA-2 | Migracja 87 Skills do HEOS | P2 | Joker | F2 |
| ODA-3 | Engineering Principles — lokalizacja | P2 | Gaja | F2 |
| ODA-4 | registry.yaml — auto czy ręcznie | P1 | Gaja | F3 |
| ODA-5 | Kiedy nowa domena | P2 | Gaja+Joker | ongoing |
| ODA-6 | Wersjonowanie HEOS | P3 | Gaja | ongoing |
| ODA-7 | Release process | P3 | Joker | F4 |
| ODA-8 | Deprecated Skills behavior | P1 | Gaja | F3 |
| ODA-9 | Multi-language | P3 | Joker | ad hoc |
| ODA-10 | Metryki jakości HEOS | P2 | Gaja | F4 |

**10 otwartych decyzji.** P1: 2 (block F3). P2: 5. P3: 3.

**Wniosek:** HEOS v1.1 jest **używalny** — żadna decyzja P0 nie jest otwarta. Ale żeby być **doskonałym** (F4), trzeba rozwiązać 5-6 z tych.

---

*Patrz też: `00-HEOS-ROADMAP.md` (kiedy to rozwiązujemy), `00-HEOS-ARCHITECTURE.md` (wpływ na architekturę).*

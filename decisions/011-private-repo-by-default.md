---
# === Wspólne metadane (wymagane) ===
type: adr
id: adr-011
name: 011-private-repo-by-default
title: Repozytoria Joker22pl/* domyślnie prywatne
status: accepted
owner: gaja
created_at: '2026-07-28'
updated_at: '2026-07-28'
review_due: '2027-01-26'
version: 1.0.0
heos_standard_version: "1.2"
tags:
- governance
- heos-internal
- github
- security
related:
- adr-002
- adr-009

# === Specyficzne dla ADR ===
adr_number: 11
superseded_by: (none)

# === Jakość ===
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---

# ADR-011: Repozytoria Joker22pl/* domyślnie prywatne

## Status

Accepted (2026-07-28). Deklaracja polityki bezpieczeństwa dla nowych repozytoriów Joker22pl/*. Backlog: 7 istniejących repo (`HEOS`, `arp-arch`, `arp-firmware`, `arp-ros2`, `imp2-arch`, `imp2-firmware`, `imp2-ros2`) zostało utworzonych jako public w przeszłości — **do zmiany ręcznej przez Jokera** (jednorazowa akcja).

## Kontekst

Po v1.5.5 HEOS jest w pełni operacyjny, publiczny na GitHubie. Przegląd 28.07 wykazał, że **7 istniejących repo Joker22pl/* jest publicznych**:

| Repo | Publiczne od | Zawartość |
|---|---|---|
| HEOS | 2026-07-27 | Standardy + ADR + Skills (referencyjna dokumentacja, OK jako public) |
| arp-arch | 2026-07-26 | ADR dla platformy ag-robotycznej |
| arp-firmware | 2026-07-26 | Skeleton firmware |
| arp-ros2 | 2026-07-26 | Skeleton ROS 2 |
| imp2-arch | 2026-07-26 | ADR-y dla robota mobilnego |
| imp2-firmware | 2026-07-24 | Mikrokontroler ESP32 firmware |
| imp2-ros2 | 2026-07-24 | ROS 2 stack dla IMP2 |

**Ryzyko:** te repo (zwłaszcza `imp2-*`) zawierają projekty badawcze (IMP2 = robot mobilny Joker22pl), mogą ujawnić:
- szczegóły platformy sprzętowej (typ czujników, konfiguracja)
- szczegóły firmware (specyficzne dla hardware Joker22pl)
- decyzje architektoniczne (ADR-y z planami rozwoju)
- nazwy endpointów / hostów (np. `imp2-arch/decisions/0016` wspomina adresy IP)

**Decyzja:** wszystkie **nowe** repo Joker22pl/* mają być domyślnie prywatne. Istniejące 7 — do ręcznej zmiany przez Jokera.

## Decyzja

### Polityka

**Wszystkie nowe repozytoria Joker22pl/* są domyślnie prywatne.** Wyjątek: repo referencyjne / open-source mogą być public, ale wymaga to świadomej decyzji ("tak, chcę public dla X").

### Workflow dla nowych repo

```bash
# 1. Joker tworzy repo na github.com (UI) — domyślnie prywatne
# 2. Joker mówi gaja "zrób bootstrap dla X"
# 3. Gaja:
#    a. git init lokalnie
#    b. git remote add origin git@github.com:Joker22pl/X.git
#    c. git push -u origin main  # default visibility z GitHub = private
# 4. Jeśli repo ma być PUBLIC — Joker daje explicite zgodę w brief.
```

### Workflow dla istniejących repo (7 do zmiany)

```bash
# 1. Joker ustawia GitHub PAT z scope `repo` w env: GITHUB_TOKEN=ghp_...
# 2. python3 tools/repo_visibility.py --make-private --repo HEOS
#    (lub --all dla wszystkich 7 naraz)
# 3. Skrypt używa GitHub API PUT /repos/{owner}/{repo} z polem `private: true`
```

**Skrypt NIE JEST auto-uruchamiany** — to jednorazowa akcja Jokera. Po zmianie wszystkich 7 na private, **archiwizujemy** `repo_visibility.py` lub zostawiamy jako utility dla przyszłych audytów.

### Dlaczego nie automatyzujemy (jeszcze)

1. **Brak CI credentials** — żaden workflow nie ma `GITHUB_TOKEN` z write scope.
2. **Audit trail** — każda zmiana widoczności powinna być ręczna + udokumentowana w commit (nie w tle).
3. **Ryzyko** — błąd w skrypcie mógłby przypadkowo zmienić widoczność (np. z private na public zamiast odwrotnie). **Nie akceptuję tego ryzyka** bez code review.

## Uzasadnienie

| Kryterium | Opcja A (private default) | Opcja B (public default + explicit) |
|---|---|---|
| **Bezpieczeństwo** | ✅ Niższe ryzyko wycieku IP | ❌ Publiczne od startu |
| **Open-source visibility** | ⚪ Trzeba explicite wybrać public | ✅ Default |
| **Workflow** | ✅ Krótszy (default OK) | ⚪ Trzeba pamiętać o --public |
| **Cognitive load** | ✅ Zero (default) | ⚪ Musisz wiedzieć że istnieje flaga |
| **Failure mode** | ⚪ Ryzyko: HEOS był public dla specjalistów — zmiana na private ogranicza widoczność | ✅ Przypadkowo public mniej szkodzi niż przypadkowo private |
| **Recovery** | ⚪ GitHub pozwala zmienić z powrotem (ale reputacja może ucierpieć) | ✅ Łatwo zmienić |

**Wybrana: Opcja A** (private default). HEOS sam zostanie public (bo dokumentacja ma wartość dla społeczności Hermes Agent) — ale decyzja o HEOS była **świadoma**, nie default. Pozostałe 7 — do ręcznej oceny.

## Konsekwencje

**Pozytywne:**

- Zmniejszone ryzyko przypadkowego wycieku IP.
- Workflow jest krótszy (default OK).
- Audyt widoczności jest skryptowalny (`repo_visibility.py --audit`).
- HEOS zostaje public (bo to dokumentacja) — wprost udokumentowane jako świadomy wyjątek.

**Negatywne / ryzyka:**

- **Istniejące 7 repo** (HEOS, arp-*, imp2-*) — trzeba ręcznie zmienić. To jest jednorazowa akcja Jokera.
- **HEOS jako public repo** — wymaga uwagi: jeśli kiedyś HEOS dostanie sekrety (np. deployment keys), trzeba je wydzielić do env vars.
- **`repo_visibility.py` wymaga PAT** z scope `repo` — nie wbudowane w CI. Dokumentuje to w skill README.

## NIE obejmuje (anty-scope-creep)

- ~~Skrypt `repo_visibility.py` w CI workflow~~ — decyzja Jokera explicite kiedy go uruchomić.
- ~~Automatyczna zmiana widoczności 7 istniejących repo~~ — wymaga Jokera + PAT.
- ~~Polityka dla forków / PR~~ — GitHub domyślnie nie zmienia widoczności forków (to osobna kwestia).
- ~~Polityka dla organizacji Joker22pl~~ — jeśli istnieje (GitHub API nie pokazuje, sprawdzić).
- ~~Multi-profile Hermes (`gaja-it`, `gaja-med`)~~ — poza scope HEOS, to ADR-005 temat.

## Alternatywy rozważone

- **Opcja B (public default + explicit)** — odrzucona bo failure mode (przypadkowy public) bardziej szkodzi niż przypadkowy private. ADR uzasadnia dlaczego.
- **Opcja C (osobna organizacja Joker22pl-open dla publicznych)** — odrzucona, scope creep. Może przyszłość, ale nie v1.6.
- **Opcja D (private wszystkie, HEOS też)** — odrzucona, HEOS ma wartość dla społeczności.

## Kiedy rewizja

- **2027-01-26** (review_due). Sprawdzić czy:
  - 7 istniejących repo zostało zmienionych na private.
  - Czy workflow jest naturalny dla Jokera (nie wymaga obejścia).
  - Czy są nowe public repo które nie powinny być (audyt).

## Lessons Learned

**Wzorzec "private default + explicit override"** jest standardem bezpieczeństwa w narzędziach enterprise (np. GitLab default branch protection, GitHub default settings dla orgs). HEOS przejmuje ten wzorzec dla widoczności repo.

**Konsekwencja:** dokumentujemy **explicite** w brief że coś ma być public (np. HEOS). Default jest zawsze bezpieczniejszą opcją.

## Powiązane

- **ADR-002** — Hub repo + osobne repo per projekt (kontekst).
- **ADR-009** — HEOS v1.4 scope (precedens: scope deklaracja z anty-scope-creep).
- **ADR-010** — HEOS v1.5 scope (precedens: scope deklaracja z "NIE zawiera").
- **`tools/repo_visibility.py`** (nowy) — utility do audytu + zmiany widoczności.
- **`tools/CHANGELOG.md`** — wpis v1.6.0 po wdrożeniu.
- **Konwencja GitHub** — https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories

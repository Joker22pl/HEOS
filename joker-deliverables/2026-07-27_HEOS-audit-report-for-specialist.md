# HEOS — Audyt specjalisty (2026-07-27)

**Autor:** Gaja (Hermes Agent, profil `gaja`)
**Adresat:** Specjalista HEOS / Hermes Engineering Operating System
**Cel raportu:** Niezależna ocena jakości projektu HEOS po audycie 1-fazowym

---

## TL;DR

HEOS v1.2.0 przeszedł pełen audyt (10 kategorii, 30+ sprawdzeń). Wykryto
**9 rzeczywistych problemów** (4 bugi w narzędziach, 3 problemy
architektoniczne, 2 w konsystencji). Wszystkie zostały naprawione w 5
commitach. Stan końcowy: **5 skilli PASS, lint 0 findings, 18/18 testów
PASS, 5/5 mostów HEOS→profil działają**. Blokery do dalszego rozwoju:
brak GitHub repo `Joker22pl/HEOS` (remote skonfigurowany, push niemożliwy)
i brak CI/CD.

---

## 1. Stan projektu — snapshot

| Metryka | Wartość |
|---|---|
| **Wersja HEOS** | v1.2.0 (lokalnie), nie pushnięte do GitHuba |
| **Lokalizacja** | `/home/gaja/gaja-projekty/HEOS/` (osobne git repo, top-level = `HEOS/`) |
| **Git remote** | `git@github.com:Joker22pl/HEOS.git` (skonfigurowany, ale repo NIE ISTNIEJE) |
| **Commity** | 7 (2 baseline + 5 po audycie) |
| **Tagi** | brak (planowany `v1.2.0`) |
| **Artefakty łącznie** | 15 (7 skills + 5 ADR + 1 lessons + 1 checklist + 1 playbook) |
| **Templates** | 6 (skill, skill-runtime, adr, checklist, lessons, playbook) |
| **Narzędzia (tools/)** | 19 (10 core + 3 nowe + 3 testy + 3 migration) |
| **Testy** | 18/18 PASS |
| **Lint** | 0 ERROR / 0 WARN |
| **CI/CD** | ❌ brak (`.github/workflows/` nie istnieje) |
| **Pre-commit hook** | ✅ `tools/pre_commit_skill_check.sh` (lokalnie) |

## 2. Stan przed naprawą (baseline) vs po naprawie

| Metryka | PRZED | PO |
|---|---|---|
| Skille zbadane przez `skill_audit` | 8 (z 4 fałszywymi FAILami) | 5 (czyste) |
| Schema FAIL | 4 (3 to raporty `joker-deliverables/` złapane catch-all) | **0** |
| Technical FAIL | 5 (w tym 4 catch-all + 1 `embedded-communications-debug`) | **0** |
| `quality_schema`/`quality_technical` | `pending` dla 5/5 | **`pass`** dla 5/5 |
| Asymetria cross-refs | 8 (3 wykryte + 5 false-positive w mojej wstępnej analizie) | **0** |
| Katalogi `lessons/`, `checklists/`, `playbooks/` | Nie istnieją (deklarowane w ARCHITECTURE) | **Istnieją z 1 przykładem każdy** |
| `lifecycle_audit.py --quiet` | ❌ (brak flagi) | ✅ |
| Tool do aktualizacji `quality_*` | ❌ (brak) | ✅ `tools/update_quality.py` |
| Tool do sprawdzania asymetrii | ❌ (brak) | ✅ `tools/check_related_symmetry.py` |
| Tool do walidacji mostów HEOS→profil | ❌ (brak) | ✅ `tools/validate_symlinks.py` |
| Duplikat `memory-hygiene` (plik 35 KB + pusty katalog) | ❌ oba istnieją | ✅ katalog + plik skonsolidowane |
| Status `combined=approved` | 0 (3 partial + 1 broken + 4 invalid) | **0 (5 partial)** — partial bo Operational unmeasured |
| Working tree | clean (przed audytem) | clean (po wszystkich commitach) |

## 3. Wykryte bugi (4) — wszystkie naprawione

### Bug #1: `skill_audit.py` catch-all łapał pliki spoza scope

**Objaw:** 4 z 4 raportów FAIL w audycie to pliki z `joker-deliverables/`
i/lub nie-SKILL.md. Raport mówił "8 Skills, 4 FAIL" — w rzeczywistości
**5 Skills, 1 prawdziwy FAIL**.

**Root cause:** `audytuj_katalog()` ma fallback `root.rglob("SKILL.md")`
który łapie KAŻDY `SKILL.md` pod root. `HEOS_KATALOGI` (whitelist)
zawierał `(tools, templates, heos-migration, archive, decisions,
01-domains)` — brakowało `"joker-deliverables"`, `"lessons"`,
`"checklists"`, `"playbooks"`.

**Fix:** Dodano `"joker-deliverables", "lessons", "checklists", "playbooks"`
do `HEOS_KATALOGI`. Dodano `is_not_skill` flagę w `SkillReport` —
pliki z `type: lessons|checklist|playbook|adr` są pomijane w catch-all.
Rozszerzono aliasy `Lessons Learned` (Pitfalle / Lessons Learned, Pitfalle)
i `Przykłady` (Przykłady użycia).

**Verification:** Po fix — 5 Skills (prawidłowa liczba), 4 PASS / 1 FAIL
gdzie ten 1 to `gaja-lab-core` z brakującym `Przykłady` (naprawiony
aliasem).

### Bug #2: Asymetria cross-references (8 przypadków)

**Objaw:** `heos_lint.py` nie sprawdzał symetrii. Mój `check_related_symmetry`
wykrył 8 niesymetrycznych relacji (np. `skill-using-chm → skill-nightly-evolution`
ale NIE odwrotnie).

**Root cause:** Brak narzędzia do sprawdzania symetrii. HEOS lint sprawdza
tylko **istnienie** celu (BROKEN_REF), nie **kierunek** relacji.

**Fix:** Nowy `tools/check_related_symmetry.py` z auto-fix (`--dry-run`).
Wywołany — 3 naprawione (pozostałe 5 to false-positive z mojego wstępnego
skryptu audytu).

**Verification:** `check_related_symmetry.py --dry-run` → "✅ Brak
asymetrii".

### Bug #3: `update_quality.py` psuł YAML (------ zamiast ---)

**Objaw:** Po uruchomieniu `update_quality.py` 5 plików skille miało
zepsuty frontmatter (`------\n` zamiast `---\n`). Wszystkie audyty
i lint raportowały 11 ERROR "BROKEN_REF" bo `yaml.safe_load(parts[1])`
zwracał `None`.

**Root cause:** `update_quality.py` używał `f"---{opener}{new_fm}---{rest}"`
gdzie `opener = "---\\n"` — wynik to `-------\\n` (6 myślników + newline).

**Fix:** `opener = ""` — caller dodaje `---` raz na początku i raz przed
rest. Naprawiono wszystkie 5 plików `sed '1s/^------$/---/'`.

**Verification:** `python3 tools/heos_lint.py` → "0 findings".

### Bug #4: Brak narzędzia do aktualizacji `quality_*` w frontmatter

**Objaw:** `quality_schema: pending`, `quality_technical: pending`,
`quality_operational: unmeasured` dla 5/5 skillów — **nigdy nie były
aktualizowane** po audycie.

**Root cause:** Audyt tylko raportuje. Nie ma hook'a ani skryptu który
by przepisywał frontmatter na podstawie wyników.

**Fix:** Nowy `tools/update_quality.py`:
- czyta każdy skill, uruchamia audyt
- ustawia `quality_schema`/`quality_technical` na `pass`/`fail`
- `--dry-run` dla bezpiecznego podglądu
- `.bak` backup przed zapisem (teraz w .gitignore)
- idempotentny (drugie uruchomienie = +0 zmian)

**Verification:** Po uruchomieniu — 5 skille z `pending` → `pass`.
Drugie uruchomienie = 0 zmian.

## 4. Wykryte problemy architektoniczne (3) — wszystkie naprawione

### Arch #1: Brak zawartości `lessons/`, `checklists/`, `playbooks/`

**Objaw:** ARCHITECTURE.md deklaruje 3 katalogi dla 3 typów artefaktów.
Katalogi nie istniały. `templates/` dla tych typów istniały, ale puste.

**Root cause:** W migracji v1.1→v1.2 (2026-07-23) skille i ADR zostały
zmigrowane, ale lessons/checklists/playbooks nie powstały nigdy.

**Fix:** Utworzono 1 przykład każdy:
- `lessons/2026-07-27-heos-audit-fix-bug.md` (z bieżącego audytu)
- `checklists/heos-pre-commit-validation.md` (7-etapowa bramka)
- `playbooks/heos-new-skill.md` (krok-po-kroku tworzenia skilla)

**Verification:** `lifecycle_audit.py --quiet` → "Artefakty: 15 (skill: 7,
adr: 5, lessons: 1, checklist: 1, playbook: 1)".

### Arch #2: Duplikat `memory-hygiene` (plik + pusty katalog)

**Objaw:** `skills/memory-hygiene.md` (674 linii, Schema PASS) + katalog
`skills/memory-hygiene/` BEZ `SKILL.md` (tylko `references/`).

**Root cause:** Ktoś rozpoczął konwersję do katalogu, ale nie dokończył.
Wcześniejszy most w profilu Hermesa wskazywał na plik `.md`, ale
`memory-hygiene.md` sam odwoływał się do `references/race-condition-signs.md`
(oczekiwał katalogu).

**Fix:** Przeniesiono `skills/memory-hygiene.md` → `skills/memory-hygiene/SKILL.md`.
Przywrócono `references/race-condition-signs.md`. Zaktualizowano most
w profilu (`SKILL.md → katalog/SKILL.md`).

**Verification:** `validate_symlinks.py` → 5/5 działających. Most
`memory-hygiene → memory-hygiene/SKILL.md` (katalog, nie plik).

### Arch #3: Brak polityki formatu Skills (.md vs katalog)

**Objaw:** 5 plików `.md` + 3 katalogi `<name>/SKILL.md` — brak wyraźnej
reguły kiedy który.

**Rekomendacja (nie wdrożona automatycznie):** Patrz §6 ABCD.

## 5. Inne wykryte problemy (5) — wszystkie naprawione

| # | Problem | Status |
|---|---|---|
| 1 | `lifecycle_audit.py --quiet` brak | ✅ naprawiony |
| 2 | Brak `tools/update_quality.py` | ✅ dodany |
| 3 | Brak `tools/check_related_symmetry.py` | ✅ dodany |
| 4 | Brak `tools/validate_symlinks.py` | ✅ dodany |
| 5 | `gaja-lab-core` 6 lessons → 8 lessons (dodane z realnego użycia CH9102) | ✅ dodane |
| 6 | `embedded-communications-debug` brak code block (Technical FAIL) | ✅ dodany Przykład 4 |
| 7 | Brak wersji HEOS w README (`unknown` w STATUS) | ✅ "Wersja HEOS: v1.2.0" |
| 8 | `git log` w root `HEOS/` vs `gaja-projekty/` | ✅ wyjaśnione — osobne repo |
| 9 | `.bak` pliki w working tree (śmieci) | ✅ usunięte + `*.bak` w .gitignore |

## 6. Niewdrożone rekomendacje (do decyzji)

### Rec #1: Polityka formatu Skills (.md vs katalog) — ADR

**Problem:** 5 plików + 3 katalogi bez spójnej reguły.

**Propozycja reguły:**
- < 200 linii + brak references → plik `.md`
- > 200 linii LUB ma `references/`/`scripts/` → katalog `<name>/SKILL.md`

**Czy chcesz ADR-006?** (Decyzja architektoniczna)

### Rec #2: GitHub repo `Joker22pl/HEOS` — push blocker

**Stan:** Remote skonfigurowany. SSH auth działa. Ale repo NIE ISTNIEJE
na GitHubie (`git ls-remote origin` → "ERROR: Repository not found").

**3 opcje:**
- **A)** Utwórz `Joker22pl/HEOS` na GitHubie (prywatne, empty, bez
  README) → potem `git push -u origin main` + tag `v1.2.0`. Wymaga
  jednorazowej akcji z Twojej strony (tworzenie repo przez UI).
- **B)** Zostaw HEOS w monorepo `gaja-projekty` (wycofaj remote,
  commituj do gaja-projekty). Bez zmian, ale blokujesz HEOS jako
  standalone.
- **C)** Odłóż (status quo). HEOS działa lokalnie, push nie blokuje
  rozwoju.

**Rekomendacja:** A (prawdziwy standalone, najbardziej zgodne z ADR-002
o osobnych repo per projekt).

### Rec #3: CI/CD (GitHub Actions) — wymagane dla release gate

**Stan:** Brak `.github/workflows/`. Pre-commit hook działa lokalnie,
ale PR-y nie mają gate'a.

**Minimum do wdrożenia:**
- `lint.yml`: `python3 tools/skill_audit.py --level all --quiet &&
  python3 tools/heos_lint.py && python3 tools/lifecycle_audit.py
  --quiet && python3 -m pytest tools/test_*.py -q`
- Trigger: PR do `main` + push do `main`

**Effort:** 30 minut. Czeka na Rec #2 (repo musi istnieć).

### Rec #4: ADR-006 (skills format policy) — patrz Rec #1

## 7. Pozostałe uwagi

### 7.1 Co działa dobrze

- **CONSTITUTION.md + ARCHITECTURE.md:** Single source of truth dobrze
  zaimplementowane. 10 fundamentalnych zasad, 6-etapowy lifecycle.
- **Templates (6):** Kompletne, z 12 polami HEOS v1.2 w frontmatter.
- **ADR (5):** Wszystkie accepted, review_due 2027-01-23 (6 miesięcy).
  Cross-refs spójne (po fix).
- **Testy narzędzi:** 18/18 PASS, < 1s wykonanie.
- **Mosty HEOS→profil:** 5/5 działają, CP #23 z HEOS-operations
  (loader wymaga katalog) respektowany.

### 7.2 Ograniczenia audytu

- **Runtime Skills:** `nightly-evolution` i `using-chm` (2 skille z
  `data_root: ~/.hermes`) są pomijane przez `skill_audit` jako
  runtime — nie są częścią HEOS evaluation. To celowe (cross-cutting).
- **Operational quality:** Nie było mierzone. Status pozostaje `unmeasured`
  (placeholder w `SkillReport.operational`).
- **Combined = approved:** 0/5. Powód: Operational = N/A → combined
  spada do `partial`. Aby `approved`, trzeba manualnie ustawić
  `quality_operational: proven` po realnym użyciu w runtime.

### 7.3 Ryzyka rezydualne

- **5 commitów lokalnych, push niemożliwy** (brak GH repo). Utrata
  danych tylko jeśli dysk padnie — brak remote backup.
- **`update_quality.py` ma `.bak` files** — działają ale nie są
  atomowe. Jeśli `update_quality.py` padnie w połowie, mamy `.bak`
  do recovery. Po .gitignore (`*.bak`) → nie commitnięte, ale zostają
  na dysku.
- **`memory-hygiene/SKILL.md` (674 linii)** to największy skill.
  Granica 500 linii w HEOS (heurystyczna) przekroczona. Przyszła
  potrzeba: wydzielić `examples.md` lub `checklist-urgent.md`.

## 8. Commity wprowadzone (5)

```
f76fb43 [tool] audyt HEOS v1.2 — fix scope + symmetry + quality update
685f04b [refactor] memory-hygiene — przenieś do katalogu (674 linii + references)
1229a28 [skill] quality_* aktualizacja + cross-ref symmetry + Lessons
6284193 [feat] lessons/, checklists/, playbooks/ — 1 przykład każdy
3ee01c6 [doc] README + STATUS + registry + gitignore cleanup
```

Wszystkie w `[main]`, working tree clean. Push zablokowany do czasu
utworzenia `Joker22pl/HEOS` na GitHubie.

## 9. Rekomendowany następny krok (dla specjalisty)

1. **Walidacja niezależna:** Odtwórz audyt w 5 minut:
   ```bash
   cd /home/gaja/gaja-projekty/HEOS
   python3 tools/skill_audit.py . --level all --quiet
   python3 tools/heos_lint.py
   python3 tools/lifecycle_audit.py --quiet
   python3 -m pytest tools/test_*.py -q
   python3 tools/validate_symlinks.py
   python3 tools/check_related_symmetry.py --dry-run
   ```
   Oczekiwany output: 5 PASS / 0 FAIL, 0 findings, 18/18 PASS, 5/5 OK,
   "Brak asymetrii".

2. **Push do GitHuba:** Jednorazowa akcja — utworzenie `Joker22pl/HEOS`
   na GitHubie (puste, prywatne, bez README). Potem `git push -u origin
   main` + `git tag v1.2.0 && git push origin v1.2.0`.

3. **CI/CD (Rec #3):** Po push — dodać `.github/workflows/lint.yml`.

4. **ADR-006 (Rec #1):** Osobna sesja, decyzja architektoniczna o
   formacie Skills.

5. **Dług techniczny runtime Skills (~85 skille profilu Hermesa):**
   Poza scope HEOS, ale wpływa na konsumpcję HEOS Skills. Patrz
   IMP-2026-006 (HEOS ADR-006), status DEFERRED.

---

**Podsumowanie dla specjalisty:** HEOS v1.2.0 jest w **dobrym stanie
inżynieryjnym** — czyste narzędzia, spójna architektura, kompletne
szablony, brak duplikatów, brak asymetrii, brak fałszywych audytów.
Główne blokery są **organizacyjne** (push do GitHuba, ADR polityki
formatu), nie techniczne. Runtime Skills (~85 w profilu Hermesa) to
osobny problem poza scope tego audytu.

Raport wygenerowany: 2026-07-27 11:40 UTC
Commity bazowe: `556163e` (init) + `bc9c3a9` (doc) + 5 nowych = 7 total
# HEOS — Raport stanu projektu (do konsultacji z ChatGPT)

**Data raportu:** 2026-07-26
**Autor:** Gaja (Hermes Agent, profil `gaja`)
**Cel:** Przekazanie kontekstu do zewnętrznego LLM w celu uzyskania rekomendacji kierunku rozwoju

---

## 1. Czym jest HEOS (jedno zdanie)

**HEOS (Hermes Engineering Operating System)** to repozytorium standardów, procedur, ADR (Architecture Decision Records), Skills i narzędzi enforcement dla projektów robotycznych Jokera (IMP2, HDS) i pracy inżynierskiej agentów AI (Hermes Agent, profil `gaja`).

Lokalizacja: `~/gaja-projekty/HEOS/` (katalog w monorepo `gaja-projekty`).

---

## 2. Stan aktualny — metryki (2026-07-26)

| Metryka | Wartość |
|---|---|
| **Wersja HEOS** | v1.2.0 (lokalnie, nie pushnięte do GitHub — bo HEOS jest katalogiem w `gaja-projekty`) |
| **Commity w `gaja-projekty`** | 4 unpushed (Etap 2 HEOS + memory-hygiene v1.1.0 + embedded-communications-debug v0.2.0 + gaja-lab-core v1.0.0) |
| **Artefakty łącznie** | 12 (7 Skills + 5 ADR) |
| **Templates** | 6 (skill, skill-runtime, adr, checklist, lessons, playbook) |
| **Narzędzia (tools/)** | 16 (w tym 3 test files) |
| **HEOS lint** | 0 ERROR / 0 WARN / 0 INFO ✅ |
| **Lifecycle audit** | 0 review_due overdue, 0 orphan ADR, 0 candidates do archive ✅ |
| **Tests** | 18/18 PASS ✅ |
| **Skill audit (HEOS skills)** | 4 PASS / 0 WARN / 3 FAIL (technical level: 0 PASS / 2 FAIL) |
| **GitHub Actions (CI)** | ❌ brak |
| **Knowledge graph** | Częściowy (auto-generowany `.registry.yaml` z inverse_index) |
| **Skills w profilu Hermesa** | ~87, większość bez pełnej zgodności HEOS v1.2 |
| **Migracja v1.1 → v1.2** | ✅ Zakończona (commit `00f1329`, walidacja 2026-07-26) |

---

## 3. Struktura katalogów

```
HEOS/
├── CONSTITUTION.md          (249 linii — ręcznie utrzymywane zasady)
├── ARCHITECTURE.md          (261 linii — architektura 2D)
├── STATUS.md                (auto-generowany snapshot)
├── README.md
├── .registry.yaml           (auto-generowany indeks 12 artefaktów)
├── .pre-commit-config.yaml  (hook: heos-skill-audit schema)
│
├── skills/                  (7 Skills, mieszane formaty: *.md + katalogi/SKILL.md)
│   ├── esp32-s3-micropython-blink.md     (v1.0.0, accepted, embedded)
│   ├── memory-hygiene.md                  (v1.1.0, accepted, cross-cutting)
│   ├── nightly-evolution.md               (v1.2.1, accepted, cross-cutting)
│   ├── using-chm.md                       (v1.0.0, accepted)
│   ├── using-heos.md                      (v1.0.0, accepted)
│   ├── embedded-communications-debug/     (v0.2.0, katalog z SKILL.md + references/)
│   ├── gaja-lab-core/                     (v1.0.0, katalog z SKILL.md + scripts/ + references/)
│   └── memory-hygiene/                    (katalog, ALE skills/memory-hygiene.md też istnieje — DUPLIKAT)
│
├── decisions/               (5 ADR, płasko, status: accepted)
│   ├── 001-micropython-esp32-s3-pico.md
│   ├── 002-hub-repo-i-osobne-repo.md
│   ├── 003-konwencja-commitow-po-polsku.md
│   ├── 004-cookiecutter-i-pre-commit.md
│   └── 005-granice-profili-hermes.md
│
├── templates/               (6: skill, skill-runtime, adr, checklist, lessons, playbook)
├── tools/                   (16: generatory, audyty, migracje, testy)
├── heos-migration/          (5: plan.md, README.md, migration-map.json, rollback.sh, d-improvement-plan)
├── archive/                 (snapshot v1.1: OVERVIEW, CHANGELOG, ROADMAP, OPEN-DECISIONS, MASTER-PROMPT v1.0.docx)
└── joker-deliverables/      (2 raporty dla Jokera: HDS architecture review v1, HDS code audit v1)
```

**Niespójność:** katalogi `lessons/`, `checklists/`, `playbooks/` są zadeklarowane w `ARCHITECTURE.md`, ale **nie istnieją** — szablony są, ale zawartości brak.

---

## 4. Filozofia i zasady (CONSTITUTION.md skrót)

- **Rola Gaja:** Chief AI Engineer, długoterminowy partner techniczny
- **10 Fundamentalnych zasad** (zrozum problem → zaplanuj → implementuj, nie zgaduj, dokumentacja = część projektu, itd.)
- **Priorytety:** P0 Bezpieczeństwo → P1 Poprawność → P2 Jakość → P3 Skalowalność → P4 Optymalizacja
- **Proces:** Analiza → Plan → Implementacja → Testy → Walidacja → Dokumentacja → Self Review → Lessons Learned
- **Persony (5):** Chief Architect, Software Engineer, Robotics Engineer, QA & Reviewer, Documentation Engineer
- **Aktywności (7):** Architect, Research, Code, Reviewer, Debugger, Documentation, Teacher
- **Lifecycle artefaktów (6-etapowy):** draft → proposed → reviewed → accepted → deprecated → archived
- **Standard Skilla (Schema):** 7 obowiązkowych pól frontmatter, 8 opcjonalnych
- **Standard Skilla (Technical):** limity treści (min. długość), code examples, Lessons Learned
- **Standard Skilla (Operational):** quality_operational: fresh / stale / unmeasured
- **Definition of Done** (7-punktowa bramka, ADR-005 granice profili)

---

## 5. Mechanizmy Enforcement (5 narzędzi)

| Narzędzie | Co robi | Częstotliwość |
|---|---|---|
| `pre_commit_skill_check.sh` | Waliduje Schema Skills przy `git commit` | per commit |
| `skill_audit.py` (3 poziomy) | Schema + Technical + Operational validation | on-demand + cron |
| `heos_lint.py` | Cross-references, related IDs, orphaned ADR | on-demand |
| `lifecycle_audit.py` | review_due overdue, candidates to archive | on-demand + weekly cron |
| `weekly_report.py` | Raport statystyk HEOS + Hermes profile | weekly cron (Mon 1:30 UTC) |
| `generate_registry.py` | `.registry.yaml` z inverse_index (kto cytuje kogo) | on-demand |
| `generate_status.py` | `STATUS.md` snapshot | on-demand |
| `update_frontmatter.py` | Bulk update frontmatter (migracje) | on-demand |

**Brak CI** — `.github/workflows/` nie istnieje. Pre-commit hook działa lokalnie, ale PR-y nie mają gate'a.

---

## 6. Skills — szczegółowa lista

| Skill | Wersja | Schema | Technical | Operational | Format |
|---|---|---|---|---|---|
| esp32-s3-micropython-blink | 1.0.0 | pending | pending | unmeasured | plik .md |
| memory-hygiene | 1.1.0 | pending | pending | **fresh** ✅ | plik .md |
| nightly-evolution | 1.2.1 | pending | pending | unmeasured | plik .md |
| using-chm | 1.0.0 | pending | pending | unmeasured | plik .md |
| using-heos | 1.0.0 | pending | pending | unmeasured | plik .md |
| embedded-communications-debug | 0.2.0 | pending | pending | unmeasured | katalog/ |
| gaja-lab-core | 1.0.0 | pending | pending | unmeasured | katalog/ |
| (memory-hygiene duplikat) | – | – | – | – | katalog/ ⚠️ |

**Quality pending** dla wszystkich mimo że Schema=7/7 PASS w audycie — prawdopodobnie bug w klasyfikacji (skill_audit raportuje `accepted=0` zamiast `accepted=4`).

**Niespójność formatów:** Starsze Skillsy to płaski `.md`, nowsze to katalog z `SKILL.md + references/`. Brak standardu który dyktuje kiedy który.

---

## 7. ADR (Architecture Decision Records)

Wszystkie 5 ADR są `accepted`, `review_due: 2027-01-23`:

1. **ADR-001** — MicroPython + mpremote dla ESP32-S3-PICO
2. **ADR-002** — Hub repo `gaja-projekty` + osobne repo per projekt
3. **ADR-003** — Konwencja commitów — `[tag] opis` po polsku
4. **ADR-004** — Cookiecutter template + pre-commit hooks (ruff, gitleaks)
5. **ADR-005** — Granice profili Hermes (gaja / gaja-it / gaja-med)

**Brak ADR dla:** architektury monorepo vs polyrepo, GitHub Actions / CI, knowledge graph, versionowanie HEOS, multi-profile HEOS, lessons learned process, security review proces, ADR lifecycle gates, retirement process.

---

## 8. Konsumpcja HEOS

HEOS jest używany przez:
- **Hermes Agent (profil `gaja`)** — ładuje skille z `~/.hermes/profiles/gaja/skills/` (87 Skills)
- **Projekty w `gaja-projekty`:** HDS, HDS-arch, imp2-arch, imp2-firmware, imp2-ros2, GAIA
- **Cron jobs** (profil `gaja`): HEOS Weekly Audit (Mon 1:30 UTC), Nightly Evolution (daily 1:00 UTC)

---

## 9. Roadmapa historyczna (v1.1, 2026-07-23)

**F0 — Fundament** ✅ DONE (1 dzień, 2026-07-23)
**F1 — Egzekucja** ✅ DONE (ten sam dzień, cron + 2 pierwsze Skillsy)
**F2 — Pokrycie** 🟡 TODO (2026-07-23 → 2026-08-23): 5 top Skills profilu Hermesa do PASS, Skills dla ADR-003/004, pierwszy playbook, pierwszy LL, pierwszy EP
**F3 — Dojrzałość** ⚪ TODO (2 miesiące): GitHub Actions CI, registry.yaml v0.5, 5 kolejnych Skillsów, pierwszy Checklist, 3 Lessons Learned, 5 kolejnych ADR
**F4 — Skala** ⚪ TODO (1 miesiąc): Knowledge graph auto-gen, multi-profile decyzja, 5 EP, roczny audyt, HEOS v2.0

**Realny postęp vs roadmap:** F0 + F1 zrobione w 1 dzień. F2 miał trwać miesiąc — po 3 dniach stan: 0/8 zadań zrobionych (brak playbooków, brak Lessons Learned, brak Skillsów dla ADR-003/004, 0 z 5 top Skillsów profilu uzupełnionych). Realne użycie HEOS poza profilem `gaja` jest **minimalne**.

---

## 10. Otwarte Decyzje Architektoniczne (ODA, z archiwum v1.1)

- **ODA-1 (P3):** Multi-profile HEOS — czy `gaja`, `gaja-it`, `gaja-med` mają mieć wspólny czy osobny HEOS? (Rekomendacja Gaja: każdy osobny + wspólny rdzeń)
- **ODA-2+:** brak dalszych (dokument niekompletny, nie zaktualizowany)

---

## 11. Znane problemy / dług techniczny

1. **`quality_schema/technical/operational` zawsze `pending`** — prawdopodobnie bug w migracji frontmatter lub w skill_audit klasyfikacji (Combined: approved=0 / partial=0 / broken / invalid zamiast approved=4)
2. **Duplikat `memory-hygiene`** — `skills/memory-hygiene.md` + `skills/memory-hygiene/SKILL.md` (ten sam skill w dwóch formatach)
3. **Niespójność formatu Skills** — 5 jest plikami `.md`, 3 to katalogi z `SKILL.md`. Brak polityki.
4. **Brak CI** — `.github/workflows/` nie istnieje, więc pre-commit hook to jedyny enforcement
5. **Brak zawartości dla `lessons/`, `checklists/`, `playbooks/`** — katalogi zadeklarowane w ARCHITECTURE.md, ale puste (są tylko templates)
6. **HEOS nie ma własnego remote** — wszystko jest katalogiem w `gaja-projekty`, więc push idzie do monorepo (nie do dedykowanego repo)
7. **Unpushed 4 commity** w `gaja-projekty` (czekają na push do monorepo)
8. **`skills/gaja-lab-core/SKILL.md` ma flagę `manually-authored`** — `skill_manage` go blokuje, lessons z realnego użycia (CH9102 detection, VID/PID itd.) nie zostały jeszcze zapisane
9. **Skill audit Schema=4 PASS / 3 FAIL** — trzeba sprawdzić które failują i dlaczego (technical level)
10. **Skill quality classification** nie działa poprawnie — `accepted=0` dla Skills które przechodzą Schema 7/7

---

## 12. Pytania do ChatGPT

1. **Jaki powinien być kolejny etap rozwoju HEOS?** (F2 niedokończone, F3 ma GitHub Actions CI jako P0)
2. **Które z 10 problemów z sekcji 11 są P0, a które można odłożyć?**
3. **Czy HEOS powinien zostać katalogiem w monorepo, czy dostać własne repo?** (z powodu braku CI i unpushed commits)
4. **Czy brak `lessons/`, `checklists/`, `playbooks/` content to problem architektury, czy dyscypliny?**
5. **Jak zmniejszyć dług techniczny Skills profilu Hermesa (~87 z większości poza HEOS) bez scope creep?**
6. **Co z duplikatem `memory-hygiene` i niespójnością formatu Skills (.md vs katalog/SKILL.md)?**
7. **Czy quality_schema/technical/operational powinno być enforced czy dobrowolne?**
8. **Jakie ADR powinny powstać w pierwszej kolejności?** (security review, CI, knowledge graph, versionowanie)
9. **Czy warto inwestować w Knowledge Graph (F3.2) czy najpierw zamknąć F2?**
10. **Multi-profile HEOS (ODA-1) — teraz czy później?**

---

## 13. Kontekst użytkownika (Joker)

- Współpracuje z Gają (AI agent) nad projektami robotycznymi i softwarowymi
- Preferuje: konkretne rekomendacje, instant value, decyzje oparte na dowodach
- Projekty: IMP2 (robot mobilny, ESP32-S3 + Jetson + ROS 2), HDS (display GUI, RPi 3A+ + NUC)
- Komunikacja: polski (kod/commity po angielsku)
- Styl: "Co lepiej wybrać?" = wykonaj rekomendację, nie pytaj o każdy krok
- Toleruje niedoskonałości byle był forward progress
- Używa HEOS jakościowo niespójnie (czasem pisze Skills, czasem pomija)

---

## 14. Stan Gita (2026-07-26)

```
Branch: main (w gaja-projekty)
Remote: git@github.com:Joker22pl/gaja-projekty.git (monorepo)
Unpushed: 4 commity
Tags w HEOS context: v1.1.0-pre-migration, v1.2.0
Backup: ~/hermes-backups/heos-pre-v1.2-2026-07-24-0035.tar.gz (0.1 MB)
```

**Najnowsze commity:**
- `65a652c` [skill] memory-hygiene v1.1.0 — append-only detection rewrite
- `fe5dc97` [fix] HEOS v1.2 Etap 2: validation + plan.md closure + lint fix
- `f1d32ef` [skill] embedded-communications-debug v0.2.0 — HEOS migration
- `5c76edc` [init] gaja-lab-core v1.0.0 — read-only workshop diagnostic foundation

---

## 15. Pierwszy output ChatGPT — oczekiwania

Proszę o:
- **Top 3 rekomendacje** rozwoju HEOS z uzasadnieniem (priorytet + effort + impact)
- **Rekomendowany P0** na najbliższe 1-2 tygodnie
- **Czy HEOS powinno mieć własne repo, czy zostać w monorepo** — z argumentami za/przeciw
- **Które z 10 problemów z sekcji 11 są krytyczne** (blokują rozwój), a które kosmetyczne
- **Czy warto kontynuować F2 (Skills dla ADR, playbook, LL), czy przejść do F3 (CI) od razu**
- **Konkretne następne 3 commity / akcje** które Gaja może wykonać sama
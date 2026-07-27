# HEOS — Kompletna Struktura

**Data snapshotu:** 2026-07-23
**Wersja HEOS:** 1.1
**Lokalizacja:** `~/gaja-projekty/HEOS/` (git: `Joker22pl/gaja-projekty`, branch `main`)
**Rozmiar:** 28 plików, 21 katalogów, ~112 KB

---

## Drzewo katalogów (pełne, z rozmiarami i statusami)

```
HEOS/                                                                                [repo root]
├── README.md                                                  3.1 KB   [hub — punkt wejścia]
│
├── 00-foundation/                                                       [Konstytucja i zasady nadrzędne]
│   ├── HEOS-MASTER-PROMPT-v1.1.md                          12.7 KB   [Konstytucja (aktywna)]
│   └── archive-HEOS-MASTER-PROMPT-v1.0.docx                38.2 KB   [Archiwum v1.0 (zachowane)]
│
├── 01-domains/                                                            [Domeny wiedzy — rozłączne]
│   ├── ai-ml/
│   │   └── README.md                                       0.1 KB   [⚪ pusty — szkielet]
│   ├── embedded/
│   │   ├── README.md                                       0.1 KB   [🟡 szkielet]
│   │   └── skills/
│   │       └── esp32-s3-micropython-blink/
│   │           └── SKILL.md                                9.4 KB   [✅ PASS — 7/7 obow., 7/8 opcjon.]
│   ├── infrastructure/
│   │   └── README.md                                       0.1 KB   [⚪ pusty — szkielet]
│   ├── robotics/
│   │   └── README.md                                       0.1 KB   [🟡 szkielet]
│   └── web/
│       └── README.md                                       0.1 KB   [⚪ pusty — szkielet]
│
├── 02-artifacts/                                                          [Typy artefaktów — forma, nie treść]
│   ├── checklists/
│   │   └── README.md                                       0.1 KB   [⚪ pusty — Definition of Done TODO]
│   ├── decision-records/                                                [ADR — Nygard format]
│   │   ├── README.md                                       1.3 KB   [rejestr ADR — spis treści]
│   │   ├── template.md                                     1.0 KB   [szablon do kopiowania]
│   │   ├── ADR-001-micropython-esp32-s3-pico.md            2.5 KB   [✅ Accepted]
│   │   ├── ADR-002-hub-repo-i-osobne-repo-per-projekt.md   2.4 KB   [✅ Accepted]
│   │   ├── ADR-003-konwencja-commitow-po-polsku.md         2.6 KB   [✅ Accepted]
│   │   ├── ADR-004-cookiecutter-i-pre-commit.md            2.6 KB   [✅ Accepted]
│   │   └── ADR-005-granice-profili-hermes.md               2.9 KB   [✅ Accepted]
│   ├── lessons-learned/
│   │   └── README.md                                       0.1 KB   [⚪ pusty — pierwszy wpis TODO]
│   ├── playbooks/
│   │   └── README.md                                       0.1 KB   [⚪ pusty — po 3+ playbookach]
│   └── skills/
│       ├── README.md                                       0.1 KB   [indeks cross-cutting Skills]
│       └── using-heos/
│           └── SKILL.md                                    8.5 KB   [✅ PASS — 7/7 obow., 6/8 opcjon.]
│
├── 03-quality/                                                            [Narzędzia enforcement]
│   ├── skill_audit.py                                       8.0 KB   [walidator 15-punktowego szablonu]
│   ├── heos_lint.py                                        10.5 KB   [walidator spójności architektury]
│   ├── heos_weekly_audit.py                                 5.7 KB   [wrapper raportu tygodniowego + Discord]
│   ├── baseline-report-2026-07-23.txt                       0.2 KB   [baseline: 0/87 PASS, 87 FAIL]
│   ├── full-audit-2026-07-23.txt                           10.9 KB   [pełna lista 87 Skills z brakami]
│   ├── templates/                                                       [⚪ pusty — szablony Self Review TODO]
│   └── weekly-reports/                                                   [raporty z cron przebiegów]
│       ├── audit-2026-07-23.md                             0.4 KB   [pierwszy raport (skrypt)]
│       └── audit-2026-07-23-updated.txt                    0.2 KB   [po ręcznej naprawie 2 Skills]
│
└── 04-knowledge-graph/                                                   [⚪ pusty — registry.yaml TODO]
```

---

## Legenda statusów

| Symbol | Znaczenie |
|---|---|
| ✅ PASS | Skill spełnia wszystkie 7 obowiązkowych + ≥6 z 8 opcjonalnych sekcji |
| 🟡 | Szkielet z README, czeka na pierwszą zawartość |
| ⚪ | Pusty katalog (czeka na use-case) |
| ❌ FAIL | Skill ma braki (audyt `skill_audit.py`) |

---

## Statystyki na 2026-07-23

### Pliki wg typu

| Typ | Liczba | Łączny rozmiar |
|---|---|---|
| Markdown (dokumentacja) | 24 | ~57 KB |
| Python (narzędzia) | 3 | ~24 KB |
| DOCX (archiwum) | 1 | ~38 KB |
| TXT (raporty) | 3 | ~11 KB |

### Pliki wg kategorii

| Kategoria | Pliki | Udział |
|---|---|---|
| Konstytucja (00-foundation) | 2 | 7% |
| Domeny (01-domains) | 7 | 25% |
| Artefakty (02-artifacts) | 13 | 46% |
| Quality / enforcement (03-quality) | 8 | 29% |
| Knowledge graph (04-knowledge-graph) | 0 | 0% |

### Audyt Skills

| Lokalizacja | PASS | WARN | FAIL | Razem |
|---|---|---|---|---|
| HEOS (nowe) | 2 | 0 | 0 | 2 |
| Profil Hermesa (`~/.hermes/profiles/gaja/skills`) | 0 | 2 | 85 | 87 |

### ADR

| Status | Liczba |
|---|---|
| Accepted | 5 |
| Proposed | 0 |
| Superseded | 0 |
| Orphan (brak Skill cytującego) | 2 (ADR-003, ADR-004) |

---

## Ścieżki absolutne (Linux)

- **Repo root:** `~/gaja-projekty/`
- **HEOS root:** `~/gaja-projekty/HEOS/`
- **Git remote:** `github.com:Joker22pl/gaja-projekty.git` (branch: `main`)
- **Konstytucja:** `~/gaja-projekty/HEOS/00-foundation/HEOS-MASTER-PROMPT-v1.1.md`
- **Audyt HEOS:** `python3 ~/gaja-projekty/HEOS/03-quality/skill_audit.py ~/gaja-projekty/HEOS/`
- **Lint HEOS:** `python3 ~/gaja-projekty/HEOS/03-quality/heos_lint.py`
- **Tygodniowy raport:** `python3 ~/gaja-projekty/HEOS/03-quality/heos_weekly_audit.py --save`

---

## Co NIE jest w HEOS (granice)

- **87 Skills w profilu Hermesa** (`~/.hermes/profiles/gaja/skills/`) — to nie jest HEOS. To są Skillsy frameworka Hermes. HEOS ma audytować ich jakość, ale nie zarządza ich zawartością (to robi Hermes Agent lifecycle).
- **Inne profile** (`gaja-it`, `gaja-med`) — HEOS jest w profilu `gaja` (ADR-005). Profile `gaja-med` i `gaja-it` mają **własne** Skillsy i własne ADR.
- **Projekty Jokera** (np. przyszły "robot-1") — to mają być **osobne repo**, nie części HEOS. HEOS to system standardów, nie hosting projektów.
- **Konstytucja v1.0** (DOCX) — zachowana w archiwum (`00-foundation/archive-...`), ale NIE jest aktywna. Aktywna jest v1.1.

---

*Snapshot wygenerowany: 2026-07-23. Zaktualizuj tę sekcję przy każdej zmianie struktury HEOS.*

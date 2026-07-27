# Migracja HEOS v1.1 → v1.2

Katalog zawiera **infrastrukturę migracji** wykorzystywaną przy przejściu z v1.1 (architektura 2D z domenami) na v1.2 (architektura płaska, domeny = tagi).

## Pliki

| Plik | Co robi |
|---|---|
| `migration-map.json` | Mapa starych → nowych ścieżek (generowana przez `heos_migrate.py --dry-run`) |
| `rollback.sh` | Skrypt do przywracania stanu v1.1 z backupu |

## Procedura

### Etap 1 (✅ zakończony): Przygotowanie narzędzi

- ✅ `tools/generate_registry.py` — generuje `.registry.yaml`
- ✅ `tools/generate_status.py` — generuje `STATUS.md`
- ✅ `tools/lifecycle_audit.py` — audyt lifecycle (review_due, deprecated)
- ✅ `tools/heos_lint.py` — walidator spójności architektury
- ✅ `tools/heos_migrate.py` — narzędzie migracji
- ✅ `tools/test_*.py` — testy jednostkowe (13/13 passing)
- ✅ `~/hermes-backups/heos-pre-v1.2-*.tar.gz` — backup przed migracją
- ✅ git tag `v1.1.0-pre-migration` — punkt powrotu

### Etap 2 (TODO, po akceptacji Jokera): Migracja właściwa

```bash
# 1. Sprawdź plan
python3 HEOS/tools/heos_migrate.py --plan

# 2. Dry-run (generuje migration-map.json)
python3 HEOS/tools/heos_migrate.py --dry-run

# 3. Sprawdź mapę (33 operacje: 15 move + 8 archive + 10 delete)
cat HEOS/heos-migration/migration-map.json | python3 -m json.tool | less

# 4. Test rollback (suchy, nic nie robi)
bash HEOS/heos-migration/rollback.sh --dry-run

# 5. (po akceptacji) Właściwa migracja
python3 HEOS/tools/heos_migrate.py --execute

# 6. Weryfikacja
python3 HEOS/tools/heos_lint.py
python3 HEOS/tools/lifecycle_audit.py
python3 HEOS/tools/generate_status.py
```

### Rollback (gdyby coś poszło nie tak)

```bash
bash HEOS/heos-migration/rollback.sh
# Wymaga potwierdzenia "t" interaktywnie
```

Przywraca stan v1.1 z backupu + checkout do tagu `v1.1.0-pre-migration`.

## Kryteria Migration Verification Gate (przed Etapem 3)

Po `heos_migrate.py --execute`, przed Etapem 3 (Adopcja), weryfikujemy:

- [ ] Liczba artefaktów przed i po jest zgodna (33 v1.1 → 33 v1.2)
- [ ] Wszystkie schematy przechodzą walidację (`heos_lint.py` 0 ERROR)
- [ ] Wszystkie referencje są poprawne
- [ ] `.registry.yaml` jest kompletne (8 artefaktów: 3 skills + 5 ADR)
- [ ] `STATUS.md` generuje się bez błędów
- [ ] Testy narzędzi przechodzą (13/13)
- [ ] Rollback został zweryfikowany na sucho

## Powiązane

- `HEOS-v1.2-STAGE1-PLAN-v2.md` (w `~/.hermes/profiles/gaja/cache/`) — plan Etapu 1
- `HEOS-v1.2-PROPOSAL.md` (w `~/.hermes/profiles/gaja/cache/`) — propozycja v1.2
- 5 ADR w `HEOS/02-artifacts/decision-records/` — decyzje architektoniczne

## Historia

- **2026-07-23**: HEOS v1.1 (3 Skills + 5 ADR, 4-punktowa architektura z domenami)
- **2026-07-24**: Etap 1 v1.2 — narzędzia, backup, tag, testy
- **TODO**: Etap 2 — właściwa migracja plików
- **TODO**: Etap 3 — przepisanie CONSTITUTION.md, ARCHITECTURE.md, push

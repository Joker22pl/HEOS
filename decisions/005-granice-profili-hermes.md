---
type: adr
id: adr-005
name: 005-granice-profili-hermes
title: Granice profili Hermes (gaja / gaja-it / gaja-med)
adr_number: 5
status: accepted
owner: gaja
created_at: '2026-07-23'
updated_at: '2026-07-24'
review_due: '2027-01-23'
version: 1.0.0
heos_standard_version: '1.2'
tags:
- cross-cutting
related:
- skill-using-heos
- skill-nightly-evolution
- skill-using-chm
- adr-006
- lessons-2026-08-01-cross-profile-audit
- adr-012
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---# ADR-005: Granice profili Hermes (gaja / gaja-it / gaja-med)

| Pole | Wartość |
|---|---|
| **Status** | Accepted |
| **Data** | 2026-07-23 |
| **Autor** | Gaja |
| **Dotyczy domeny** | cross-cutting (Hermes Agent) |

## Kontekst

Na serwerze Jokera działają **trzy profile Hermes Agent** z różnymi userami i przeznaczeniem:

| Profil | User | Przeznaczenie |
|---|---|---|
| `gaja` | Joker | Osobista asystentka do projektów / robotów / code |
| `gaja-it` | (bot narzędziowy) | SysAdmin/DevOps — dba o serwer, logi, troubleshooting |
| `gaja-med` | Asia (lekarka, przyjaciółka Jokera) | Wspiera Asię klinicznie w pracy jako lekarka |

Pytanie: **czy profile mogą współdzielić sekrety (klucze API, dane)?**

## Decyzja

- **Każdy profil ma własne `.env`, własne `MEMORY.md`, własne `USER.md`, własne skills**
- **`gaja` NIE współdzieli kluczy API z `gaja-med`** (ani z `gaja-it`)
- **`gaja` NIE czyta pamięci `gaja-med`** (ani odwrotnie)
- **`gaja-it` to bot narzędziowy** — traktowany jako persona techniczna, nie osobisty user
- **Cross-profile reads/writes są domyślnie zablokowane** — wymagają explicit cross_profile=True i zgody Jokera

## Uzasadnienie

| Kryterium | Współdzielone sekrety | Osobne sekrety per profil |
|---|---|---|
| Bezpieczeństwo (compromised profile = compromised wszystko) | ❌ ryzykowne | ✅ izolacja |
| Rate limits API | dzielone | per-user |
| Granica kontekstu (dane medyczne vs projekty) | ❌ mieszane | ✅ czyste |
| Zgodność z RODO/HIPAA (dane medyczne) | ❌ ryzykowne | ✅ kontrolowalne |
| Convenience | ✅ mniej konfiguracji | niewielka niedogodność |

**Kluczowe:** Asia jest lekarką i obsługuje dane wrażliwe (kliniczne). Jej profil powinien mieć **własne konta** (Tavily, Firecrawl) i **własne klucze** — nawet jeśli to dziś oznacza dla niej dodatkową konfigurację. To jest granica, której nie przekraczamy dla wygody.

## Konsekwencje

**Pozytywne:**
- Compromised profil = ograniczona szkoda
- Jasna odpowiedzialność za sekrety
- Dane medyczne Asii zostają w jej profilu

**Negatywne / ryzyka:**
- Asia musi założyć własne konta API (jeśli chce web search)
- Trzy konta Tavily/Firecrawl = trzy razy setup (ale każdy user powinien mieć swoje)

## Rozważane alternatywy

- **Jeden profil, wiele kontekstów (workspace)** — odrzucone: Hermes nie ma takiego mechanizmu, plus mieszanie kontekstów to ryzyko wycieku
- **Jeden profil + encrypt-at-rest dla sekretów** — odrzucone: nadal jeden compromised profil = wszystko
- **Współdzielony profil z ACL** — odrzucone: nie istnieje w Hermes

## Kiedy rewizja

- Jeśli Hermes doda mechanizm "sub-kontekstów" z izolacją sekretów → można rozważyć konsolidację
- Jeśli Asia uzna, że nie potrzebuje web search → jej profil zostaje bez kluczy API, decyzja bez zmian

## Lessons Learned

- **Profile Hermesa to naturalne granice kontekstu** — nie próbuj ich scalać. Każdy profil ma swoją pamięć, skills, sesje.
- **NIE współdziel sekretów między profilami** — każdy profil powinien mieć własne klucze API. Tavyly/Firecrawl osobno dla gaja, gaja-it, gaja-med.
- **Cross-profile reads są możliwe** (read_file z explicit path), ale **domyślnie zablokowane** (cross_profile guard). To jest dobre zabezpieczenie.
- **Asymetria related** w v1.2: Skills cytują ADR-005 ale ADR-005 nie cytował Skills z powrotem. Naprawione w v1.2.1 (auto-fix).
## Powiązane

- `02-artifacts/skills/` (Skills w `gaja` NIE są widoczne dla `gaja-med`)
- Pamięć `gaja`: zapisane 2026-07-22

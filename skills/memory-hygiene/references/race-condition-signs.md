# Race condition w `MEMORY.md` — 7 sygnałów i reakcja

## Kiedy ten plik ma zastosowanie

`MEMORY.md` jest w `~/.hermes/profiles/<profile>/memories/`, **NIE** w repo git.
Nie ma merge strategy. Kilka mechanizmów może pisać równolegle:

- **nightly-evolution cron** (`~/.hermes/profiles/gaja/cron/output/`) — sprawdź
  job_id przez `cronjob action=list`.
- **memory-helper skilla** (jeśli aktywny w sesji).
- **Ręczna edycja Jokera** przez edytor.
- **Inny profil Hermesa** — ale cross-profile writes są blokowane domyślnie.
- **Inna sesja tego samego profilu** (np. otwarty równolegle chat).

## 7 sygnałów że zewnętrzny writer był aktywny

### Sygnał 1: `wc -c` po zapisie nie zgadza się z oczekiwanym

```bash
# Baseline: 7076 B
# Mój zapis powinien dodać ~300 B
# Po zapisie: 7963 B (+887 B zamiast +300 B)
# → ktoś dopisał +587 B ekstra
```

### Sygnał 2: `mtime` pliku zmienił się między `stat` a `wc -c`

```bash
stat MEMORY.md
# Modify: 2026-07-25 16:30:07.005353116
# Jeśli modyfikowałem plik o 16:03, ale mtime to 16:30 → ktoś pisał.
```

### Sygnał 3: `tail -3 MEMORY.md` pokazuje append bez separatora

```bash
# Ostatnie 3 linie mojego pliku to §9 "Znane pitfalle..."
# Ale coś dopisało na końcu bez §/##/--- separatora
```

### Sygnał 4: format wpisu nie pasuje do reszty struktury

```bash
# Moje wpisy mają format: "- **Temat** — opis 1 zdanie."
# Append ma: "HDS 2026-07-25: Stage 6-7 production..." → inny format.
# → to nightly-evolution albo memory-helper.
```

### Sygnał 5: w `~/.hermes/profiles/gaja/cron/output/` pojawiły się nowe pliki

```bash
ls -lt ~/.hermes/profiles/gaja/cron/output/ | head -3
# Jeśli ostatni job timestamp zgadza się z ostatnim zapisem MEMORY.md → to nightly.
```

### Sygnał 6: w `MEMORY.md` pojawia się "§N" którego nie napisałem

```bash
grep "^## " MEMORY.md | wc -l
# Jeśli jest §10, §11, a ja napisałem tylko §1-§9 → ktoś dodał.
```

### Sygnał 7: `~/.hermes/profiles/gaja/logs/agent.log` ma wpisy o "memory add"

```bash
tail -50 ~/.hermes/profiles/gaja/logs/agent.log | grep -i "memory"
# Jeśli są wpisy z innego job_id / user_id → równoległa sesja.
```

## Procedura reakcji (5 kroków)

### Krok 1: Oceń append (filtr 7-punktowy)

Czy append przechodzi filtr? (memory-hygiene §3):

1. Przydatny za miesiąc+? ✓ (HDS Stage 6-7 lesson → tak)
2. Wpływa na decyzje? ✓ (production Pygame pitfalls → tak)
3. Multi-projekt? może
4. Nie ma w USER/SOUL/skille/repo? raczej tak
5. Potwierdzone? tak (z nocnego audytu)
6. Brak = powtórka błędu? tak (GIL held by render thread)
7. Krótko i jednoznacznie? średnio (887 B to dużo)

Wynik: 5-6/7 = **zostaw, nie kasuj**.

### Krok 2: Zapisz do `pending-review.md`

```markdown
### N. Append od zewnętrznego writera MEMORY.md

**Kontekst:** Między 16:03 a 16:30 dopisano ~887 B (prawdopodobnie
nightly-evolution cron). Append jest wartościowy (przechodzi filtr 7-pkt).

**Wersja A (status quo):** zostawić jak jest, append na końcu.

**Wersja B (rekomendacja):** przy następnym audycie tygodniowym
zintegrować append z istniejącymi sekcjami (§6 aktywne projekty lub §9
pitfalle) i usunąć separator.

**Pytanie:** Jak chcesz żeby wyglądały przyszłe appendy — na końcu
(append-only) czy zintegrowane z sekcjami (refactor przy audycie)?
```

### Krok 3: Kontynuuj pracę

NIE revertuj appendu, NIE usuwaj, NIE przenoś. Append został zapisany
przez kogoś z konkretnego powodu (nocny audyt, inna sesja, ręczna
zmiana Jokera). Usunięcie = utrata pracy + brak audit trail.

### Krok 4: Dodaj do changelogu

```markdown
### 2026-07-25 (kontynuacja) — Wykryto race condition

- MEMORY.md: 7,076 B (mój baseline) → 7,963 B (po append od zewnętrznego
  writera, +887 B = +12.5%).
- Źródło prawdopodobne: nightly-evolution cron (timestamp zgadza się).
- Decyzja: zostawiam append (przechodzi filtr 7-pkt, wartościowy).
- Flaga: `pending-review.md` pyt.N — "append-only vs refactor przy audycie".
```

### Krok 5: Raport dla usera (opcjonalny, krótki)

```
⚠️ Wykryto zewnętrznego writera MEMORY.md:
- baseline: 7076 B → po append: 7963 B (+887 B)
- źródło: nightly-evolution cron (16:30:07)
- zawartość: HDS Stage 6-7 production Pygame lesson
- decyzja: zostawiam, dodaję do pending-review do Twojej oceny
```

## Dlaczego NIE robić `cp MEMORY.md /tmp/` jako "lock"

Nie ma operacyjnego filesystem lock dla `MEMORY.md` w Hermes (plik
`.lock` jest markerem a nie flock). Nawet `cp ... /tmp/MEMORY.md.bak`
nie chroni przed innym writerem — on pisze do oryginału, nie do /tmp.

Prawdziwe zabezpieczenie:
- **Sprawdzaj `wc -c` PRZED i PO** (5x taniej niż `cp` + diff).
- **NIGDY nie revertuj cudzego appendu** (utrata pracy).
- **Akceptuj shared reality** — `MEMORY.md` to nie exclusive resource.

## Kiedy NIE stosować tej procedury

- **MEMORY.md NIE zmienił rozmiaru** od ostatniego sprawdzenia → nie
  ma race condition, nie musisz nic robić.
- **Append jest duplikatem tego co już napisałem** — możesz scalić
  (usuwając mój lub jego wpis, nie oba), ale z flagą w pending-review.
- **Append psuje strukturę** (np. łamie `##` syntax) → commit fix
  z `--no-verify` i flagą w pending-review.

## Metryka do śledzenia

```bash
# W swoim audycie codziennym:
git diff <(wc -c MEMORY.md) <(sleep 1 && wc -c MEMORY.md)
# Różnica >0 między dwoma odczytami = ktoś pisze.
```

Jeśli różnica >0 **regularnie** (np. codziennie +500 B od nightly) →
planuj z góry miejsce na te appendy (zostawiaj 5-10% limitu bufora).

---
type: adr
id: adr-001
name: 001-micropython-esp32-s3-pico
title: MicroPython + mpremote dla ESP32-S3-PICO
adr_number: 1
status: accepted
owner: gaja
created_at: '2026-07-23'
updated_at: '2026-07-24'
review_due: '2027-01-23'
version: 1.0.0
heos_standard_version: '1.2'
tags:
- embedded
related:
- skill-esp32-s3-micropython-blink
- adr-003
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---# ADR-001: MicroPython + mpremote dla ESP32-S3-PICO

| Pole | Wartość |
|---|---|
| **Status** | Accepted |
| **Data** | 2026-07-23 |
| **Autor** | Gaja (z inicjatywy Jokera) |
| **Dotyczy domeny** | `01-domains/embedded` |

## Kontekst

Pierwszy test robota na ESP32-S3-PICO podłączonym do NUC-a. Próba użycia Arduino CLI zakończyła się niepowodzeniem:

- Arduino core autodetekcji wybrało wariant **Feather ESP32-S3** zamiast **ESP32-S3-PICO** — złe piny, inne mapowanie GPIO
- Każda iteracja wymagała pełnego cyklu `arduino-cli compile → upload → monitor` (10-15s na przebudowę)
- Brak REPL — każda zmiana to nowy upload firmware'u
- Walka z `fqbn` (Fully Qualified Board Name) i wariantami płytki

## Decyzja

Przechodzimy na **MicroPython + mpremote** dla płytek z rodziny ESP32-S3 (i podobnych modułów Espressif).

## Uzasadnienie

| Kryterium | Arduino CLI | MicroPython + mpremote |
|---|---|---|
| Szybkość iteracji | 10-15s/cykl (compile+upload) | <1s (REPL `exec()` lub `mpremote run`) |
| REPL | ❌ | ✅ (`mpremote repl`) |
| Auto-detekcja płytki | ❌ (trzeba wskazać `fqbn`) | ✅ (`mpremote connect /dev/ttyACM0`) |
| Krzywa uczenia | średnia (C++ idiomy, framework) | niska (Python) |
| Ekosystem bibliotek | bogaty | mniejszy, ale wystarczający dla 80% use-case'ów |
| Niskopoziomowy dostęp do peryferiów | pełny | ograniczony (workaroundi przez `machine.mem32`) |
| Debug hardware (PIR, ADC) | trudny | trywialny (REPL + `print()`) |

## Konsekwencje

**Pozytywne:**
- Iteracja 10× szybsza
- Łatwiejsze prototypowanie i debugowanie
- Można uczyć się peryferiów ESP32 bez C++

**Negatywne / ryzyka:**
- Brak niektórych niskopoziomowych peryferiów (częściowy workaround przez `machine.mem32`)
- Wydajność CPU niższa (interpreter vs natywny kod) — istotne dla DSP / kryptografii
- Nie nadaje się do produkcyjnych buildów (rozmiar firmware'u, determinizm)

## Rozważane alternatywy

- **ESP-IDF** (oficjalny Espressif) — pełna kontrola, ale wysoki próg wejścia (CMake, RTOS). Za ciężkie na fazę prototypu.
- **CircuitPython** (Adafruit fork MicroPythona) — fajny, ale mniej wsparcia dla gołych modułów Espressif.
- **Zephyr** — profesjonalny RTOS, ale overkill dla hobbysty.

## Kiedy rewizja

- Gdy potrzebujemy hard-real-time DSP (audio, motor control PWM z mikrosekundową precyzją)
- Gdy MicroPython przestaje wspierać ESP32-S3 (mało prawdopodobne, ale monitorujemy)

## Lessons Learned

- **Pinout per board** — każda płytka ESP32 (Feather/Pico/DevKitC) ma inny pin RGB LED. Zawsze sprawdzaj docs producenta PRZED pisaniem kodu, nie po.
- **Bootloader vs App port** — po wgraniu MicroPython dwa porty `/dev/ttyACM*` się zamieniają. Nie hardkoduj `/dev/ttyACM0` — sprawdzaj po każdym restarcie.
- **`sys.platform` nie rozróżnia wariantów** — MicroPython zwraca `"esp32"` dla wszystkich S3/C3/Pico. Nie pytaj Pythona o model, pytaj pinout.
- **Arduino core ma warianty boardów** — zły wariant = złe piny BEZ błędu kompilacji. MicroPython eliminuje tę pułapkę.
## Powiązane

- `skills/esp32-s3-micropython-blink.md` (HEOS Skill — wzorcowa implementacja)
- ADR-003 (konwencja commitów)

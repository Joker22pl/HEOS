---
name: esp32-s3-micropython-blink
description: Flash MicroPython on ESP32-S3 boards (Waveshare Pico, Adafruit Feather S3, DevKitC) and verify with an RGB NeoPixel
  blink test. Use when a new ESP32-S3 board is just connected, when Arduino-ESP32 core variant pinning is giving wrong LED
  pins, or when you need a quick "is this board alive?" check.
status: accepted
platforms:
- linux
- macos
type: skill
id: skill-esp32-s3-micropython-blink
title: ESP32-S3 MicroPython Blink — first-board test
owner: gaja
created_at: '2026-07-24'
updated_at: '2026-07-24'
review_due: '2027-01-23'
version: 1.0.0
heos_standard_version: '1.2'
tags:
- embedded
related:
- adr-001
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---

# ESP32-S3 MicroPython Blink — first-board test

## Cel

Szybki test "czy ta płytka żyje" dla nowej płytki ESP32-S3, z migotaniem RGB LED i weryfikacją przez serial. Zastępuje walkę z Arduino-ESP32 core / wariantami płytek.

## Zakres

- **Dotyczy:** płytki z rodziny ESP32-S3 (Waveshare Pico, Adafruit Feather S3, Espressif DevKitC, ESP32-S3-PICO)
- **Narzędzia:** MicroPython firmware, `mpremote`, `esptool`, host Linux/macOS
- **Czas:** 5-10 minut od zera (z pobraniem firmware)

## Kiedy używać

- ✅ Nowa płytka ESP32-S3 właśnie podłączona do USB — chcesz szybki "is it alive?"
- ✅ Arduino-ESP32 core wybrał zły wariant → piny nie działają
- ✅ Przejście z Arduino CLI na MicroPython (potrzebujesz czystego startu)
- ✅ Test loopback dla innych sensorów — chcesz potwierdzić że USB/serial działa przed dalszą pracą
- ✅ Bootloader diagnostics — flash MicroPython żeby obejść bootloader

## Kiedy nie używać

- ❌ Masz Arduino sketch który działa i chcesz tylko dodać feature → zostań przy Arduino
- ❌ Projekt wymaga hard-real-time DSP / audio z niskim latency → MicroPython jest za wolny
- ❌ Płytka to **nie** ESP32-S3 (np. ESP32, ESP32-C3, RP2040) — pinout i procedura inne
- ❌ Production firmware release → MicroPython to nie jest docelowy stack (rozmiar, determinizm)

## Workflow (krok-po-kroku)

### 1. Wykryj płytkę w USB

```bash
lsusb | grep -iE "espressif|adafruit|silicon labs"
# Espressif VID 303a (bootloader: 1001, app: różne)
# Adafruit VID 239a (Feather: 811b)
ls /dev/ttyACM* 2>/dev/null
```

Płytka po podłączeniu ma **dwa porty `/dev/ttyACM*`** — jeden dla bootloadera, jeden dla app. Numery się zamieniają przy restarcie.

### 2. Znajdź pin RGB LED (NIE ZGADUJ!)

| Płytka | Pin RGB LED | Pin czerwonej LED |
|---|---|---|
| **Waveshare ESP32-S3-Pico** | GPIO21 | (osobna, tylko PWR) |
| **Adafruit Feather ESP32-S3** | GPIO33 | GPIO13 (czerwona) |
| **Espressif DevKitC v1.1** | GPIO48 | — |
| **Espressif DevKitC-1 v1** | GPIO38 | — |

Źródło: oficjalny pinout producenta. **Nie zgaduj — sprawdź w docs.**

### 3. Pobierz firmware MicroPython

```bash
# Najnowsza wersja z https://micropython.org/download/ESP32_GENERIC_S3/
curl -fsSL -o /tmp/esp32s3-mp.bin \
  https://micropython.org/resources/firmware/ESP32_GENERIC_S3-20260406-v1.28.0.bin
ls -la /tmp/esp32s3-mp.bin  # sprawdź rozmiar > 1MB
```

### 4. Wymaż i wgraj firmware

```bash
# Użyj portu BOOTLOADERA (ten który znika po resecie, albo ma VID 303a:1001)
export ESPTOOL_PORT=/dev/ttyACM0  # lub ACM1 — sprawdź który to bootloader
esptool --chip esp32s3 erase_flash
esptool --chip esp32s3 --baud 460800 write_flash 0 /tmp/esp32s3-mp.bin
```

Po flashu płytka się zrestartuje i pojawi się REPL.

### 5. Napisz blink.py

```python
# main.py
from machine import Pin
from neopixel import NeoPixel
from time import sleep_ms

# === ZMIEŃ PIN DLA SWOJEJ PŁYTKI ===
RGB_PIN = 21   # Pico=21, Feather=33, DevKitC=48
# =====================================

np = NeoPixel(Pin(RGB_PIN, Pin.OUT), 1)

print("Blink startuje...")
while True:
    np[0] = (40, 0, 0);  np.write(); print("RED");   sleep_ms(500)
    np[0] = (0, 0, 0);   np.write(); print("OFF");   sleep_ms(500)
    np[0] = (0, 40, 0);  np.write(); print("GREEN"); sleep_ms(500)
    np[0] = (0, 0, 0);   np.write(); print("OFF");   sleep_ms(500)
    np[0] = (0, 0, 40);  np.write(); print("BLUE");  sleep_ms(500)
    np[0] = (0, 0, 0);   np.write(); print("OFF");   sleep_ms(500)
```

⚠️ **Bezpieczna jasność:** `(40, 0, 0)` a nie `(255, 0, 0)` — NeoPixel zasilany z USB ma ograniczoną wydajność.

### 6. Upload i weryfikacja

```bash
export PATH="$HOME/bin:$PATH"
mpremote connect /dev/ttyACM0 fs cp ./main.py :main.py
mpremote connect /dev/ttyACM0 reset

# Czytaj z portu APP (tego co NIE był bootloader-mode)
timeout 5 cat /dev/ttyACM1  # lub ACM0 — sprawdź który teraz jest app
```

Powinieneś zobaczyć:
```
Blink startuje...
RED
OFF
GREEN
...
```

I RGB LED na płytce powinna migać w kolorach (czerwona dioda obok USB-C to PWR — nie reaguje).

## Przykłady

### Przykład 1: Pierwszy test nowej płytki

Sytuacja: użytkownik podłącza nową ESP32-S3-Pico, chce potwierdzić że działa.

Wynik: po 5 minutach miganie widoczne, serial wypisuje RED/OFF/GREEN/..., `lsusb` pokazuje Espressif VID 303a, brak komunikatów o błędach w esptool.

### Przykład 2: Diagnoza złego pinu

Sytuacja: dioda RGB nie miga ale czerwona PWR LED świeci.

Wynik: sprawdzenie pinout → odkrycie że pin to 21 a nie 33 (lub odwrotnie). Poprawka w `main.py`, ponowny upload, sukces.

### Przykład 3: Przejście z Arduino

Sytuacja: użytkownik miał Arduino sketch, chce przejść na MicroPython.

Wynik: `esptool erase_flash` czyści stary firmware, wgranie MicroPython, blink test, dalsza praca w Pythonie.

## Lessons Learned (z naszej historii)

1. **Dwa porty USB zamieniają się** — po wgraniu MicroPython port bootloader znika, pojawia się port app. Nie hardkoduj `/dev/ttyACM0` — sprawdzaj po każdym restarcie.
2. **`sys.platform` zwraca `"esp32"`** — nie ma rozróżnienia S3 vs C3 vs Pico. Nie pytaj MicroPythona o model, sprawdź pinout z docs.
3. **Arduino core ma warianty płytek** — wybór złego wariantu (`esp32:esp32:esp32s3` zamiast `esp32:esp32:adafruit_feather_esp32s3`) daje złe piny BEZ błędu kompilacji. Diagnoza trwa godziny. MicroPython nie ma tego problemu.
4. **Świecąca czerwona LED to prawdopodobnie PWR** — nie RGB. RGB ma zachowanie które się zmienia. Sprawdź czy miga w kolorach, nie czy świeci stale.
5. **Bootloader zostaje po restarcie** — `esptool` wchodzi w tryb flash automatycznie przy GPIO0=LOW, ale jeśli chcesz flashować później, musisz wejść w tryb ręcznie (przycisk BOOT + RST na płytce).
6. **`esptool --chip esp32s3`** — zawsze podawaj chip, bo inaczej autodetect może się pomylić między ESP32, S2, S3, C3.

## Typowe błędy

- **Błędny pin RGB** → dioda się nie zapala. Sprawdź pinout producenta.
- **Brak `erase_flash` przed flashem** → stary firmware zostaje, nowy się nie wgrywa lub zachowuje się dziwnie.
- **Upload na zły port** (bootloader zamiast app) → timeout lub "device busy".
- **Za duża jasność `(255, 255, 255)`** → może zrestartować płytkę lub spowodować brownout z USB.
- **`from machine import I2C` zamiast `SoftI2C`** → na ESP32-S3 z niektórymi sensorami I2C hang. SoftI2C pewniejszy.

## Debugging

| Objaw | Diagnoza | Fix |
|---|---|---|
| Nic się nie dzieje po flashu | zły port lub firmware niekompletny | sprawdź VID w `lsusb`, wgraj jeszcze raz |
| Tylko PWR LED świeci | zły pin RGB | sprawdź pinout, zmień `RGB_PIN` |
| Serial wypisuje ale LED nie miga | pin GPIO nie obsługuje NeoPixel lub jest w innym formacie | sprawdź czy LED to NeoPixel (WS2812) a nie zwykła |
| `mpremote: device not found` | port ACM0/ACM1 się zamienił | `ls /dev/ttyACM*` po restarcie |
| Esptool timeout | płytka nie w bootloader mode | BOOT + RST, albo GPIO0=LOW przy starcie |

## Biblioteki

- `machine` (builtin MicroPython) — Pin, SoftI2C, I2C
- `neopixel` (builtin MicroPython) — sterowanie WS2812/NeoPixel
- `time.sleep_ms` (builtin) — opóźnienia

## Narzędzia (host)

- `esptool` — flash firmware
- `mpremote` — REPL, file system, upload skryptów
- `curl` — pobieranie firmware
- `lsusb` — detekcja VID/pid

## Oficjalne źródła

- MicroPython ESP32-S3 firmware: https://micropython.org/download/ESP32_GENERIC_S3/
- MicroPython library reference: https://docs.micropython.org/en/latest/library/index.html
- mpremote docs: https://docs.micropython.org/en/latest/reference/mpremote.html
- Waveshare ESP32-S3-Pico pinout: https://www.waveshare.com/wiki/ESP32-S3-Pico
- Adafruit Feather ESP32-S3: https://learn.adafruit.com/adafruit-feather-esp32-s3

## Wersjonowanie

- **v1.0** (2026-07-23) — pierwsza wersja, oparta na doświadczeniu z testów 2026-07-23

## Checklisty

### Pre-flight
- [ ] Płytka podłączona do USB
- [ ] `lsusb` potwierdza Espressif VID
- [ ] `ls /dev/ttyACM*` pokazuje ≥1 port
- [ ] Sprawdziłem pinout producenta (nie zgaduję pinu RGB)

### Post-test
- [ ] RGB LED miga w kolorach (nie świeci stale)
- [ ] Serial wypisuje RED/OFF/GREEN/OFF/BLUE/OFF w pętli
- [ ] `mpremote repl` wchodzi do REPL bez błędów
- [ ] Mogę uploadać kolejne pliki przez `mpremote fs cp`

## Najlepsze praktyki

1. **Zawsze sprawdź pinout** — 5 minut czytania oszczędza godziny debugowania
2. **`erase_flash` przed każdym flashem nowego firmware** — czysta baza
3. **SoftI2C zamiast machine.I2C** dla sensorów na ESP32-S3 — pewniejsze
4. **REPL test przed `main.py`** — wgraj przez `mpremote` zamiast uruchamiać main, zobacz co się dzieje
5. **Backup działającego firmware** — jeśli robisz coś ryzykownego, zapisz binarkę
6. **Osobna karta sieciowa dla testów WiFi** — żeby test nie wpływał na domową sieć

## Powiązane

- **ADR-001** — MicroPython + mpremote dla ESP32-S3-PICO
- Skills: `esp32-s3-micropython-blink` (ten), `esp32-robotics-bringup` (TODO — pełna procedura z sensorami)
- domena: `01-domains/embedded/`

---

name: gaja-lab-core
description: First-response workshop diagnostics for USB devices, serial ports, and embedded boards. Use when a device is just
  plugged in and you need VID/PID, port name, permission audit, or a board identification hint. Read-only — never flashes, never
  mounts, never writes to the device. Invoke the bundled `scripts/lab_helper.py` via terminal; every subcommand returns JSON.
status: accepted
platforms:
- linux
- macos
type: skill
id: skill-gaja-lab-core
title: gaja-lab-core — workshop USB/serial diagnostic foundation
owner: gaja
created_at: '2026-07-25'
updated_at: '2026-07-25'
review_due: '2027-01-25'
version: 1.0.0
heos_standard_version: '1.2'
tags:
- embedded
- workshop
- usb
- serial
- diagnostics
related:
- skill-esp32-s3-micropython-blink
quality_schema: pass
quality_technical: pass
quality_operational: unmeasured
---

# gaja-lab-core — workshop diagnostic foundation

> "Sprawdź, co zostało właśnie podłączone przez USB" → odpowiedź w jednym turnie.

## Cel

Dostarczyć **niezawodny, read-only, pure-stdlib Python** zestaw narzędzi do
szybkiej diagnostyki USB / serial / embedded w warsztacie. Pierwszy klockek
w łańcuchu narzędzi — wszystkie inne skille (ESP32 blink, RPi kiosk, etc.)
mogą z niego korzystać.

## Zakres

- **Wykrywanie urządzeń USB** (`lsusb`) z parsowaniem VID/PID
- **Identyfikacja płytki** z local VID/PID database (Espressif, Adafruit,
  FTDI, WCH CH340/CH9102, STM32, Raspberry Pi, Arduino, Nordic, Teensy)
- **Audyt portów serial** (`/dev/tty*`) z diagnostyką uprawnień
- **Diagnostyka środowiska** — czy masz odpowiednie narzędzia (`esptool`,
  `mpremote`, `arduino-cli`, `openocd`...)
- **Snapshot logu kernela** (filtrowany `dmesg`) dla eventów usb/serial

**NIE w zakresie** (kolejne pluginy):
- Wgrywanie firmware (użyj `esp32-s3-micropython-blink` lub `esp32-nuc-flash`)
- Debug JTAG/SWD (OpenOCD)
- Konfiguracja udev rules (osobny skill)
- Live monitoring nowych podłączeń (wymagałby pluginu, nie skilla)

## Kiedy używać

- ✅ User właśnie podłączył płytkę / debugger / konwerter USB-UART
- ✅ "Co to za urządzenie?" — bez nazwy, bez docs
- ✅ Flash nie działa, brak portu `/dev/ttyUSB0` — sprawdź czy kernel widzi
- ✅ Nowy host / nowa maszyna wirtualna — pełen audyt środowiska
- ✅ Pierwszy krok przed każdym embedded flow (RPi, ESP32, STM32, RP2040)

## Kiedy nie używać

- ❌ User chce wgrać firmware → idź do `esp32-s3-micropython-blink`
  albo `esp32-nuc-flash`
- ❌ Live monitoring (event gdy ktoś coś podłączy) → za to trzeba pluginu
  z hookem, nie jednorazowego odpytania
- ❌ Debug aplikacji na płytce (REPL, breakpoint) → mpremote / openocd
- ❌ Systemy bez `/dev` (kontenery, Windows) → skill jest Linux/macOS

## Filozofia: read-only or it didn't happen

**Helper nigdy nie:**
- Nie pisze do portu szeregowego (open tylko `O_RDONLY` via `cat`)
- Nie flashuje, nie wywołuje `esptool write_flash`
- Nie montuje dysków
- Nie modyfikuje `udev` rules
- Nie zmienia grup użytkownika
- Nie kasuje plików

**Helper zawsze:**
- Zwraca **JSON** (parsowalny przez agenta)
- Ma wbudowany timeout (żadna komenda nie zawiesi agenta na godziny)
- Łapie wyjątki (exit code != 0 z `errors[]`, ale nigdy nie crashuje)

## Workflow (jak agent ma tego używać)

### 1. Wykryj co się pojawiło

```bash
python3 scripts/lab_helper.py list-usb
```

Jeśli output ma nowe `address` względem poprzedniego odpytania → to jest
nowe urządzenie. Porównaj z `identify-board` żeby dostać nazwę płytki.

### 2. Zidentyfikuj płytkę

```bash
python3 scripts/lab_helper.py identify-board
```

Zwraca VID/PID + `board_hint` z lokalnej bazy. Jeśli `is_known: false`,
sprawdź `usb-ids.gowdy.us` albo `the-sz.com/products/usb/deskew` —
i powiedz userowi czego szukać.

### 3. Sprawdź czy są porty i uprawnienia

```bash
python3 scripts/lab_helper.py list-serial
python3 scripts/lab_helper.py check-permissions
```

Jeśli `readable: false` lub `writable: false` → `check-permissions`
zwraca gotowy fix: `sudo usermod -aG dialout <user>`, plus ostrzeżenie
że wymaga wylogowania.

### 4. (Opcjonalnie) Snapshot stanu środowiska

```bash
python3 scripts/lab_helper.py check-toolchain
```

Wykrywa `esptool`, `mpremote`, `arduino-cli`, `openocd`, `dfu-util`,
`picotool`, `tio`/`minicom`/`screen` — wszystko co może być potrzebne
w kolejnych krokach.

### 5. (Opcjonalnie) Diagnoza "dlaczego nie działa"

```bash
python3 scripts/lab_helper.py capture-dmesg --since "5 min ago"
```

Filtrowany `dmesg` dla eventów usb/serial. Pokaże np.
`ch341: failed to set default baud rate` albo
`cdc_acm: failed to set dtr/rts`.

### 6. (Opcjonalnie) Czytanie surowego deskryptora

```bash
python3 scripts/lab_helper.py read-descriptor 003:042
```

Pełen `lsusb -v` dla jednego urządzenia. Użyj gdy chcesz zobaczyć
klasę, interfejsy, endpointy, serial number.

## Polecenie użytkownika — wzorcowy flow

> **"Gaja, sprawdź co zostało właśnie podłączone przez USB"**

Agent powinien:

1. `lab_helper.py list-usb` — porównać z poprzednim stanem
2. Dla każdego nowego urządzenia: `identify-board` lub
   `read-descriptor <address>`
3. `list-serial` + `check-permissions` — czy user może otworzyć port
4. Zaproponować następny krok (np. "Wgrać MicroPython?
   → `esp32-s3-micropython-blink` skill")

## Dostępne komendy helpera (kompletna lista)

| Komenda | Output | Użycie |
|---|---|---|
| `list-usb [-v]` | wszystkie urządzenia USB, opcjonalnie z `lsusb -v` | inwentaryzacja |
| `list-serial` | `/dev/tty*` + perms + group | "czy widzę port?" |
| `identify-board` | VID/PID → nazwa płytki (best-effort) | "co to jest?" |
| `read-descriptor BBB:DDD` | pełen `lsusb -v` dla urządzenia | deep-dive |
| `read-serial-log /dev/ttyX` | ostatnie N linii z portu (cat + timeout) | "co płytka mówi?" |
| `check-permissions` | audyt uprawnień + gotowy fix | "dlaczego nie widzę portu?" |
| `check-toolchain` | dostępne dev-tools + install hint | "co mi brakuje?" |
| `capture-dmesg [--since X]` | filtrowany kernel log | "dlaczego to nie działa?" |

## VID/PID database (lokalna)

Pokrywa 25+ popularnych płytek. Rozszerzenia w pliku:
`scripts/lab_helper.py` → `BOARD_DB` dict.

Pełna referencja online: <http://www.linux-usb.org/usb-ids.html>

## Przykłady użycia (z prawdziwych sesji)

### Przykład 1: ESP32-S3-Pico zaraz po podłączeniu

User: "sprawdź co właśnie podłączyłem"

```json
{
  "tool": "list-usb",
  "data": {
    "basic": [{
      "bus": 3, "device": 7, "address": "003:007",
      "vid": "303a", "pid": "1001",
      "name": "Espressif ESP32-S3",
      "board_hint": "ESP32-S3 (ROM bootloader mode)"
    }]
  }
}
```

Następny krok: `esp32-s3-micropython-blink` skill.

### Przykład 2: Permission problem

User: "Wgrałem esptool ale dostaję Permission denied"

`check-permissions` zwraca:
```json
{
  "serial_group_membership": {"dialout": false, "tty": false, "uucp": false},
  "missing_groups": ["dialout"],
  "fix_suggestion": ["sudo usermod -aG dialout gaja", "→ log out and back in"]
}
```

### Przykład 3: Brak portu w ogóle

User: "Nie widzę /dev/ttyUSB0"

`list-serial` → `count: 0` + warning "nothing plugged in?".
`capture-dmesg --since "5 min ago"` → pustka albo `usb 3-1: device descriptor read/all, error -110`.

Następny krok: sprawdzić kabel (data vs charge-only) albo czy VID/PID w ogóle
pojawił się w `list-usb`.

## Pitfalle / Lessons Learned

1. **`/dev/tty` to character device**, nie directory. `iterdir()` na nim
   wybucha `NotADirectoryError`. Iteruj `/dev/` i filtruj po nazwie.
2. **`dmesg` wymaga roota** (lub grupy `kmem`) na większości dystrybucji.
   Helper wykrywa `permission denied` i zwraca gotowy komunikat z hintem.
3. **`arduino-cli --version` zwraca błąd** ("unknown flag: --version").
   Helper łapie to — entry zostaje, ale `version: "unknown"`. Nie jest
   to crash.
4. **Serial read z pustego portu** = timeout + warning, nie crash.
   Użytkownik może testować z `/dev/ttyUSB0` który ma zły baud — to nie
   błąd helpera, helper tylko czyta.
5. **VID/PID match w BOARD_DB to best-effort.** Ten sam VID (np. CP2102
   `10c4:ea60`) obsługuje 50+ różnych urządzeń. Helper mówi "Silicon
   Labs CP2102/CP2104", ale NIE wie czy to Wemos D1 czy Sonoff.
6. **Nie pytaj o VID/PID w runtime** — baza jest w skrypcie, łatwa do
   rozszerzenia. Dodaj nowy wpis do `BOARD_DB` gdy trafisz na nową płytkę.
7. **CH9102 vs CP2102 — różne VID/PID, ten sam use-case.** CH9102 ma
   `1a86:55d3/55d4`, CP2102 ma `10c4:ea60`. Adaptery CH9102 często
   wchodzą w tryb `cdc_acm` (pojawiają się jako `/dev/ttyACM*`), ale
   pod Linuksem bywają traktowane jako `/dev/ttyUSB*` (driver
   `ch341`). Diagnostyka: zawsze `lsusb -v` VID/PID przed założeniem
   jaki driver. Helper zwraca VID/PID w polu `usb.device.vid_pid`.
8. **ESP32-S3 native USB vs UART bridge** — dwa różne porty. Native USB
   (USB-C na płytce) = `/dev/ttyACM0` (CDC-ACM). UART bridge (external
   adapter) = `/dev/ttyUSB0`. Ten sam chip, dwa endpointy, dwa różne
   flow-control. mpremote działa z obu, ale `mpremote connect` potrzebuje
   świadomości który. Helper pokazuje oba w `usb.device.endpoints`.

## Instalacja (jednorazowa per host)

```bash
# 1. Skopiuj helper do katalogu skilla (albo użyj ścieżki HEOS)
chmod +x scripts/lab_helper.py

# 2. Opcjonalnie: link w /usr/local/bin
sudo ln -sf $(pwd)/scripts/lab_helper.py /usr/local/bin/lab_helper

# 3. Zależności systemowe (apt)
sudo apt install usbutils coreutils   # lsusb + dmesg
```

## Weryfikacja

Po utworzeniu skilla, zweryfikuj:

```bash
# 1. Helper działa
python3 scripts/lab_helper.py --version      # → "lab_helper 1.0.0"
python3 scripts/lab_helper.py list-usb       # → JSON, ok:true
python3 scripts/lab_helper.py check-permissions  # → JSON, ok:true

# 2. Skill jest dostępny dla agenta
# → agent załaduje go gdy user zapyta o USB/serial
```

## Rozszerzenia (kolejne wersje)

- **v1.1:** board database z wpisami z `usb-ids` (auto-sync)
- **v1.2:** `watch-usb` subcommand (inotify-based, ale read-only, no daemon)
- **v1.3:** integracja z `udev` rules audit (które reguły w `/etc/udev/rules.d/`
  dotyczą serial)
- **v2.0 (plugin mode):** jeśli user poprosi o live monitor, zamień
  skill + helper na plugin Python z FastAPI dashboardem + WS broadcast

## Powiązane

- `esp32-s3-micropython-blink` — używa helpera do wykrycia ESP32 przed flash
- `esp32-nuc-flash` — to samo, ale zdalnie (NUC → RPi)
- `pi-touchscreen-panel-bringup` — inny kąt warsztatu (HDMI panel)
- ADR-001 — MicroPython + mpremote dla ESP32-S3-PICO
- HEOS v1.2 standard (skill layout, JSON envelope)

## Wersjonowanie

- **v1.0** (2026-07-25) — pierwsza wersja. 8 subkomend, local VID/PID DB,
  pure stdlib (zero `pip install`), JSON output envelope.

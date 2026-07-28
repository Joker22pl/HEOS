---
type: skill
id: skill-embedded-communications-debug
name: embedded-communications-debug
title: Embedded Communications Debug — UART/I2C/SPI/CAN/USB-serial
description: Debug embedded communication buses (UART, I2C, SPI, CAN, USB-serial) on microcontrollers. Use when
  the user reports no response from a sensor, bus errors, framing issues, CRC mismatches, timeouts, or hardware
  not responding on expected pins. Triggered by keywords — UART, I2C, SPI, CAN, USB-serial, sensor not responding,
  bus error, NACK, framing error, CRC error.
status: accepted
owner: gaja
created_at: '2026-07-25'
updated_at: '2026-07-28'
review_due: '2027-01-25'
version: 0.3.1
heos_standard_version: "1.2"
tags:
- embedded
- robotics
- debugging
- uart
- i2c
- spi
- can
- usb-serial
- hardware
related:
- skill-gaja-lab-core
quality_schema: pass
quality_technical: pass
quality_operational: unmeasured
last_verified: 2026-07-26
verified_on: ESP32-S3 + I2C sensor (2026-07-25), UART debug session
---

# Embedded Communications Debug

## Cel

Diagnozuj problemy komunikacyjne w układach embedded i robotyce w sposób warstwowy,
bezpieczny i oparty na dowodach. Skill obejmuje UART, I2C, SPI, CAN oraz USB-serial
na platformach takich jak ESP32, RP2040/Raspberry Pi Pico, Arduino, Raspberry Pi,
Jetson i komputery z Linuxem, macOS lub Windowsem.

Nie zgaduj przypadkowych poprawek. Najpierw ustal warstwę awarii, przygotuj
minimalny test i zmieniaj tylko jeden parametr naraz.

## Zakres

**W zakresie:**

- Diagnostyka magistrali sprzętowych: UART TTL, RS-232, RS-485, I2C/SMBus, SPI, CAN/CAN FD, USB-serial (CDC ACM, FTDI, CP210x, CH34x, PL2103).
- Platformy: ESP32, ESP8266, RP2040, STM32, Arduino, Raspberry Pi, Jetson, NUC, Linux/macOS/Windows hosty.
- Objawy: brak odpowiedzi, puste/losowe dane, framing errors, NACK, bus-off, timeouty, błędy parsera.
- Pełen cykl: od enumeracji USB do diagnostyki warstwy fizycznej i protokołu.

**Poza zakresem (patrz inne Skills):**

- Identyfikacja płytki przy pierwszym podłączeniu → `gaja-lab-core`.
- Pierwszy flash i blink LED na ESP32 → `esp32-micropython-blink`, `esp32-robotics-bringup`.
- Debugging magistrali wyłącznie programowo (ROS 2, DDS, TCP/IP, Wi-Fi) → inne skille w zależności od kontekstu.
- Strojenie regulatorów silników, analiza RF, reverse-engineering protokołu z samego capture → ten skill to dopiero etap wstępny.

## Kiedy używać

- ✅ Urządzenie, czujnik lub mikrokontroler przestaje odpowiadać po UART, I2C, SPI, CAN lub USB-serial.
- ✅ Odbierane dane są puste, losowe, przesunięte albo uszkodzone (framing errors, CRC mismatch).
- ✅ Transmisja działa tylko czasami, po restarcie lub przy małej prędkości.
- ✅ Magistrala blokuje się: timeouty, NACK, bus-off, error-passive.
- ✅ Port szeregowy istnieje w systemie, ale aplikacja nie może go otworzyć.
- ✅ Po zmianie płytki, przewodu, konwertera lub firmware komunikacja przestała działać.
- ✅ Trzeba przygotować powtarzalną procedurę testową i raport diagnostyczny.

## Kiedy nie używać

- ❌ Debugging wyłącznie programowy (ROS 2, DDS, TCP/IP, Wi-Fi, Ethernet) bez warstwy sprzętowej.
- ❌ Strojenie regulatorów silników PID — to jest inna klasa diagnostyki.
- ❌ Analiza RF, dekodowanie sygnałów radiowych — poza zakresem.
- ❌ Reverse-engineering nieznanego protokołu wyłącznie z przechwyconych danych — ten skill daje ramy diagnostyczne, nie dekoder binarny.
- ❌ Naprawa zasilania lub problemów bezpieczeństwa — zatrzymaj się i eskaluj.

## Workflow

Workflow jest 7-etapowy i powtarzalny. Każdy etap ma **kryterium zakończenia**
(explicite `Kryterium:` na końcu). Nie przechodź dalej, dopóki kryterium nie jest spełnione.

### 1. Freeze the State (zamroź stan)

Zapisz bieżące połączenia, konfigurację, firmware i pełny objaw.
Nie zmieniaj układu przed utrwaleniem stanu.

**Kryterium:** istnieje krótki baseline pozwalający odtworzyć problem.

### 2. Classify the Failure Layer (przypisz warstwę awarii)

Przypisz problem do jednej lub kilku warstw:

| Warstwa | Typowe objawy |
|---|---|
| Fizyczna | luźny przewód, zły pin, za długi przewód, zamienione linie |
| Elektryczna | złe napięcie, brak wspólnej masy, brak pull-up/terminacji, przeciążenie |
| Konfiguracja | zły port, baud rate, adres, tryb SPI, bitrate CAN |
| Protokół | zła ramka, kolejność bajtów, CRC, wymagany handshake |
| Sterownik/OS | brak urządzenia, prawa dostępu, konflikt procesu, reset portu |
| Aplikacja | zły parser, timeout, buforowanie, blokada wątku, błędna inicjalizacja |

**Kryterium:** każda aktywna hipoteza ma przypisaną warstwę i obserwację, która ją wspiera.

### 3. Prove Power, Ground, and Logic Levels (potwierdź warstwę elektryczną)

Sprawdź napięcie zasilania modułu, napięcie logiki, ciągłość GND, stan linii w spoczynku,
orientację złączy i obecność konwertera poziomów.

**Kryterium:** połączenie jest elektrycznie zgodne albo wskazano konkretną niezgodność.

### 4. Reduce to a Minimal Reproducible Link (zredukuj do minimalnego testu)

Odłącz elementy niepotrzędne. Jeden host, jedno urządzenie, krótkie przewody,
minimalny firmware, konserwatywna prędkość, prosty komunikat testowy.

**Kryterium:** problem występuje lub znika w minimalnym układzie, co zawęża warstwę awarii.

### 5. Test One Direction at a Time (testuj jeden kierunek naraz)

Oddzielnie: wykrywanie/inicjalizacja, host→urządzenie, urządzenie→host,
parsowanie odpowiedzi, zachowanie po restarcie i ponownym otwarciu.

**Kryterium:** wiadomo, w którym kierunku i etapie pojawia się pierwszy błąd.

### 6. Change One Variable (zmieniaj jedną zmienną naraz)

Dla każdej próby zapisz hipotezę, jedną zmianę, oczekiwany wynik, wynik rzeczywisty, wniosek.

**Kryterium:** wynik testu zwiększa lub zmniejsza prawdopodobieństwo konkretnej hipotezy.

### 7. Validate the Fix (sprawdź poprawkę)

Po znalezieniu poprawki: przywróć docelową konfigurację etapami, wykonaj zimny start,
serię powtórzeń, dłuższą transmisję, hot-unplug/replug. Potwierdź, że poprawka nie
mimikuje fix zmniejszeniem prędkości lub zwiększeniem timeoutu.

**Kryterium:** rozwiązanie jest powtarzalne i wyjaśnia przyczynę, nie tylko usuwa objaw.

### Routing Table — wybór referencji

Załaduj tylko referencję odpowiadającą badanemu interfejsowi:

| Problem | Referencja |
|---|---|
| UART TTL, RS-232/RS-485 przez konwerter, framing, baud rate | `${HERMES_SKILL_DIR}/references/uart.md` |
| I2C/SMBus, adresy, pull-up, SDA/SCL, NACK, bus stuck | `${HERMES_SKILL_DIR}/references/i2c.md` |
| SPI, CS, CPOL/CPHA, bit order, MISO/MOSI | `${HERMES_SKILL_DIR}/references/spi.md` |
| CAN/CAN FD, terminacja, bitrate, bus-off, SocketCAN | `${HERMES_SKILL_DIR}/references/can.md` |
| USB-UART, CDC ACM, enumeracja, sterownik, COM/tty | `${HERMES_SKILL_DIR}/references/usb-serial.md` |

Jeśli problem obejmuje adapter USB-UART, załaduj najpierw `usb-serial.md`, a następnie `uart.md`.

## Przykłady

### Przykład 1: ESP32-S3 milczy po podłączeniu — zły kierunek TX/RX

**Sytuacja:** ESP32-S3 Feather podłączony do USB-UART adaptera (CH9102). Adapter widoczny
w `lsusb`, port `/dev/ttyACM0` istnieje, ale `mpremote` i `screen` nie odbierają REPL.
`dmesg` czyste, `udevadm info` pokazuje poprawny VID:PID. Po podłączeniu pin `RX` adaptera
do pinu `TX` ESP32 (zamiast `RX`).

**Diagnoza:** routing table → `usb-serial.md` (port widoczny) → `uart.md` (loopback na adapterze
przechodzi) → Test Static CS/Voltage (TX adaptera ma ~3.3 V w idle, RX ESP32 ma ~3.3 V) → Warstwa
fizyczna: zamienione TX/RX.

**Poprawka:** skrzyżuj linie (adapter TX → ESP32 RX, adapter RX ← ESP32 TX), upewnij się że
GND jest wspólny.

**Wynik:** REPL odpowiada, `mpremote eval "print('hello')"` zwraca `hello`.

### Przykład 2: I2C OLED SSD1306 — brak ACK na 0x3C

**Sytuacja:** OLED SSD1306 podłączony do ESP32-S3 przez I2C (SDA=8, SCL=9). Biblioteka
`ssd1306` zwraca `OSError: [Errno 5] No such device or address`. Dwa OLED-y na tej samej
szynie (drugi na 0x3D).

**Diagnoza:** routing table → `i2c.md` → Linux I2C: `i2cdetect -y 1` → `i2cdetect` pokazuje
tylko `0x3D`, brak `0x3C`. Test D (Known Register) na 0x3C: NACK. Warstwa elektryczna:
pull-upy na module — sprawdź rezystancję SDA→VCC i SCL→VCC (4.7 kΩ każdy). Zmierz napięcie
VCC modułu — 0 V.

**Poprawka:** sprawdź zasilanie modułu OLED (przewód VCC przerwany przy złączu). Po naprawie
i2cdetect pokazuje `0x3C`.

**Wynik:** biblioteka inicjalizuje się poprawnie, OLED wyświetla splash.

### Przykład 3: CAN node zgłasza bus-off po restarcie

**Sytuacja:** dwa node'y CAN na izolowanej magistrali testowej, bitrate 500 kbit/s,
terminacja 120 Ω na obu końcach. Po restarcie jednego node'a wchodzi w bus-off.

**Diagnoza:** routing table → `can.md` → Passive Checks First: rezystancja CANH-CANL ~60 Ω ✓.
Powered Idle Check: napięcia w recesywnym ~2.5 V ✓. Bit Timing: oba node'y 500 kbit/s, sample
point ~87.5% ✓. Minimal Two-Node Test: node A nadaje, node B widzi ramki, ale licznik `berr-counter
tx` rośnie. Symptom Map → ACK Errors → tylko jeden aktywny node (B w silent mode). Warstwa
konfiguracja: tryb transceivera B w standby.

**Poprawka:** wybudź transceiver B (pin STB/EN), restart node'a. Po fix licznik błędów 0.

**Wynik:** magistrala działa stabilnie po wielu restartach.

### Przykład 4: Najczęstsze komendy debug (copy-paste)

```bash
# 1. Identyfikacja portu
lsusb
ls -la /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
dmesg | tail -20

# 2. UART loopback (zwarcie RX↔TX adaptera)
stty -F /dev/ttyACM0 115200 raw -echo
echo "hello" > /dev/ttyACM0
cat /dev/ttyACM0  # powinno zwrócić "hello"

# 3. I2C scan (wymaga i2c-tools)
sudo i2cdetect -y 1        # scan na bus 1 (RPi)
sudo i2cget -y 1 0x3C 0x00 # odczyt rejestru 0x00 z urządzenia 0x3C

# 4. SPI loopback (zwarcie MOSI↔MISO)
sudo spi-tools -d /dev/spidev0.0 -s 1000000 \
     -w "\xAA\x55" -r 4    # wyślij 2 bajty, odbierz 4

# 5. CAN dump (wymaga can-utils)
candump can0               # pasywny listening
cansend can0 123#DEADBEEF  # nadaj ramkę

# 6. USB-serial: VID/PID lookup
udevadm info -a -p /dev/ttyACM0 | grep -E "ATTRS{idVendor}|ATTRS{idProduct}"
```

**Pass gdy:** każda komenda zwraca oczekiwany output dla twojego peryferyjnego.

## Lessons Learned

- **Warstwa fizyczna przed aplikacją.** 80% "bugów w kodzie" to zły pin, brak GND lub brak
  pull-up. Zmierz napięcie i ciągłość ZANIM otworzysz edytor.
- **Adres I2C 7-bit vs 8-bit.** Dokumentacja i biblioteka mogą podawać różne formaty. Przelicz
  zawsze: `8-bit write = (7-bit << 1) | 0`, `8-bit read = (7-bit << 1) | 1`. Przykład: 7-bit
  `0x68` → write `0xD0`, read `0xD1`.
- **USB D+/D− NIE TO SAMO CO UART TTL.** Podłączenie USB bezpośrednio do pinów TX/RX niszczy
  mikrokontroler. Użyj osobnego adaptera USB-UART (CH340/CH9102/FTDI/CP2102) z konwersją
  napięcia na 3.3 V.
- **CAN bez transceivera = spalony pin kontrolera.** Linie CANH/CANL wymagają transceivera
  (SN65HVD230, TJA1050, MCP2551). Bez niego zwarcie lub przepięcie uszkadza CAN controller.
- **DTR/RTS resetuje płytkę.** ESP32, Arduino i inne MCU wchodzą w bootloader przy otwarciu
  portu z DTR/RTS active. Jeśli test wymaga stanu runtime, wyłącz te linie w terminalu
  (`stty -F /dev/ttyACM0 -hupcl`) lub w aplikacji.
- **ModemManager na Linuksie.** Może chwilowo zająć nowy port i wysłać komendy AT, co resetuje
  urządzenie. Sprawdź `lsof /dev/ttyUSB0` i wyklucz VID:PID przez regułę udev.
- **Loopback adaptera USB-UART NIE dowodzi poprawności celu.** Dowodzi tylko, że host,
  sterownik, port i tor adaptera działają. Separacja USB↔UART to fundamentalna technika.
- **`${HERMES_SKILL_DIR}` jest rozwiązywane przez Hermes.** Ścieżki referencji w body SKILL.md
  mogą używać tej zmiennej — loader Hermesa rozwiązuje ją przed dostarczeniem treści
  (sprawdzone w `tests/agent/test_skill_commands.py:766-831`). NIE flaguj tych ścieżek
  jako hardcoded.

## Typowe błędy

- **Naprawianie aplikacji przed potwierdzeniem warstwy elektrycznej.** Pinout, masa, pull-upy —
  najpierw.
- **Mylenie numeru GPIO z numerem fizycznego pinu.** Pin 11 na złączu ≠ GPIO11.
- **Zakładanie wspólnego poziomu 3,3 V/5 V.** RPi 3.3 V, Arduino Uno 5 V — brak konwersji = uszkodzenie.
- **Wykonywanie wielu zmian przed ponownym testem.** Każda zmiana musi mieć hipotezę i być jedna.
- **Uznanie pojedynczej udanej ramki za stabilne rozwiązanie.** Powtórz 100×, sprawdź dłuższą sesję.
- **Ignorowanie resetu urządzenia wywoływanego przez DTR/RTS.** Pierwsza ramka po otwarciu portu
  to często boot, nie runtime.
- **Zwiększanie timeoutu bez wyjaśnienia źródła opóźnienia.** Timeout maskuje problem, nie rozwiązuje.
- **Traktowanie "urządzenie widoczne w systemie" jako dowodu poprawnej komunikacji protokołu.**
  `lsusb` widzi VID:PID, ale protokół może być źle zinterpretowany.

## Debugging

| Objaw | Przyczyna | Fix |
|---|---|---|
| Port widoczny w `lsusb`, brak `/dev/tty*` | brak sterownika, urządzenie w trybie bootloadera, zły VID:PID | `dmesg -w`, sprawdź `modinfo <driver>`, zainstaluj brakujący moduł |
| `i2cdetect` pokazuje same `UU` lub `--` | SDA zwarte, brak pull-up, magistrala zawieszona | sprawdź ciągłość SDA/SCL, pull-upy, bus recovery |
| CAN wchodzi w bus-off natychmiast | brak ACK (słuchacz w listen-only), bitrate mismatch, zwarcie | sprawdź `ip -details -statistics link show can0`, potwierdź dwa aktywne node'y |
| SPI zwraca same `0xFF` | MISO w Hi-Z, brak aktywnego CS, zły pin | sprawdź stan CS oscyloskopem/LED, zweryfikuj wiring |
| UART zamienia działający ruch w garbage | baud rate, inwersja, napięcie logiki | zweryfikuj baud rate na obu stronach, sprawdź czy nie ma inwersji (RS-232) |
| Adapter USB-UART działa, urządzenie nie | zły kierunek TX/RX, brak GND, level mismatch | sprawdź napięcie TX adaptera, skrzyżuj TX/RX, potwierdź wspólny GND |

## Narzędzia

- `lsusb`, `ls -l /dev/serial/by-id/`, `dmesg --follow`, `udevadm monitor --property` — enumeracja USB.
- `stty -F /dev/ttyUSB0 -a` — konfiguracja portu szeregowego.
- `i2cdetect`, `i2cdump`, `i2cset` (z pakietu `i2c-tools`) — diagnostyka I2C.
- `smbus2` (Python) — fallback skanowania I2C bez `i2c-tools`.
- `ip -details -statistics link show can0`, `candump`, `cansend` (z `can-utils`) — diagnostyka CAN.
- `miniterm` (Python `pyserial`) — terminal szeregowy bez instalacji dedykowanego klienta.
- Oscyloskop / analizator logiczny (Saleae, Hantek, sigrok) — narzędzia wyższego poziomu, gdy
  diagnostyka niskonarzędziowa nie daje rozstrzygającego dowodu.
- Multimetr — absolutne minimum (napięcie, rezystancja, ciągłość).

## Oficjalne źródła

- Espressif ESP32 Technical Reference Manual — sekcje o UART, I2C, SPI, USBSerial.
- NXP UM10204 — I2C-bus specification and user manual.
- Motorola/Freescale/NXP — Bosch CAN Specification 2.0 i CAN FD 1.0.
- USB 2.0 Specification (USB Implementers Forum) — klasy CDC, HID, vendor.
- Linux kernel docs — `Documentation/admin-guide/devices.txt`, `Documentation/i2c/`, `Documentation/networking/can.rst`.
- Microsoft docs — Win32_SerialPort, Win32_PnPEntity.

## Wersjonowanie

- **v0.1.0** (2026-07-25) — pierwsza wersja runtime w profilu `gaja`. Tylko frontmatter runtime minimum.
- **v0.1.1** (2026-07-25) — audyt pojedynczego skilla (peer review): 9 poprawek (P0+P1+P2+P3).
  Przeniesienie do kategorii `hardware/`, nowy trigger-focused description, normalizacja numeracji
  testów (`### Test A/B/C/D`), akcje domyślne w Stop Conditions, Evidence Priority z oscyloskopem,
  fallbacks I2C, flow control w UART Symptom Map.
- **v0.2.0** (2026-07-25) — migracja do HEOS. Pełny frontmatter v1.2 (13 pól), 7 obowiązkowych sekcji
  HEOS (Cel/Zakres/Kiedy używać/Kiedy nie używać/Workflow/Przykłady/Lessons Learned), 8 opcjonalnych.
  Sekcje Przykłady (3 use-case'y), Lessons Learned z obserwacjami z audytu peer review.

## Checklisty

### Pre-flight (przed rozpoczęciem diagnostyki)

- [ ] Czy zebrałem Information Contract (modele płytek, napięcia logiki, parametry, objaw, ostatnia zmiana)?
- [ ] Czy zasilanie jest wyłączone przed zmianą przewodów?
- [ ] Czy mam kompletny baseline (firmware, konfiguracja, pełen objaw)?
- [ ] Czy wybrałem właściwą referencję z Routing Table?

### Post-use (po zakończeniu)

- [ ] Czy zapisano przyczynę źródłową, nie tylko obejście?
- [ ] Czy poprawka zweryfikowana po restarcie i w serii powtórzeń?
- [ ] Czy przywrócono docelową konfigurację (nie zostawiono minimalnego układu)?
- [ ] Czy wyciągnąłem wnioski do Lessons Learned (profil lub ten Skill)?

## Najlepsze praktyki

1. **Zawsze mierz, zanim zaczniesz zgadywać.** Multimetr w ręku, datasheet na drugim ekranie.
2. **Jeden test = jedna hipoteza.** Bez wyjątków.
3. **Minimalny układ ZANIM pełnym stosem.** Nie debuguj ROS 2 jeśli I2C nie działa.
4. **Zapisuj baseline PRZED zmianą.** Bez baseline'u nie masz reproducer'a.
5. **Nie zwiększaj timeoutu jako fix.** To nie jest fix, to maskowanie.
6. **Używaj stabilnej ścieżki urządzenia** (`/dev/serial/by-id/`, reguła udev z numerem seryjnym).
7. **Oddzielaj warstwy w raporcie.** Każda hipoteza ma warstwę i obserwację.
8. **Pierwsza udana ramka to nie stabilne rozwiązanie.** Powtórz 100×.

## Powiązane

- **skill-gaja-lab-core** (peer, HEOS): first-response workshop diagnostics dla VID/PID i portów — ładuj PRZED tym skillem, gdy urządzenie jest właśnie podłączone.
- **skill-esp32-s3-micropython-blink** (peer, HEOS): flash i blink LED na ESP32-S3 — verify płytka żyje ZANIM zaczniesz komunikację z peryferiami.
- **skill-systematic-debugging** (runtime Hermes, profil `gaja`): ogólna 4-fazowa metoda debugowania — uzupełnia ten skill, nie zastępuje go. Skille embedded `esp32-robotics-bringup` są peerami runtime, nie HEOS, więc nie są cytowane w `related` (cross-tree boundary).


## Verification

> Skill jest proceduralny (komunikacja embedded: UART/I2C/SPI/CAN/USB-serial). Verification sprawdza, czy każdy kanał diagnostyczny daje wiarygodny wynik.

- **Komenda (UART loopback):** `minicom -D /dev/ttyUSB0 -b 115200` + zwarcie TX↔RX
  - **Oczekiwany output:** echo wpisanych znaków
  - **Pass gdy:** pełny loopback działa (port + baud + wiring OK)
  - **Czas:** < 30s

- **Komenda (I2C scan):** `i2cdetect -y 1` (lub `i2cdetect -y 0` na starszych RPi)
  - **Oczekiwany output:** tabela z adresami widocznych urządzeń (np. `0x3c` SSD1306)
  - **Pass gdy:** znane urządzenie widoczne pod oczekiwanym adresem
  - **Czas:** < 1s

- **Komenda (SPI loopback):** `spidev_test -D /dev/spidev0.0 -v -l` (jeśli dostępne)
  - **Oczekiwany output:** sekwencja bajtów 0x00..0xFF odebrana poprawnie
  - **Pass gdy:** TX == RX dla zwarcia MOSI↔MISO
  - **Czas:** < 5s

- **Komenda (CAN bus):** `candump can0` (z `can-utils`)
  - **Oczekiwany output:** ramki CAN z ID + payload (jeśli druga strona nadaje)
  - **Pass gdy:** widoczne ramki z oczekiwanym ID
  - **Czas:** interaktywny

- **Test integracyjny (pełen embedded debug):**
  - **Setup:** nowe urządzenie peryferyjne podłączone do MCU
  - **Kroki:**
    1. Identyfikacja portu: `lsusb` / `ls /dev/tty*` / `dmesg | tail -20`
    2. Wiring check: multimetr (VCC, GND, sygnał)
    3. Loopback test (jeśli UART/SPI) → port OK?
    4. Protocol-specific test (I2C scan / CAN dump)
    5. Logi: `dmesg -w` + `journalctl -f` (obserwuj w trakcie operacji)
  - **Kryterium PASS:** wszystkie 5 kroków zielone + peryferyjne działa end-to-end
  - **Kryterium FAIL:** którykolwiek FAIL → sprawdź odpowiedni krok (hardware → software → protocol)

- **Audit (kwartalny):** sprawdź czy nowe wersje firmware nie zmieniły pinout/baudrate dla znanych peryferii.
# USB-Serial Debugging Reference

## Scope

Adaptery USB-UART oraz urządzenia implementujące port szeregowy przez USB, np. CDC ACM, FTDI, CP210x, CH34x, PL2303 i wbudowane mostki debugowe. Referencja rozdziela problem enumeracji USB od problemu transmisji UART.

Po potwierdzeniu poprawnego portu i sterownika załaduj także `uart.md`.

## Layer Model

Diagnozuj kolejno:

1. zasilanie i kabel USB;
2. enumeracja urządzenia;
3. sterownik systemowy;
4. utworzenie portu COM/tty;
5. uprawnienia i wyłączność portu;
6. reset/boot mode;
7. parametry UART;
8. protokół aplikacyjny.

Widoczność portu nie dowodzi poprawności sygnałów UART po stronie pinów adaptera.

## Symptom Map

| Objaw | Najpierw sprawdź |
|---|---|
| Brak reakcji po podłączeniu | kabel data, port USB, zasilanie, urządzenie |
| Jest w `lsusb`, brak tty | sterownik, tryb urządzenia, log kernela |
| tty pojawia się i znika | reset, zasilanie, uszkodzony kabel, bootloader |
| Permission denied | grupy, ACL, sandbox, właściciel urządzenia |
| Device busy | monitor szeregowy, IDE, ModemManager, inny proces |
| Port zmienia nazwę | `/dev/serial/by-id`, bootloader, inny VID/PID |
| Otwiera port i resetuje płytkę | DTR/RTS, auto-reset |
| Flash działa, terminal nie | inny port funkcji, parametry UART, firmware |
| Terminal działa, aplikacja nie | konfiguracja, line ending, parser, blokada portu |

## Cable and Power

Najpierw zamień jedną rzecz:

- użyj znanego kabla z transmisją danych;
- podłącz bezpośrednio bez huba;
- użyj innego portu USB;
- odłącz urządzenia pobierające dużo prądu;
- sprawdź, czy kabel nie jest wyłącznie zasilający;
- sprawdź napięcie zasilania docelowej płytki.

Nie podawaj jednocześnie dwóch niezależnych źródeł zasilania na tę samą szynę bez znajomości schematu.

## Linux Enumeration Workflow

Uruchom obserwację przed podłączeniem (najlepiej równolegle w drugim terminalu):

```bash
dmesg --follow
```

Jako uzupełnienie — czysty sygnał z warstwy urządzeń, bez kernelowego szumu:

```bash
udevadm monitor --property --subsystem-match=tty
```

Następnie:

```bash
lsusb
ls -l /dev/serial/by-id/ 2>/dev/null
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

Zbierz informacje o konkretnym porcie:

```bash
udevadm info --query=all --name=/dev/ttyUSB0
```

Sprawdź, kto używa portu:

```bash
lsof /dev/ttyUSB0 2>/dev/null
fuser -v /dev/ttyUSB0 2>/dev/null
```

Nie zakładaj nazwy `/dev/ttyUSB0`. Urządzenia CDC ACM zwykle tworzą `/dev/ttyACM*`, a numer może się zmieniać.

Preferuj stabilną ścieżkę:

```text
/dev/serial/by-id/<vendor_model_serial>
```

## Permissions on Linux

Sprawdź:

```bash
ls -l /dev/ttyUSB0
id
getfacl /dev/ttyUSB0 2>/dev/null
```

Typowym rozwiązaniem jest członkostwo w grupie posiadającej port, często `dialout`, ale nazwa zależy od systemu. Po zmianie grupy wymagana może być nowa sesja logowania.

Nie ustawiaj stałego `chmod 777` i nie uruchamiaj całego środowiska jako root. Dla urządzeń produkcyjnych użyj precyzyjnej reguły udev opartej na VID/PID i, najlepiej, numerze seryjnym.

## Driver and VID/PID

`lsusb` pokaże VID:PID. Ustal:

- producenta mostka;
- używany moduł kernela;
- czy urządzenie ma kilka funkcji USB;
- czy bootloader i aplikacja mają różne VID/PID;
- czy tani adapter nie zgłasza się jako niezgodny klon.

Na Linuxie można sprawdzić powiązanie sterownika przez `udevadm` i log kernela. Nie pobieraj losowego sterownika z nieznanej strony.

## ModemManager and Auto-Probing

Na części dystrybucji ModemManager może otwierać nowe porty i wysyłać komendy. Objawy:

- port chwilowo zajęty;
- nieoczekiwane bajty;
- reset urządzenia;
- opóźnienie po podłączeniu.

Najpierw potwierdź proces przez `lsof`/`fuser` i logi. Nie wyłączaj globalnie usług bez dowodu. Preferuj regułę wykluczającą konkretne urządzenie.

## DTR/RTS and Auto-Reset

Płytki Arduino, ESP32 i inne mogą używać DTR/RTS do resetu lub wejścia w bootloader. Otwieranie portu może:

- zresetować firmware;
- zmienić port;
- spowodować utratę pierwszych logów;
- pozostawić układ w trybie programowania.

Zapisz stany DTR/RTS używane przez terminal i aplikację. Po otwarciu portu odczekaj czas startu tylko wtedy, gdy reset został potwierdzony.

## Native USB vs USB-UART

Urządzenie może mieć:

- osobny mostek USB-UART;
- natywne USB kontrolera;
- jednocześnie port debug i port aplikacyjny;
- port bootloadera i port runtime.

Nie zakładaj, że port użyty do flashowania jest tym samym portem, którym firmware wysyła dane.

## Windows Workflow

W Menedżerze urządzeń sprawdź:

- kategorię `Ports (COM & LPT)`;
- dokładną nazwę urządzenia;
- numer COM;
- identyfikatory sprzętu VID/PID;
- kod błędu sterownika.

PowerShell:

```powershell
Get-PnpDevice -Class Ports
Get-CimInstance Win32_SerialPort |
  Select-Object DeviceID, Name, PNPDeviceID
```

Po przejściu do bootloadera urządzenie może otrzymać inny numer COM.

## macOS Workflow

Sprawdź:

```bash
ls -l /dev/cu.* /dev/tty.* 2>/dev/null
system_profiler SPUSBDataType
```

Do inicjowania połączenia szeregowego zwykle używa się `/dev/cu.*`; dokładne zachowanie zależy od aplikacji i sterownika.

## Stable Device Naming

Dla wielu robotów nie używaj na stałe `/dev/ttyUSB0`. Stosuj:

1. `/dev/serial/by-id/`, jeśli urządzenie ma unikalny serial;
2. regułę udev z VID, PID i numerem seryjnym;
3. dodatkowe kryterium fizycznego portu tylko wtedy, gdy urządzenie nie ma serialu.

Przykładowy kierunek reguły, który trzeba dopasować do rzeczywistych danych:

```udev
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", \
ATTRS{serial}=="REAL_SERIAL", SYMLINK+="robot/controller"
```

Nie kopiuj wartości przykładowych bez odczytania `udevadm info`.

## Separation Test

Aby rozdzielić USB od UART:

1. potwierdź stabilną enumerację;
2. wykonaj loopback adaptera zgodnie z `uart.md`;
3. dopiero potem połącz docelową płytkę;
4. sprawdź napięcie TX adaptera;
5. sprawdź, czy GND i TX/RX są poprawne;
6. uruchom prosty wzorzec sekwencyjny.

Wyniki:

- brak enumeracji → warstwa USB/kabel/zasilanie;
- enumeracja bez portu → sterownik/funkcja USB;
- port działa, loopback nie → adapter/sterownik/konfiguracja;
- loopback działa, cel nie → UART/pinout/firmware/protokół.

## USB-Serial Completion Checklist

- [ ] Użyto potwierdzonego kabla danych.
- [ ] Zapisano VID/PID i log enumeracji.
- [ ] Ustalono dokładny port i stabilną ścieżkę.
- [ ] Sprawdzono sterownik, uprawnienia i proces blokujący.
- [ ] Ustalono wpływ DTR/RTS i resetu.
- [ ] Rozróżniono port bootloadera, debug i runtime.
- [ ] Adapter przeszedł test loopback.
- [ ] Po warstwie USB wykonano diagnostykę z `uart.md`.

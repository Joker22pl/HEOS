# UART Debugging Reference

## Scope

UART TTL oraz połączenia realizowane przez odpowiednie konwertery, np. USB-UART, RS-232 lub RS-485. Nie łącz bezpośrednio elektrycznie UART TTL z RS-232 albo RS-485.

## Electrical Identity First

Ustal dla obu stron:

- poziom logiki: najczęściej 1,8 V, 3,3 V albo 5 V;
- czy wejścia są tolerancyjne na wyższe napięcie;
- czy interfejs jest TTL/CMOS, RS-232 czy RS-485;
- czy wymagany jest wspólny GND;
- czy sygnał nie jest odwrócony przez konwerter;
- czy linie są oznaczone z perspektywy nadajnika czy złącza.

Typowe UART TTL:

```text
TX urządzenia A -> RX urządzenia B
RX urządzenia A <- TX urządzenia B
GND A           -- GND B
```

Nie podłączaj równolegle dwóch aktywnych wyjść TX.

## Configuration Matrix

Zapisz pełną konfigurację, nie tylko baud rate:

```text
baud rate:
data bits:
parity:
stop bits:
flow control:
idle polarity / inversion:
line ending:
encoding:
packet framing:
timeout:
```

Popularny zapis `115200 8N1` oznacza 115200 bit/s, 8 bitów danych, brak parzystości i 1 bit stopu.

## Symptom Map

| Objaw | Najpierw sprawdź |
|---|---|
| Brak danych w obu kierunkach | GND, skrzyżowanie TX/RX, właściwy port, poziomy napięć |
| Losowe znaki | baud rate, zegar, inversion, poziom logiki |
| Działa tylko jeden kierunek | konkretna linia TX/RX, konfiguracja pinu, bufor kierunkowy |
| Pierwsze bajty giną | reset, DTR/RTS, czas uruchamiania, opróżnianie bufora |
| Dane urywają się | flow control (RTS/CTS lub XON/XOFF), przepełnienie bufora, timeout, obciążenie CPU |
| Duża strata pakietów przy dużym obciążeniu | brak hardware flow control albo zbyt mały bufor po stronie firmware |
| Działa przy małej prędkości | jakość przewodów, poziomy, zegar, obciążenie, konwerter |
| Odpowiedź ma echo | lokalne echo terminala lub echo firmware |
| Port zajęty | inny proces, monitor szeregowy, ModemManager |

## Minimal Test Sequence

### Test A — Static Electrical Check

Przy włączonym, poprawnie zasilonym urządzeniu i bez transmisji zmierz napięcie TX względem GND. UART TTL zwykle pozostaje w stanie wysokim w spoczynku, ale dokumentacja urządzenia ma pierwszeństwo.

**Interpretacja:**

- brak sensownego poziomu: zły pin, brak zasilania, pin nie jest UART albo jest w Hi-Z;
- napięcie wyższe niż tolerancja odbiornika: zatrzymaj test i użyj konwersji poziomów;
- poziom ujemny lub znacznie wyższy: możliwy RS-232, nie UART TTL.

### Test B — Adapter Loopback

Tylko dla samodzielnego adaptera USB-UART o potwierdzonym napięciu:

1. odłącz adapter od docelowego urządzenia;
2. połącz TX adaptera z RX adaptera;
3. otwórz port z wyłączonym lokalnym echem;
4. wyślij znany tekst;
5. potwierdź identyczny odbiór.

Udany loopback dowodzi działania hosta, sterownika, portu i toru adaptera. Nie dowodzi poprawności docelowego urządzenia.

### Test C — One-Way Known Pattern

Nadaj cyklicznie wzorzec łatwy do rozpoznania:

```text
UART_TEST seq=0001\r\n
UART_TEST seq=0002\r\n
```

Sekwencja ujawnia utratę, duplikację i zmianę kolejności danych.

## Linux Checks

```bash
ls -l /dev/serial/by-id/ 2>/dev/null
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
dmesg --follow
stty -F /dev/ttyUSB0 -a
```

Konserwatywny test tekstowy po ustawieniu parametrów:

```bash
stty -F /dev/ttyUSB0 115200 cs8 -cstopb -parenb -ixon -ixoff raw -echo
cat /dev/ttyUSB0
```

W drugim terminalu:

```bash
printf 'PING\r\n' > /dev/ttyUSB0
```

Dla danych binarnych nie oceniaj transmisji przez zwykły terminal. Zapisz strumień i pokaż go w hex:

```bash
timeout 5 cat /dev/ttyUSB0 > /tmp/uart.bin
xxd /tmp/uart.bin
```

Nie instaluj dodatkowych pakietów bez potrzeby. Jeżeli `pyserial` jest już dostępny, można użyć `python -m serial.tools.miniterm`, ale nie traktuj go jako wymaganego.

## Windows Checks

Sprawdź Menedżer urządzeń i rzeczywisty numer COM. W PowerShell:

```powershell
Get-CimInstance Win32_SerialPort |
  Select-Object DeviceID, Name, PNPDeviceID
```

Port COM może zmienić numer po użyciu innego gniazda USB lub wejściu urządzenia w bootloader.

## Firmware Checks

- pin mux został ustawiony na właściwy UART;
- wskazano poprawny numer kontrolera UART;
- TX i RX nie są współdzielone z bootloaderem lub logami;
- bufor odbiorczy jest czytany wystarczająco często;
- ISR nie wykonuje ciężkiej pracy;
- parser potrafi odzyskać synchronizację po uszkodzonym bajcie;
- logowanie debug nie miesza się z protokołem na tym samym porcie;
- urządzenie nie resetuje się przy otwarciu portu.

## Clock Error

Przy losowych znakach lub błędach framing sprawdź źródło zegara i dokładność baud rate obu stron. Wbudowany oscylator może być niewystarczająco dokładny w skrajnej temperaturze lub przy określonych dzielnikach.

Nie zwiększaj arbitralnie prędkości. Najpierw sprawdź stabilność na konserwatywnej wartości, a później zwiększaj ją etapami.

## RS-232 and RS-485 Notes

### RS-232

- napięcia mogą być dodatnie i ujemne;
- logika jest odwrócona względem typowego UART TTL;
- wymagany jest transceiver, np. klasy MAX3232 dla odpowiedniego napięcia.

### RS-485

- wymaga transceivera różnicowego;
- sprawdź A/B zgodnie z dokumentacją konkretnego producenta — nazewnictwo bywa niejednoznaczne;
- w half-duplex sprawdź sterowanie DE/RE;
- terminacja i biasing zależą od topologii;
- kolizje mogą wynikać z jednoczesnego nadawania wielu węzłów.

## UART Completion Checklist

- [ ] Potwierdzono typ elektryczny interfejsu.
- [ ] Potwierdzono napięcia obu stron.
- [ ] TX i RX są skrzyżowane, a GND poprawny.
- [ ] Zapisano pełny format transmisji.
- [ ] Adapter przeszedł loopback, jeśli dotyczy.
- [ ] Oddzielnie sprawdzono oba kierunki.
- [ ] Parser przetestowano na znanym wzorcu i sekwencji.
- [ ] Poprawkę sprawdzono po ponownym otwarciu portu i restarcie.

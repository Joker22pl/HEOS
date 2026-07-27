# CAN Debugging Reference

## Scope

CAN Classic i CAN FD w robotyce, automatyce i systemach embedded. Obejmuje warstwę fizyczną, transceivery, terminację, bitrate, stany błędów oraz podstawy SocketCAN.

Nie wysyłaj ramek na aktywną magistralę pojazdu, maszyny lub systemu bezpieczeństwa bez wyraźnej zgody, planu ryzyka i znajomości protokołu.

## Required Architecture

Typowy węzeł:

```text
MCU / SoC CAN controller
        |
      TX/RX logic
        |
   CAN transceiver
        |
     CANH / CANL
```

Kontroler CAN nie zastępuje transceivera. Sprawdź:

- zgodność napięcia logiki kontroler–transceiver;
- zasilanie transceivera;
- pin STB/EN/SILENT;
- czy transceiver obsługuje CAN FD, jeśli jest używany;
- połączenie odniesienia masy lub izolację zgodną z projektem;
- topologię magistrali;
- bitrate i sample point wszystkich węzłów.

## Topology and Termination

Klasyczny CAN używa magistrali liniowej z terminacją na obu fizycznych końcach. Typowo są to dwa rezystory 120 Ω.

Przy wyłączonym zasilaniu i po upewnieniu się, że pomiar jest bezpieczny, rezystancja między CANH i CANL w poprawnie zakończonej magistrali z dwiema terminacjami 120 Ω wynosi około 60 Ω.

Interpretacja orientacyjna:

| Pomiar H-L | Możliwa przyczyna |
|---|---|
| około 60 Ω | dwie terminacje 120 Ω |
| około 120 Ω | prawdopodobnie jedna terminacja |
| znacznie mniej niż 60 Ω | zbyt wiele terminacji lub zwarcie |
| bardzo wysoka / open | brak terminacji lub przerwa |

Elementy aktywne i topologia mogą wpływać na pomiar. Nie traktuj go jako jedynego dowodu.

Unikaj długich odgałęzień. Dopuszczalna długość zależy od bitrate, kabla, transceiverów i jakości instalacji.

## Symptom Map

| Objaw | Najpierw sprawdź |
|---|---|
| Brak ramek | transceiver, STB/EN, bitrate, CANH/CANL, terminacja |
| Tylko błędy ACK | brak drugiego aktywnego węzła, zły bitrate, silent mode |
| Error passive / bus-off | bitrate, zakłócenia, zwarcie, brak ACK |
| Działa jeden węzeł, wiele nie | ID/protokół, terminacja, topologia, obciążenie |
| Działa przy małym bitrate | przewody, terminacja, odgałęzienia, transceiver |
| CAN Classic działa, FD nie | transceiver FD, data bitrate, sample point |
| Po restarcie nie wraca | brak auto-restart lub zła obsługa bus-off |
| Linie mają nietypowe napięcia | brak zasilania transceivera, zwarcie, standby |

## Passive Checks First

1. odłącz zasilanie;
2. sprawdź rezystancję CANH-CANL;
3. sprawdź brak zwarcia CANH-GND, CANL-GND i do zasilania;
4. potwierdź ciągłość i polaryzację H/L;
5. zidentyfikuj oba końce magistrali;
6. sprawdź zasilanie i piny trybu transceiverów.

**Kryterium:** fizyczna magistrala ma znaną topologię i terminację.

## Powered Idle Check

W typowym nieizolowanym high-speed CAN obie linie w stanie recesywnym znajdują się zwykle w pobliżu wspólnego poziomu około połowy zasilania transceivera, często około 2,5 V. W stanie dominującym CANH rośnie, a CANL maleje. Dokładne wartości zależą od transceivera i standardu.

Multimetr pokaże wartość uśrednioną, nie kształt ramek. Użyj go do wykrywania rażących nieprawidłowości, nie do oceny jakości sygnału.

## Minimal Two-Node Test

Do pełnego testu nadawania potrzebne są co najmniej dwa poprawnie skonfigurowane węzły, ponieważ nadajnik oczekuje ACK od innego węzła.

Minimalny układ:

- dwa węzły;
- dwa transceivery;
- dwie terminacje na końcach;
- krótki przewód;
- ten sam nominal bitrate;
- jeden nadajnik prostych ramek;
- jeden odbiornik/loger.

Tryb listen-only nie generuje ACK na niektórych konfiguracjach, więc samotny nadajnik może zgłaszać błędy mimo widocznych ramek na analizatorze.

## Bit Timing

Zapisz:

```text
CAN Classic / CAN FD:
nominal bitrate:
data bitrate:
sample point:
SJW:
clock source:
automatic retransmission:
listen-only / loopback / normal:
```

Dwa węzły z tym samym opisowym bitrate mogą nadal nie współpracować, jeśli rzeczywista częstotliwość zegara lub parametry bit timing są błędne.

## Linux SocketCAN

Sprawdzenie interfejsu:

```bash
ip -details -statistics link show can0
```

Przykładowa konfiguracja CAN Classic:

```bash
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 500000 restart-ms 100
sudo ip link set can0 up
ip -details -statistics link show can0
```

Jeśli `can-utils` jest już zainstalowane:

```bash
candump -L can0
```

Wysyłanie testowej ramki:

```bash
cansend can0 123#11223344
```

Wysyłaj tylko na izolowanej magistrali testowej. Nie instaluj pakietów ani nie transmituj na docelowym systemie bez potrzeby i zgody.

Zwróć uwagę na:

- `state ERROR-ACTIVE`, `ERROR-PASSIVE` lub `BUS-OFF`;
- liczniki `berr-counter tx/rx`;
- liczbę dropped packets;
- aktualne `bitrate`, `sample-point`;
- stan interfejsu `UP/DOWN`.

## CAN FD

Dla CAN FD trzeba oddzielnie ustawić nominalną i szybką fazę danych. Przykład zależny od sprzętu:

```bash
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 500000 dbitrate 2000000 fd on restart-ms 100
sudo ip link set can0 up
```

Nie używaj CAN FD z transceiverem lub kontrolerem, który go nie obsługuje.

## Error Interpretation

### ACK Errors

Najczęstsze przyczyny:

- tylko jeden aktywny węzeł;
- odbiornik w listen-only;
- niezgodny bitrate;
- odbiornik nie widzi poprawnej ramki;
- uszkodzona warstwa fizyczna.

### Bus-Off

Bus-off jest skutkiem przekroczenia liczników błędów, nie pierwotną przyczyną. Zapisz liczniki i warunki przed automatycznym restartem. Nie maskuj problemu wyłącznie przez agresywne `restart-ms`.

### Arbitration Is Not a Collision Error

Dominujący bit wygrywa nad recesywnym, a węzeł przegrywający arbitraż czeka. Normalna utrata arbitrażu nie jest awarią magistrali.

## Firmware Checks

- właściwe piny CAN TX/RX i pin mux;
- transceiver nie jest w standby/silent;
- zgodny bitrate i zegar peryferium;
- filtry nie ukrywają oczekiwanych ramek;
- obsługa error passive i bus-off;
- kolejki TX nie są przepełnione;
- ID standard 11-bit vs extended 29-bit;
- format Classic vs FD;
- BRS, DLC i długość danych są zgodne;
- protokół wyższej warstwy nie używa tego samego ID w sprzeczny sposób.

## CAN Completion Checklist

- [ ] Potwierdzono obecność i tryb transceivera.
- [ ] Zmapowano topologię i końce magistrali.
- [ ] Sprawdzono terminację przy wyłączonym zasilaniu.
- [ ] Potwierdzono nominal bitrate i, jeśli dotyczy, data bitrate.
- [ ] Zapisano stan i liczniki błędów.
- [ ] Test wykonano na izolowanym układzie co najmniej dwóch węzłów.
- [ ] Wyjaśniono źródło ACK errors lub bus-off.
- [ ] Poprawkę sprawdzono pod obciążeniem i po restarcie.

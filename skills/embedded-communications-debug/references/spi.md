# SPI Debugging Reference

## Scope

Synchroniczne połączenia SPI pomiędzy jednym kontrolerem i jednym lub wieloma urządzeniami. SPI nie ma standardowego mechanizmu ACK, dlatego brak odpowiedzi trzeba lokalizować przez konfigurację i obserwację linii.

## Signal Identity

Typowe sygnały:

```text
SCLK / SCK  - zegar generowany przez kontroler
MOSI        - kontroler -> urządzenie
MISO        - urządzenie -> kontroler
CS / SS     - wybór konkretnego urządzenia
GND         - odniesienie sygnału
```

Nazwy COPI/CIPO mogą zastępować MOSI/MISO. Ustal kierunek na podstawie roli, nie samej etykiety.

Najpierw potwierdź:

- napięcie logiki;
- wspólną masę;
- rolę controller/peripheral;
- GPIO i pin mux;
- osobny CS dla każdego urządzenia;
- czy MISO przechodzi w Hi-Z po dezaktywacji CS;
- czy urządzenie wymaga dodatkowych pinów RESET, D/C, BUSY, IRQ lub ENABLE.

## Configuration Contract

Zapisz:

```text
clock frequency:
SPI mode (0-3):
CPOL:
CPHA:
bit order:
word size:
CS polarity:
CS timing:
inter-byte delay:
duplex mode:
command/address/data framing:
```

Tryby:

| Mode | CPOL | CPHA |
|---|---:|---:|
| 0 | 0 | 0 |
| 1 | 0 | 1 |
| 2 | 1 | 0 |
| 3 | 1 | 1 |

Dokumentacja urządzenia ma pierwszeństwo nad przykładami z bibliotek.

## Symptom Map

| Objaw | Najpierw sprawdź |
|---|---|
| Same `0xFF` | MISO w stanie wysokim/Hi-Z, brak aktywnego CS, brak urządzenia |
| Same `0x00` | MISO zwarte nisko, urządzenie w resecie, błędny pin |
| Dane przesunięte o bit | CPHA/CPOL, sampling edge, jakość sygnału |
| Każdy bajt ma odwrócone bity | bit order |
| Działa tylko wolno | przewody, poziomy, drive strength, setup/hold |
| Pierwsza transakcja błędna | reset, power-up delay, CS timing, dummy bytes |
| Jedno urządzenie działa, dwa nie | konflikt CS, MISO nie przechodzi w Hi-Z |
| Zapis działa, odczyt nie | MISO, kierunek 3-wire, dummy cycles, read bit |

## Minimal Test Sequence

### Test A — Single Peripheral

Odłącz pozostałe urządzenia SPI. Pozostaw krótkie przewody i niską, obsługiwaną częstotliwość.

### Test B — Static CS Test

Sprawdź, czy CS ma właściwy stan nieaktywny i zmienia się tylko podczas transakcji do badanego urządzenia. Nie zakładaj, że aktywny poziom zawsze jest niski.

### Test C — Known Command

Użyj najprostszej udokumentowanej operacji:

- odczyt ID;
- odczyt rejestru statusu;
- zapis i odczyt rejestru testowego, jeśli bezpieczne;
- dla wyświetlacza: prosta komenda bez transferu pełnej ramki.

Zapisz dokładny strumień:

```text
TX: 9F 00 00 00
RX: FF EF 40 18
CS: aktywny przez całą komendę
mode: 0
frequency: 500 kHz
```

### Test D — Mode Matrix

Tylko gdy dokumentacja jest niejasna i test jest bezpieczny, sprawdź tryby 0-3 przy małej prędkości, nie zmieniając innych parametrów. Nie używaj tej metody do urządzeń, w których przypadkowa komenda może zmienić krytyczną konfigurację.

## Full-Duplex Behavior

Podczas każdego taktu jednocześnie wysyłany i odbierany jest bit. Bajty odebrane podczas wysyłania komendy mogą być nieistotne. Dane odpowiedzi mogą pojawić się dopiero podczas wysyłania bajtów dummy.

Nie odrzucaj całego odczytu tylko dlatego, że pierwszy bajt RX jest pusty lub `0xFF`; sprawdź dokumentację faz transakcji.

## CS Timing

Sprawdź:

- minimalny czas od aktywacji CS do pierwszego zbocza;
- czy CS musi pozostać aktywny przez komendę i dane;
- przerwę pomiędzy transakcjami;
- wymagany stan CS podczas resetu;
- czy biblioteka automatycznie przełącza CS pomiędzy bajtami.

Błąd CS często wygląda jak zły tryb SPI.

## Multiple Devices

Każde urządzenie powinno mieć osobny CS, chyba że topologia jest jawnie inna. W stanie nieaktywnym urządzenie nie może sterować MISO.

Procedura:

1. uruchom każde urządzenie osobno;
2. dodaj drugie przy nieaktywnym CS;
3. potwierdź, że pierwsze nadal działa;
4. zamień kolejność inicjalizacji;
5. sprawdź, czy biblioteki nie zmieniają globalnego trybu lub prędkości bez przywrócenia ustawień.

## 3-Wire and Half-Duplex SPI

Niektóre urządzenia współdzielą linię danych. Trzeba zmieniać kierunek GPIO w dokładnym momencie. Konflikt kierunków może uszkodzić pin lub zafałszować odczyt.

Ustal:

- kiedy kontroler zwalnia linię;
- kiedy urządzenie zaczyna odpowiadać;
- czy wymagany jest rezystor szeregowy;
- czy kontroler sprzętowy obsługuje half-duplex.

## Signal Integrity Without an Oscilloscope

Przy braku oscyloskopu:

- skróć przewody;
- prowadź GND blisko sygnałów;
- zmniejsz częstotliwość;
- testuj jedno urządzenie;
- unikaj płytki stykowej przy wyższych prędkościach;
- sprawdź zasilanie i kondensatory odsprzęgające;
- porównaj wynik po zmianie tylko jednego przewodu.

Poprawa po zmniejszeniu zegara wskazuje problem czasowy lub elektryczny, ale sama nie identyfikuje przyczyny.

## Firmware Checks

- prawidłowy kontroler SPI i piny;
- poprawny mode, bit order i word size;
- transakcja ustawia parametry przed aktywacją CS;
- CS nie jest przejmowany przez inną bibliotekę;
- DMA nie kończy się po dezaktywacji CS;
- cache i wyrównanie bufora są poprawne na platformach wymagających tego dla DMA;
- bufor TX/RX ma właściwą długość;
- parser uwzględnia dummy bytes i status bytes;
- reset i power-up delay są zgodne z dokumentacją.

## SPI Completion Checklist

- [ ] Potwierdzono poziomy logiczne i GND.
- [ ] Potwierdzono kierunki MOSI/MISO.
- [ ] Zapisano pełną konfigurację SPI.
- [ ] CS obserwowano jako osobny element diagnozy.
- [ ] Test wykonano z jednym urządzeniem i znaną komendą.
- [ ] Uwzględniono dummy bytes i pełny duplex.
- [ ] Sprawdzono działanie po dodaniu kolejnych urządzeń.
- [ ] Poprawkę zweryfikowano przy docelowej częstotliwości.

# I2C Debugging Reference

## Scope

I2C i zgodne elektrycznie warianty używane w czujnikach, ekspanderach, pamięciach i modułach embedded. SMBus może mieć dodatkowe ograniczenia czasowe i protokołowe.

## Electrical Model

SDA i SCL są zwykle liniami typu open-drain/open-collector. Stan wysoki tworzą rezystory podciągające do właściwego napięcia logiki.

Najpierw ustal:

- napięcie pull-up;
- wartości rezystorów pull-up;
- czy moduł ma własne pull-upy;
- łączną pojemność i długość magistrali;
- zgodność poziomów wszystkich urządzeń;
- wspólną masę;
- topologię i liczbę urządzeń;
- maksymalną prędkość najwolniejszego urządzenia.

Nie dodawaj kolejnych pull-upów bez sprawdzenia istniejących. Wiele modułów z własnymi pull-upami połączonych równolegle może dać zbyt małą rezystancję zastępczą.

## Address Rules

- większość dokumentacji podaje adres 7-bitowy;
- niektóre źródła podają 8-bitowy bajt adresu zawierający bit R/W;
- przed zmianą kodu ustal, którego formatu oczekuje biblioteka;
- sprawdź piny adresowe, zworki i wariant układu;
- dwa urządzenia z tym samym adresem wymagają zmiany adresu, multipleksera lub osobnej magistrali.

Przykład:

```text
7-bit address: 0x68
8-bit write byte: 0xD0
8-bit read byte:  0xD1
```

Nie zamieniaj automatycznie adresu bez potwierdzenia dokumentacji i API biblioteki.

## Symptom Map

| Objaw | Najpierw sprawdź |
|---|---|
| Brak urządzeń | zasilanie, GND, właściwe GPIO, pull-up, numer magistrali |
| Wszystkie adresy odpowiadają | SDA zwarta lub źle działające skanowanie |
| NACK na adres | zły adres, urządzenie w resecie, zła sekwencja startowa |
| NACK w trakcie danych | format komendy, czas przetwarzania, write protect |
| SCL lub SDA stale nisko | zwarcie, urządzenie trzyma linię, brak resetu |
| Działa tylko wolno | rise time, pojemność, słabe pull-upy, level shifter |
| Zawiesza się po błędzie | brak timeoutu lub procedury bus recovery |
| Działa osobno, nie razem | konflikt adresów, suma pull-upów, obciążenie magistrali |

## Minimal Test Sequence

### Test A — Power-Off Resistance and Continuity

Przy odłączonym zasilaniu:

- sprawdź zwarcie SDA-GND, SCL-GND, SDA-SCL;
- sprawdź ciągłość przewodów;
- zidentyfikuj, do jakiej szyny podłączone są pull-upy.

Nie wyciągaj wniosków o dokładnej rezystancji pull-up bez uwzględnienia pozostałych elementów układu.

### Test B — Idle Voltage

Po zasileniu i bez aktywnej transmisji SDA i SCL powinny osiągać poziom wysoki zgodny z magistralą. Linia stale niska wskazuje zwarcie, błędny pin lub urządzenie utrzymujące magistralę.

### Test C — Single Device

Odłącz wszystkie urządzenia poza jednym. Użyj niskiej, obsługiwanej prędkości, np. 100 kHz, jeśli dokumentacja ją dopuszcza.

### Test D — Known Register

Zamiast pełnego sterownika wykonaj minimalną operację opisaną w dokumentacji, np. odczyt rejestru identyfikacyjnego. Zapisz:

```text
adres:
rejestr:
oczekiwane bajty:
rzeczywiste bajty:
status ACK/NACK:
```

## Linux I2C

Najpierw ustal dostępne magistrale:

```bash
ls -l /dev/i2c-* 2>/dev/null
```

Jeśli `i2c-tools` jest już zainstalowane:

```bash
i2cdetect -l
i2cdetect -y 1
```

Jeśli `i2c-tools` nie jest dostępne i nie chcesz instalować pakietu, skanowanie można wykonać przez Python (`smbus2`) albo przez sysfs:

```bash
python3 -c "from smbus2 import SMBus; print([hex(a) for a in sorted(SMBus(1).scan())])"
```

Jeśli nawet `smbus2` nie jest dostępne, użyj uproszczonego skanu po sysfs (wymaga uprawnień):

```bash
for addr in $(seq 0x03 0x77); do
  i2cset -f -y 1 "$addr" 0x00 2>/dev/null && echo "ACK $addr"
done
```

Skanowanie nie jest całkowicie neutralne dla każdego urządzenia. Nie skanuj aktywnego systemu sterującego ani urządzeń, których dokumentacja ostrzega przed nieznanymi komendami. Preferuj odczyt znanego rejestru.

Dostęp do `/dev/i2c-*` może wymagać odpowiedniej grupy lub uprawnień. Nie rozwiązuj tego przez stałe uruchamianie całej aplikacji jako root; ustal właściwe uprawnienia urządzenia.

## Pull-Up Diagnosis

Nie istnieje jedna poprawna wartość dla każdego układu. Dobór zależy od:

- napięcia;
- częstotliwości;
- pojemności magistrali;
- prądu sink urządzeń;
- level shifterów;
- liczby równoległych rezystorów.

Typowe moduły używają wartości rzędu kilku kiloohmów, ale nie traktuj tego jako zamiennika obliczeń lub dokumentacji.

Objawy zbyt słabego podciągania:

- wolne zbocze narastające;
- błędy przy większej prędkości;
- poprawa po skróceniu przewodów.

Objawy zbyt mocnego podciągania:

- urządzenie nie potrafi ściągnąć linii wystarczająco nisko;
- nadmierny prąd;
- pogorszenie po dołączeniu kolejnych modułów z pull-upami.

## Clock Stretching

Niektóre urządzenia utrzymują SCL w stanie niskim, aby opóźnić mastera. Sprawdź, czy kontroler, biblioteka i wybrany pin mux obsługują clock stretching w wymagany sposób.

Nie traktuj każdej długiej fazy niskiej jako zwarcia, zanim nie sprawdzisz dokumentacji i czasu trwania.

## Bus Recovery

Gdy slave pozostawi SDA nisko po przerwanym transferze:

1. zatrzymaj kontroler I2C;
2. przełącz SCL na GPIO open-drain lub bezpieczny odpowiednik;
3. wygeneruj do dziewięciu impulsów zegara, obserwując SDA;
4. wygeneruj warunek STOP, jeśli sprzęt i dokumentacja na to pozwalają;
5. ponownie zainicjalizuj kontroler;
6. jeśli linia nadal jest niska, zresetuj lub odłącz zasilanie winnego urządzenia.

Nie stosuj tej procedury bez potwierdzenia, że piny i poziomy są bezpieczne.

## Firmware Checks

- poprawne GPIO SDA/SCL i alternatywna funkcja;
- poprawny numer kontrolera;
- właściwy adres 7-bitowy;
- opóźnienie po włączeniu zasilania;
- wymagany repeated START;
- kolejność bajtów rejestru;
- długość adresu rejestru 8/16 bit;
- timeout transakcji;
- obsługa NACK i ponownej inicjalizacji;
- mutex, jeśli kilka zadań używa tej samej magistrali.

## I2C Completion Checklist

- [ ] Zidentyfikowano napięcie pull-up i poziomy urządzeń.
- [ ] Sprawdzono, czy pull-upy istnieją i nie są nadmiernie równoległe.
- [ ] Potwierdzono GPIO i numer magistrali.
- [ ] Potwierdzono format adresu 7-bit/8-bit.
- [ ] Test wykonano z jednym urządzeniem.
- [ ] Użyto znanego rejestru zamiast przypadkowego skanowania.
- [ ] Sprawdzono timeout i bus recovery.
- [ ] Poprawkę sprawdzono z pełnym zestawem urządzeń.

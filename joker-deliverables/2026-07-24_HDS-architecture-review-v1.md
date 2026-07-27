# HDS — krytyczny przegląd Master Project Specification v1.0

**Data:** 2026-07-24  
**Status:** Review / bez implementacji  
**Źródło:** `GAJA.txt` (MD5 `bdaae918141c6497fad6e224aa2857c7`)  
**Autor przeglądu:** Gaja — Chief AI Engineer

## 1. TL;DR

HDS ma sens i trafia w realną potrzebę: cienki klient dotykowy, niezależny od Hermesa, działający lokalnie bez przeglądarki. Kierunek technologiczny — FastAPI + REST/SSE + Pygame — jest rozsądny dla Raspberry Pi 3A+ i 800×480. Jednak dokument v1.0 jest **konspektem architektury, nie specyfikacją gotową do implementacji**: 9450 B, 26 sekcji, około 364 B/sekcję, 0 tabel kontraktów, 0 właściwych diagramów i 0 ADR-ów. Największe braki to: brak uniwersalnego modelu danych, brak wersjonowanego API, niejasna granica pluginów, brak modelu bezpieczeństwa oraz brak decyzji, co zrobić z istniejącym `hermes-panel`, który realizuje już znaczną część HDS.

**Ocena:** **6.3/10 jako wizja**, **2.8/10 jako specyfikacja implementacyjna**.  
**Rekomendacja:** nie tworzyć jeszcze kodu ani nowego repo. Najpierw podjąć 5–7 decyzji ADR i opisać kontrakt HDS v1.

---

## 2. Co jest dobre — zachować

1. **Twardy podział server/client.** GUI nie zna wewnętrznego API Hermesa; to poprawna granica antykorupcyjna.
2. **Renderowanie lokalne.** Utrata sieci nie może wyłączyć ekranu — dobry wymóg operacyjny.
3. **Lekki stack.** Pygame/SDL2 jest właściwszy niż Chromium/Electron dla Pi 3A+ z 512 MB RAM.
4. **REST + SSE.** Dobra para dla snapshotu stanu i jednokierunkowych zdarzeń.
5. **Offline mode.** Ostatni stan + jawne oznaczenie nieaktualności to właściwa semantyka UX.
6. **Screen Manager.** Centralizacja nawigacji i lifecycle ekranów zapobiega zależnościom ekran-ekran.
7. **Iteracyjna realizacja.** Projekt przed kodem, małe testowalne etapy i akceptacja po każdym etapie są prawidłowe.
8. **Ręczne aktualizacje.** Na pierwszym etapie Git + jawne wdrożenie jest prostsze i bezpieczniejsze niż OTA.

---

## 3. Najważniejsze odkrycie: HDS nie startuje od zera

Na NUC istnieje już `/home/gaja/projects/hermes-panel`, który zawiera m.in.:

- backend FastAPI,
- REST `/api/status`, `/api/system`, `/api/models`, `/api/profiles`,
- SSE `/api/events`,
- SQLite,
- autoryzację `X-API-Key`,
- klienta Pygame 800×480,
- reconnect z exponential backoff,
- Dashboard i Face,
- obsługę ADS7846 przez `evdev`,
- testy backendu,
- usługę systemd.

To nie jest argument, żeby bezrefleksyjnie przemianować stare repo. Obecny kod jest silnie związany z Hermesem (`HermesClient`, collectory Hermesa, endpointy modeli/profili) i nie spełnia jeszcze uniwersalnego kontraktu HDS.

**Decyzja blokująca ADR-0001:**

- **A — ewolucja:** `hermes-panel` staje się bazą HDS i jest refaktoryzowany etapami;
- **B — ekstrakcja:** z `hermes-panel` wydzielamy neutralny rdzeń HDS, a integrację Hermes przenosimy do adaptera;
- **C — greenfield:** HDS powstaje od nowa, a `hermes-panel` służy wyłącznie jako spike/reference.

**Moja rekomendacja: B — ekstrakcja.** Zachowujemy działający kod i testy, ale nie przenosimy błędnych nazw ani sprzężenia z Hermesem do publicznego kontraktu.

---

## 4. Wady P0 — przed utworzeniem kodu

### P0.1 — Brak uniwersalnego modelu danych

**Problem:** Dokument mówi, że HDS ma obsługiwać Hermes, ROS 2, medycynę, IoT i Home Assistant, ale jedyny opis danych to lista pól dashboardu Hermesa.

**Ryzyko:** API stanie się zbiorem endpointów `/hermes/...`, `/ros2/...`, `/medical/...`; GUI zacznie rozpoznawać źródła i uniwersalność zniknie.

**Propozycja:** zdefiniować neutralne prymitywy prezentacyjne:

- `SystemStatus` — health, connectivity, severity, timestamp;
- `Metric` — id, label, value, unit, range, timestamp, freshness;
- `Notification` — severity, title, body, source, created_at, expiry;
- `ViewModel` — screen id, sections/widgets, revision;
- `DisplayEvent` — id, type, source, timestamp, payload;
- `Capability` — funkcje dostępne dla danego klienta/pluginu.

Hermes, ROS 2 i pozostałe systemy mają mapować swoje dane na ten kontrakt przez adaptery.

### P0.2 — Niejasna architektura pluginów

**Problem:** „Każdy plugin implementuje własne źródło danych”, ale pluginy wymienione są obok GUI, backendu i wspólnego katalogu. Nie wiadomo, gdzie działają, jaki mają lifecycle i czy wolno im renderować.

**Decyzja rekomendowana:** w v1 plugin = **server-side data adapter**, nie rozszerzenie GUI.

```text
Source system → Adapter plugin → HDS domain model → REST/SSE → Client
```

Frontend otrzymuje neutralne modele. Rozszerzenia ekranów i rendererów, jeśli kiedyś będą potrzebne, powinny być osobnym mechanizmem (`frontend extensions`), a nie tym samym plugin API.

### P0.3 — Brak wersjonowanego kontraktu API

**Problem:** Brak endpointów, schematów JSON, kodów błędów, polityki kompatybilności i semantyki SSE.

**Minimum:**

- prefiks `/api/v1`;
- OpenAPI jako kontrakt;
- modele Pydantic współdzielone semantycznie, ale bez importowania kodu backendu przez klienta;
- `schema_version` w snapshotach;
- SSE: `id`, `event`, `data`, heartbeat, `Last-Event-ID` lub jawna zasada „po reconnect pobierz snapshot”;
- identyczny format błędów;
- zegar UTC ISO-8601 i `generated_at`/`valid_until`.

### P0.4 — Brak decyzji o relacji HDS Server ↔ Hermes

**Problem:** Diagram pokazuje `Hermes Agent → HDS Display Server`, ale jednocześnie HDS ma być niezależny. Nie wiadomo, czy server:

- odpytuje Hermesa,
- czyta jego pliki,
- subskrybuje eventy,
- czy Hermes pushuje dane,
- uruchamia się na NUC czy może również na innym hoście.

**Propozycja:** HDS Server nie zależy od Hermesa. Zależy od abstrakcji `DataSourceAdapter`. `HermesAdapter` jest pierwszym adapterem i jedynym elementem znającym Hermesa.

### P0.5 — Brak threat modelu

**Problem:** Dotykowy klient i przyszłe „Sterowanie Hermes” zmieniają system z read-only w control plane. Brak modelu zaufania, uwierzytelniania, autoryzacji i segmentacji sieci.

**Minimum dla v1:**

- dashboard read-only;
- server nasłuchuje tylko w zaufanym LAN/VLAN;
- klucz per urządzenie, nie wspólny globalny sekret;
- sekret poza repo i logami;
- rate limiting dla reconnect;
- sterowanie jako osobny capability + endpointy command, nigdy przez endpoint statusu;
- audyt komend przed Etapem 8.

TLS można odłożyć w kontrolowanym LAN, ale musi to być jawna decyzja ADR z konsekwencjami, nie przypadek.

### P0.6 — Specyfikacja nie rozstrzyga losu `hermes-panel`

Bez tej decyzji grożą dwa równoległe projekty robiące to samo, rozjazd nazw, testów i usług systemd. ADR-0001 powinien poprzedzić utworzenie repo HDS.

---

## 5. Wady P1 — przed pierwszym prototypem

### P1.1 — „SQLite od początku” nie ma uzasadnienia

Dla bieżącego snapshotu i cache klienta wystarczy atomowy plik JSON lub lekka warstwa repository. SQLite ma sens dla historii metryk, audit logu i durable notifications, ale nie powinno przenikać domeny.

**Rekomendacja:** interfejs `StateStore`; implementacja `MemoryStore` w testach, `SQLiteStore` tylko dla danych wymagających trwałości.

### P1.2 — Offline mode jest opisany jako zachowanie, nie kontrakt

Brakuje:

- gdzie i jak długo przechowywany jest cache;
- czy cache przeżywa restart klienta;
- progu `stale`;
- różnicy między `offline`, `server unavailable`, `source unavailable` i `stale source`;
- zachowania przy niezgodnej wersji schematu.

**Rekomendacja:** jawny `ConnectionState`: `BOOTSTRAPPING`, `ONLINE`, `DEGRADED`, `OFFLINE`, `INCOMPATIBLE`; każdy snapshot ma czas i TTL.

### P1.3 — Brak resource budget dla Pi 3A+

Pi 3A+ ma ograniczone CPU i 512 MB RAM. „Animacje”, pluginy, fonty i logi mogą zabić stabilność, co wcześniejszy `hermes-panel` już praktycznie ujawnił.

**Budżety do ustalenia:**

- RSS klienta;
- czas startu do pierwszej klatki;
- FPS target (30 domyślnie, 60 opcjonalnie);
- maksymalny czas renderowania klatki;
- maksymalny rozmiar cache i logów;
- zachowanie przy OOM i restart policy systemd.

### P1.4 — Wayland/labwc a „bez pulpitu” wymaga precyzji

`labwc` jest kompozytorem Wayland, więc jakaś sesja graficzna istnieje. Poprawny wymóg brzmi: **dedykowana sesja kioskowa uruchamiająca tylko HDS Client**, bez paneli, menedżera plików i innych aplikacji użytkownika.

### P1.5 — Screen Manager wymaga lifecycle

Samo „każdy ekran w osobnym pliku” nie wystarczy. Potrzebne operacje:

- `on_enter(context)`;
- `handle_event(event)`;
- `update(dt, state)`;
- `render(surface)`;
- `on_exit()`.

Preferowana jest kompozycja i protokół/interfejs, bez ciężkiej hierarchii klas.

### P1.6 — Brak separacji domeny, transportu i renderowania

Jeśli modele Pydantic/FastAPI będą importowane bezpośrednio do Pygame, „common/” stanie się sprzężeniem wdrożeniowym.

**Rekomendacja:** trzy warstwy:

1. `domain` — neutralne modele i porty;
2. `adapters` — Hermes, ROS 2, storage, HTTP/SSE;
3. `presentation` — ViewModels, screens, widgets, themes, animations.

### P1.7 — Etapy są niepełne i niemierzalne

Etap 5 jest pusty. Etapy nie mają Definition of Done, testów akceptacyjnych ani granic zakresu. Nie wiadomo również, kiedy powstaje neutralny adapter/plugin contract.

---

## 6. Wady P2/P3

### P2 — przed stabilizacją v1

- Logi jako cztery osobne pliki zwiększają komplikację. Lepszy jeden strumień strukturalny z loggerami/kategoriami i rotacją journald/logrotate.
- `config.json` nie ma schematu, wersji, migracji ani walidacji.
- „jasność” może wymagać sterowania podświetleniem sprzętowym; HDMI nie gwarantuje tej funkcji.
- Brak accessibility: rozmiary dotyku, kontrast, tryb nocny, redukcja animacji.
- Brak i18n, mimo potencjalnych wdrożeń medycznych.
- Brak synchronizacji czasu NUC/RPi i definicji zachowania przy złym zegarze.
- Brak observability: liczba reconnectów, drop events, frame time, cache age.

### P3 — później

- mechanizm paczek theme/assets;
- screenshot tests i golden images;
- simulator desktopowy klienta 800×480;
- multi-display discovery;
- WebSocket dopiero, gdy pojawi się realna potrzeba komunikacji dwukierunkowej.

---

## 7. Proponowana architektura docelowa

```text
Hermes / ROS 2 / IoT / Medical system
              │
              ▼
      server-side adapters
              │
              ▼
       HDS Domain Model
              │
      Application Services
       ┌──────┴──────┐
       ▼             ▼
 StateStore       EventBus
       │             │
       └──────┬──────┘
              ▼
       API v1: REST + SSE
              │
              ▼
      HDS Client transport
              │
   Cache + freshness + reconnect
              │
              ▼
 ViewModel → Screen Manager → Widgets/Face/Theme → SDL/Pygame
```

**Zasada:** źródło danych nie zna ekranu, ekran nie zna źródła, transport nie zna widgetów.

---

## 8. Lepsza struktura repo

Rekomenduję **jedno repo (monorepo)** dla HDS v1. Server, client i kontrakt API będą rozwijane wspólnie i muszą przechodzić wspólne testy kompatybilności. Rozdzielanie repo teraz zwiększyłoby koszt wersjonowania bez korzyści.

```text
HDS/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── pyproject.toml
├── config/
│   ├── server.example.toml
│   └── client.example.toml
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── adr/
│   ├── operations/
│   └── testing/
├── src/hds/
│   ├── domain/
│   │   ├── models.py
│   │   ├── events.py
│   │   └── ports.py
│   ├── server/
│   │   ├── application/
│   │   ├── api/v1/
│   │   ├── adapters/
│   │   │   ├── hermes/
│   │   │   ├── ros2/
│   │   │   └── system/
│   │   └── storage/
│   ├── client/
│   │   ├── transport/
│   │   ├── state/
│   │   ├── screens/
│   │   ├── widgets/
│   │   ├── input/
│   │   └── runtime/
│   └── face/
│       ├── engine.py
│       ├── animation.py
│       └── themes.py
├── assets/
│   ├── fonts/
│   ├── icons/
│   ├── animations/
│   ├── sounds/
│   └── themes/
├── packaging/
│   ├── systemd/
│   └── rpi/
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   ├── visual/
│   └── hardware/
└── tools/
    ├── simulator/
    └── diagnostics/
```

Nie twórzmy pustych katalogów dla hipotetycznych pluginów. Pierwszy realny adapter to `hermes`; kolejne katalogi powstaną dopiero z implementacją.

---

## 9. Proponowane API v1 — zakres projektu, nie finalna akceptacja

### REST

| Endpoint | Cel |
|---|---|
| `GET /healthz` | liveness servera, bez danych domenowych |
| `GET /api/v1/capabilities` | wersje i funkcje servera |
| `GET /api/v1/snapshot` | pełny neutralny stan do startu/reconnect |
| `GET /api/v1/notifications` | aktywne powiadomienia |
| `GET /api/v1/screens` | dostępne deklaracje ekranów, jeśli będą server-driven |
| `GET /api/v1/events` | SSE |

### SSE

Typy minimalne:

- `snapshot.updated`;
- `metric.updated`;
- `status.changed`;
- `notification.created`;
- `notification.dismissed`;
- `heartbeat`.

Po reconnect klient zawsze pobiera `/snapshot`; SSE służy do delt. To prostsze i bardziej niezawodne niż pełne odtwarzanie historii eventów w v1.

### Wstępny envelope

```json
{
  "schema_version": "1.0",
  "event_id": "01J...",
  "type": "metric.updated",
  "source": "hermes",
  "generated_at": "2026-07-24T12:00:00Z",
  "payload": {}
}
```

---

## 10. Proponowane interfejsy/klasy

To projekt granic, nie kompletna lista klas:

- `DataSourceAdapter` — start/stop/snapshot/health;
- `StateStore` — load/save/history według jawnych potrzeb;
- `EventPublisher` — publish/subscribe wewnątrz servera;
- `SnapshotService` — składa dane adapterów do modelu HDS;
- `ApiClient` — REST snapshot/capabilities;
- `EventStreamClient` — SSE/reconnect;
- `ConnectionManager` — maszyna stanów połączenia;
- `ClientCache` — ostatni poprawny snapshot + metadata;
- `ScreenManager` — lifecycle i routing;
- `Screen` Protocol — enter/event/update/render/exit;
- `Widget` Protocol — measure/update/render;
- `FaceEngine` — niezależny od źródła danych, sterowany semantycznym `mood/state`.

**Nie tworzyć** `Manager` dla każdej rzeczy. Nazwa `Manager` jest dopuszczalna tylko tam, gdzie faktycznie zarządzany jest lifecycle wielu obiektów.

---

## 11. Standard kodowania

- Python 3.11 jako bazowa wersja v1; wsparcie 3.13 dopiero po CI/hardware test.
- `pyproject.toml`, `src/` layout, jeden pakiet `hds`.
- Typowanie obowiązkowe na granicach publicznych; `mypy`/`pyright` bez błędów dla domeny i API.
- `ruff format` + `ruff check`.
- Pydantic dla wire models; dataclasses/protokoły dla logiki wewnętrznej.
- Maksymalnie jedna odpowiedzialność modułu, ale bez sztucznego limitu linii.
- Brak globalnego mutable state.
- Dependency injection przez konstruktory/fabryki, nie framework DI w całej aplikacji.
- Logi strukturalne; zakaz logowania sekretów i pełnych danych medycznych.
- Publiczne kontrakty i komentarze kodu po angielsku; dokumentacja użytkowa może być po polsku.

---

## 12. Wersjonowanie

- Projekt: Semantic Versioning (`0.x` podczas projektowania, `1.0.0` po stabilizacji kontraktu).
- API: prefiks major `/api/v1`; zmiany addytywne w ramach v1.
- Schema: `schema_version` w payloadzie.
- ADR-y: monotonicznie `0001`, `0002`, ... ze stanami Proposed/Accepted/Rejected/Deferred/Superseded.
- Commity: `[init]`, `[adr]`, `[add]`, `[fix]`, `[doc]`, `[refactor]`, `[test]`.
- Release tag: `v0.1.0`, `v0.2.0`, itd.
- Każda zmiana kontraktu wymaga contract test i wpisu w CHANGELOG.

---

## 13. Strategia testów

### Unit

- modele domenowe i walidacja;
- freshness/TTL;
- reconnect/backoff;
- Screen Manager lifecycle;
- mapper Hermes → HDS;
- Face Engine state transitions.

### Contract

- OpenAPI snapshot;
- server payload ↔ client decoder;
- zgodność `schema_version`;
- event envelope i błędy.

### Integration

- FastAPI + adapter fake + SQLite/temp store;
- przerwanie SSE i reconnect;
- restart servera;
- cache po restarcie klienta;
- niezgodna wersja API.

### Visual/headless

- SDL dummy driver;
- golden screenshots 800×480;
- hit zones i minimalne rozmiary dotyku;
- stale/offline/degraded states.

### Hardware-in-the-loop

- boot RPi → pierwsza klatka;
- 8 h soak test;
- odłączenie Wi-Fi/servera;
- dotyk ADS7846;
- pamięć/CPU/FPS;
- restart po crashu;
- start po zaniku zasilania.

### Kryteria jakości v1

- zero crash przez 8 h;
- klient działa po utracie sieci i oznacza stale data;
- reconnect bez restartu aplikacji;
- snapshot po reconnect przywraca spójny stan;
- ustalone budżety RAM/startup/frame time spełnione na Pi 3A+;
- wszystkie testy unit/contract/integration przechodzą.

---

## 14. Poprawiona roadmapa

### Etap 0 — decyzje architektoniczne

**MINIMUM:**

1. ADR-0001: los `hermes-panel` i strategia ekstrakcji;
2. ADR-0002: neutralny model domenowy;
3. ADR-0003: granica pluginów/adapters;
4. ADR-0004: API v1 + SSE/reconnect;
5. ADR-0005: security model v1;
6. ADR-0006: runtime Pi/kiosk/resource budgets;
7. Architecture v1.1 zatwierdzona przez Jokera.

### Etap 1 — repo i kontrakty

Repo, dokumentacja, modele domenowe, OpenAPI draft, fake adapter, testy contract. Bez prawdziwego Hermesa i bez GUI produkcyjnego.

### Etap 2 — pionowy walking skeleton

Fake adapter → server → REST snapshot/SSE → minimalny client → jeden statyczny ekran. Celem jest dowód całego przepływu.

### Etap 3 — odporność klienta

Reconnect, persistent cache, stale state, network state machine, testy awarii.

### Etap 4 — Dashboard + HermesAdapter

Prawdziwe dane Hermesa mapowane do neutralnego modelu; Dashboard nie importuje niczego z Hermesa.

### Etap 5 — kiosk i hardware validation

systemd, labwc kiosk session, ADS7846, log rotation, soak test i resource budgets na Pi 3A+.

### Etap 6 — Screen Manager i komponenty prezentacyjne

Dashboard jako pierwszy pełny ekran; Boot/Diagnostics dopiero według potrzeb operacyjnych.

### Etap 7 — Face Engine skeleton

Kontrakt stanów/mood, jedna minimalna animacja, testy timingowe. Bez rozbudowanych theme packów.

### Etap 8 — drugi adapter jako test uniwersalności

Mały adapter `system` albo `weather`. Dopiero drugi niezależny source pokaże, czy abstrakcja jest naprawdę uniwersalna.

### Etap 9 — sterowanie

Osobny threat model, capability model, authorization i audit log. Nie rozszerzać read-only API przypadkowymi POST-ami.

### Etap 10 — Token Engine

Dopiero po stabilizacji modelu danych i rzeczywistej potrzebie.

---

## 15. Pytania blokujące

1. Czy HDS ma zastąpić obecny `hermes-panel`, czy oba projekty mają istnieć równolegle?
2. Czy HDS Server w v1 działa wyłącznie na NUC, czy wymagamy przenośności także na Pi/Jetson/inny Linux?
3. Czy wszystkie źródła danych są zaufane i lokalne, czy przewidujesz dostęp spoza LAN?
4. Czy przyszłe systemy medyczne oznaczają wyłącznie prezentację niesensytywnych statusów, czy także dane pacjentów? To zmienia bezpieczeństwo i zgodność radykalnie.
5. Czy klient ma mieć układ ekranów zakodowany lokalnie, czy server ma przesyłać deklaratywny layout? Rekomenduję lokalny layout w v1.
6. Jaki ma być domyślny ekran po starcie: Dashboard czy Face?
7. Czy obecna karta/system RPi będzie odtwarzana i dalej używana, czy przygotujemy świeży image? To wpływa na plan Etapu 5, nie na model domenowy.

---

## 16. Rekomendowane ADR-y

1. **ADR-0001 — Existing hermes-panel migration strategy**
2. **ADR-0002 — HDS domain model and data ownership**
3. **ADR-0003 — Server-side adapter plugin boundary**
4. **ADR-0004 — REST/SSE API v1 and reconnect semantics**
5. **ADR-0005 — Authentication and network trust model**
6. **ADR-0006 — Raspberry Pi kiosk runtime and resource budgets**
7. **ADR-0007 — Persistence and offline cache strategy**
8. **ADR-0008 — Monorepo and release/versioning strategy**
9. **ADR-0009 — Local screens versus server-driven UI**
10. **ADR-0010 — Observability and log retention**

Pierwsze sześć blokuje rozpoczęcie właściwego kodu. ADR-0007–0010 mogą być rozstrzygane przed odpowiednimi etapami.

---

## 17. Wniosek końcowy

Projekt HDS jest wart realizacji. Najmocniejszą decyzją jest odcięcie GUI od Hermesa; najsłabszym miejscem jest brak neutralnego kontraktu, który faktycznie to odcięcie egzekwuje. Nie potrzebujemy teraz więcej katalogów ani więcej klas — potrzebujemy kilku precyzyjnych decyzji i jednego pionowego walking skeleton.

**Rekomendowana kolejność:**

1. rozstrzygnąć ADR-0001: ekstrakcja z `hermes-panel`;
2. zatwierdzić model domenowy i plugin boundary;
3. zatwierdzić API/reconnect/security;
4. dopiero wtedy utworzyć repo HDS i dokumentację Etapu 1;
5. kod zacząć od fake adapter → snapshot → minimalny ekran.

**Pewność: ★★★★☆** — wysoka co do diagnozy architektonicznej i overlapu z istniejącym kodem, potwierdzonego inspekcją plików. Jedna gwiazdka mniej, ponieważ stan fizycznego RPi i ostateczny zakres medyczny wymagają decyzji Jokera.

---
name: using-chm
description: How to use and configure the Context Health Manager (CHM) plugin in Hermes Agent. Load when the user asks about
  context window monitoring, token counts, automatic thread summarization, or the CHM dashboard.
status: accepted
type: skill
id: skill-using-chm
title: Using CHM (Context Health Manager)
owner: gaja
created_at: '2026-07-24'
updated_at: '2026-07-28'
review_due: '2027-01-23'
version: 1.0.0
heos_standard_version: '1.2'
tags:
- cross-cutting
- observability
- hermes-plugin
related:
- adr-005
- skill-using-heos
- skill-nightly-evolution
quality_schema: pass
quality_technical: pass
quality_operational: unmeasured
# NOTE: skill_audit.py oznacza ten plik jako 'runtime' (bo opisuje plugin + ma data_root ~/.hermes),
# więc NIE pojawia się w standardowym audycie HEOS. quality_* ustawione manual review 2026-07-28.
---

# Using CHM (Context Health Manager)

## Cel

CHM (Context Health Manager) to plugin profilu Hermesa, który **obserwuje** rozmiar kontekstu każdej sesji i raportuje:
- Liczbę tokenów bieżącego promptu i kontekstu rozmowy
- Procent wykorzystania okna kontekstowego
- Status zdrowia: GOOD / WARNING / HIGH / CRITICAL
- Po przekroczeniu 700k tokenów — automatycznie generuje streszczenie projektu i proponuje nowy wątek
- Udostępnia dane przez REST API + WebSocket pod `127.0.0.1:8770` (domyślnie)

**CHM jest read-only** — nigdy nie modyfikuje promptu, wiadomości ani cache modelu. Każda warstwa Hermes działa dokładnie tak samo z CHM lub bez niego.

## Zakres

**W zakresie:**
- Monitoring tokenów dla każdego wywołania modelu
- Progi zdrowia kontekstu (50% / 70% / 90% domyślnie)
- Generowanie artefaktu streszczenia przy >700k tokenów
- Sugestia rozpoczęcia nowego wątku
- Dashboard (REST + WebSocket)

**Poza zakresem:**
- Kompresja kontekstu (to robi istniejący `ContextCompressor` w hermes-agent, nie CHM)
- Modyfikacja promptu
- Routing wiadomości Discord
- Licznik kosztów (planowane w przyszłej wersji)

## Kiedy używać

- ✅ Użytkownik pyta o "ile tokenów zużyliśmy" lub "ile zostało"
- ✅ Wątek zbliża się do limitu kontekstu i trzeba zaplanować kompresję lub nowy wątek
- ✅ Użytkownik chce wystawić dashboard dla ekranu HDMI / GUI
- ✅ Po deployment CHM — żeby zweryfikować konfigurację

## Kiedy nie używać

- ❌ Zwykłe pytanie o rozmowę — CHM to observability, nie feature
- ❌ Kompresja kontekstu — to inny mechanizm (ContextCompressor)
- ❌ Profile `gaja-it` / `gaja-med` — CHM jest w profilu `gaja` (granice profili: ADR-005)

## Workflow

### 1. Szybki start: weryfikacja czy CHM działa

```bash
# Test importu i stanu
python3 - <<'EOF'
import sys
sys.path.insert(0, '/home/gaja/.hermes/profiles/gaja/plugins/chm/src')
from chm import init_chm
from chm.config import load_chm_config
cfg = load_chm_config()
print('enabled:', cfg.enabled)
print('context_limit:', cfg.context_limit)
print('summary_threshold:', cfg.summary_threshold)
print('dashboard:', f'{cfg.dashboard_host}:{cfg.dashboard_port}')
EOF
```

### 2. Dashboard — uruchomienie

```bash
# Terminal 1: uruchom dashboard
python3 -c "
import sys
sys.path.insert(0, '/home/gaja/.hermes/profiles/gaja/plugins/chm/src')
from chm.config import load_chm_config
from chm.dashboard import run_dashboard
run_dashboard(load_chm_config())
"

# Terminal 2: odpytywanie
curl -s http://127.0.0.1:8770/api/chm/health | python3 -m json.tool
curl -s http://127.0.0.1:8770/api/chm/summary | python3 -m json.tool
```

Lub w przeglądarce: <http://127.0.0.1:8770/>

### 3. WebSocket — subskrypcja real-time

```javascript
const ws = new WebSocket("ws://127.0.0.1:8770/api/chm/ws");
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === "chm.health") {
    // msg.data = { context_tokens, usage_percent, health, ... }
  }
};
```

### 4. Konfiguracja (`~/.hermes/profiles/gaja/config.yaml`)

```yaml
chm:
  enabled: true
  context_limit: 1_000_000        # pełne okno modelu
  warning_threshold: 500_000      # = 50% domyślnie
  summary_threshold: 700_000      # = 70% domyślnie, trigger streszczenia
  critical_threshold: 900_000     # = 90% domyślnie
  health:
    warning_pct: 50
    high_pct: 70
    critical_pct: 90
  dashboard:
    host: 127.0.0.1
    port: 8770
```

Po edycji configu — restart gateway (`hermes gateway restart`).

### 5. Artefakt streszczenia

Gdy `context_tokens >= 700_000`, CHM automatycznie:
1. Wywołuje callback (domyślnie `summary.default_summary_callback`).
2. Zapisuje markdown do `~/.hermes/profiles/gaja/plugins/chm/artifacts/<thread>-<date>-summary.md`.
3. Ustawia `recommended_new_thread = true` w state.
4. Przy następnym `observe()` zwraca snapshot z `summary_path` i `recommended_new_thread: true`.
5. Hook w `conversation_loop.py` wyświetla banner z ikoną 🔴 (CRITICAL).

Streszczenie zawiera 9 sekcji z briefu: cele, decyzje, architektura, standardy, TODO, otwarte problemy, ważne pliki, ważne prompty, decyzje do zachowania.

## Przykłady

### Przykład 1: Sprawdź ile kontekstu zostało

```bash
curl -s http://127.0.0.1:8770/api/chm/health | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Context: {d[\"context_tokens\"]:,} / {d[\"context_limit\"]:,} ({d[\"usage_percent\"]:.1f}%)')
print(f'Health: {d[\"health\"]}')
print(f'Summary: {d[\"summary_path\"] or \"(none yet)\"}')"
```

### Przykład 2: Dashboard dla ekranu HDMI

Uruchom CHM dashboard na porcie 8770, a na Raspberry Pi (patrz skill `pi-touchscreen-panel-bringup`) otwórz przeglądarkę w trybie kiosk na `http://<hermes-host>:8770/`. Zbuduj prosty HTML który odpytuje `/api/chm/health` co sekundę.

### Przykład 3: Programowe użycie w skrypcie

```python
import sys
sys.path.insert(0, '/home/gaja/.hermes/profiles/gaja/plugins/chm/src')
from chm import init_chm
from chm.config import load_chm_config

# Symulacja agenta
class MockAgent:
    context_compressor = type('C', (), {
        'context_length': 1_000_000,
        'last_prompt_tokens': 0,
    })()
    model = 'MiniMax-M3'
    tools = []
    system_prompt = 'You are Hermes.'
    messages = [{'role': 'user', 'content': 'Hello'}]

mgr = init_chm(MockAgent(), thread_id='my-script', config=load_chm_config())
snap = mgr.observe(MockAgent.messages)
print(f'Health: {snap.health} | Usage: {snap.usage_percent:.1f}%')
```

## Typowe błędy

1. **CHM pokazuje 0% zawsze** — sprawdź czy `agent.context_compressor.context_length` jest ustawione. Jeśli nie, to CHM używa default z `chm.context_limit` w configu.
2. **Summary się nie generuje** — sprawdź czy `notified_thresholds` w state file nie zawiera już `summary` (idempotentne — tylko raz na próg).
3. **Dashboard nie odpowiada** — sprawdź `chm.dashboard.host` i `port`. Domyślnie `127.0.0.1:8770` — dostępne tylko lokalnie.
4. **Banner nie wyświetla się** — `quiet_mode` agenta jest włączony. To jest celowe zachowanie, nie bug.
5. **Token count niedokładny** — CHM używa heurystyki `len(text) // 4` jeśli hermes-agent estimator nie jest dostępny. W granicach ±15%, wystarczające dla progów 50/70/90%.

## Narzędzia

- `chm.manager.ContextHealthManager` — core
- `chm.observability.init_chm_for_agent(agent)` — hook wywoływany z conversation_loop
- `chm.observability.observe_pre_call(agent, messages)` — read-only, snapshot
- `chm.dashboard.build_app(config)` — FastAPI sub-app
- `chm.dashboard.run_dashboard(config)` — standalone runner
- `chm.summary.default_summary_callback` — generuje artefakt markdown

## Oficjalne źródła

- Plugin location: `~/.hermes/profiles/gaja/plugins/chm/`
- HEOS CONSTITUTION.md (v1.5.2): `CONSTITUTION.md` — zasady HEOS
- ADR-005 (granice profili) — granice HEOS↔runtime
- Hermes Agent context: https://hermes-agent.nousresearch.com/docs/user-guide/configuration

## Wersjonowanie

- **v1.0** (2026-07-23) — pierwsza wersja, zainstalowana przez Jokera w profilu `gaja`.

## Checklisty

### Pre-install
- [ ] Hermes `gaja` jest aktywny
- [ ] Python `fastapi` + `uvicorn` dostępne (`pip install fastapi uvicorn`)
- [ ] Config CHM dodany do `~/.hermes/profiles/gaja/config.yaml`

### Post-install
- [ ] `python3 ~/.hermes/profiles/gaja/plugins/chm/src/chm/__init__.py` → no error
- [ ] Dashboard binduje: `curl -s http://127.0.0.1:8770/` → 200 OK
- [ ] Hook działa: nowa sesja → banner CHM pojawia się w outpucie

## Najlepsze praktyki

1. **Heurystyka > dokładność** — tokeny są szacowane (char/4), nie mierzone (tiktoken). Progi 50/70/90% są poprawne niezależnie od estymatora.
2. **CHM jest opt-in** — domyślnie włączony, ale wyłączenie to `chm.enabled: false` w configu. Zero impactu na Hermes bez CHM.
3. **Idempotentny summary** — triggerowane raz na próg, nie przy każdym wywołaniu modelu powyżej progu.
4. **Dashboard na 127.0.0.1** — domyślnie tylko lokalny. Dla zdalnego dostępu zmień `host` na `0.0.0.0` (ale rozważ firewall).
5. **Nie hardcode thresholds** — wszystko w config.yaml, nigdy w kodzie.

## Powiązane

- **ADR-005** — granice profili Hermes (CHM jest w profilu `gaja`).
- `CONSTITUTION.md` (HEOS v1.5.2) — konstytucja.
- Hermes Agent config: https://hermes-agent.nousresearch.com/docs/user-guide/configuration
- `nightly-evolution` skill — używa CHM do analizy kontekstu sesji w nocnym audycie.

## Lessons Learned

- Ten Skill jest utrzymywany w HEOS. Aktualizuj gdy masz nowe wnioski z runtime.
- Jeśli coś nie działa, sprawdź Debugging w tym Skillu lub podobne Skillsy.

## Verification

Po włączeniu CHM sprawdź czy faktycznie działa:

- [ ] **Plugin załadowany** — `hermes config get chm.enabled` zwraca `true`
- [ ] **Dashboard odpowiada** — `curl -sS http://127.0.0.1:7865/health` (lub odpowiedni port z configu) zwraca `{"status":"ok"}`. Bez tego dashboard = martwy plugin.
- [ ] **Token counter się aktualizuje** — odpowiedz na pytanie, za 5s sprawdź czy `token_count` w dashboard wzrósł. Jeśli stoi w miejscu → CHM nie podpięty do conversation_loop.
- [ ] **Threshold 70%** działa — wyślij długą wiadomość (>50% kontekstu), obserwuj czy pojawił się auto-summary. Jeśli nie → próg nieaktywny lub event nie jest emitowany.
- [ ] **Log bez błędów** — `journalctl -u hermes-gateway --since "5min ago" | grep -iE 'chm|context.health'` nie pokazuje ERROR/Traceback. CHM nie może crashować głównej pętli.
- [ ] **Disable działa czysto** — `chm.enabled: false` w configu + restart → dashboard martwy, ale Hermes działa normalnie (CHM nie jest required path).

Fail gdy: dashboard martwy, tokeny nie aktualizują się, lub CHM crashuje gateway w logach.

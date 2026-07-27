# HDS — full code audit v1

**Date:** 2026-07-25  
**Repository:** `/home/gaja/gaja-projekty/HDS`  
**Reviewed revision:** `2345a37` (`main`, one local commit ahead of `origin/main`)  
**Scope:** all tracked Python, tests, REST/SSE contract, security, client runtime, adapters, installers, systemd/udev packaging and operational documentation.  
**Method:** manual review, three independent reviewer agents, full test/lint/type/coverage run, OpenAPI validation, `systemd-analyze verify`, and targeted runtime reproducers.  
**Repository modifications:** none. This report is stored outside the HDS repository.

## Executive verdict

**NO-GO for a fresh production installation.** The design foundations are strong, but the checked revision contains release blockers in the client refresh loop, server entry point, client packaging/interpreter path, Wayland user identity, and the new vtconsole rule.

This does **not** mean the currently hand-configured RPi/NUC pair cannot appear operational. It means the repository, as a reproducible source of truth, cannot currently recreate that installation reliably from scratch.

**Confidence: ★★★★★.** The blockers are supported by failing tests, direct entry-point/systemd inspection, official Linux kernel documentation, or deterministic control-flow analysis.

## Verification evidence

| Check | Result |
|---|---|
| Full pytest | **542 passed, 2 failed, 1 skipped** in 32.37 s |
| Failing tests | Both `tests/integration/test_main_loop.py`; `TypeError` at `src/hds/client/main.py:161` |
| Coverage | **85% total branch coverage**; `server/api/v1/sse.py` only 23%, `client/main.py` 69% |
| Ruff lint | Passed |
| Ruff format check | Failed: **30 files would be reformatted** |
| mypy strict | Passed: 52 source files, 0 issues |
| compileall | Passed |
| OpenAPI validator | `docs/api/openapi.yaml: OK` |
| pip check | No broken requirements |
| systemd verification | `StartLimitIntervalSec` invalid in server `[Service]`; `hds-server` executable missing |
| Git state | HDS working tree clean; local `main` one commit ahead of origin |

---

# Confirmed blockers — P0

## HDS-001 — snapshot refresh crashes the client

**Location:** `src/hds/client/main.py:137-177`, especially `:161` and `:224`.

`run_forever()` creates `snapshot_lock = asyncio.Lock()`, then passes it to the synchronous render thread. `_render_loop()` executes `with snapshot_lock:`, but `asyncio.Lock` only supports `async with` on its owning event loop.

**Evidence:** both full-suite failures end with:

```text
TypeError: 'Lock' object does not support the context manager protocol
```

**Impact:** the render task terminates when a refresh signal reaches it; systemd then restarts the client. The UI cannot reliably update from SSE.

**Minimum fix:** replace the entire cross-thread bridge with `queue.Queue[Snapshot]` or a small thread-safe snapshot store using `threading.Lock`. Do not pass asyncio synchronization primitives into the render thread.

## HDS-002 — refresh and screen-switch state machines are logically broken

**Location:** `src/hds/client/main.py:225-292`.

The same `refresh_flag` is consumed and cleared independently by:

- render-thread `refresh_now()` (`:258-262`), and
- async `refresh_loop()` (`:281-292`).

Only one side observes each event:

1. If render consumes it first, it rebuilds from the old snapshot and no HTTP refresh occurs.
2. If async refresh consumes it first, it fetches and appends a new snapshot, but no render-update signal remains.

Separately, `on_switch()` only changes `current_name`; the local `screen` object in `_render_loop()` is rebuilt only on the same broken refresh path. A Dashboard→Face touch therefore does not immediately change the rendered screen.

**Impact:** even after fixing HDS-001, live data and navigation remain unreliable.

**Minimum fix:** use two explicit channels: an `asyncio.Event` for “fetch requested” and a thread-safe queue/reference for “new snapshot/screen requested”. Add an integration test that asserts actual rendered screen identity after touch and actual snapshot data after SSE.

## HDS-003 — packaged server service points to a nonexistent executable

**Locations:**

- `pyproject.toml:52-53` — only `hds-admin` is declared.
- `packaging/systemd/hds-server.service:13` — expects `/opt/hds/.venv/bin/hds-server`.

**Evidence:** installed distribution exposes only:

```text
console_scripts hds-admin -> hds_admin.cli:main
```

`.venv/bin/hds-server` does not exist. `systemd-analyze verify` reports the missing executable.

**Impact:** a fresh installation ends in systemd `203/EXEC`; the server never starts.

**Minimum fix:** add a tested `hds-server` console entry point that starts uvicorn, or change the unit to a real executable such as `/opt/hds/.venv/bin/uvicorn hds.server.main:app ...`. Add a packaging test that installs a wheel into a clean venv and executes every unit `ExecStart` target.

## HDS-004 — fresh client install and systemd use different Python environments

**Locations:**

- `install/install-client.sh:87-94` installs HDS into `/opt/hds/.venv`.
- `packaging/systemd/hds-client.service:15` runs `/usr/bin/python3 -m hds.client.main`.

HDS uses a `src/` layout, so merely setting `WorkingDirectory=/opt/hds` does not make `src/hds` importable. The system interpreter cannot see the package installed only in the venv.

**Impact:** a fresh install is expected to fail with `ModuleNotFoundError: No module named 'hds'`, unless an undocumented out-of-band system installation already exists.

**Minimum fix:** choose one supported runtime and make installer/unit/docs consistent. For RPi 3A+, the proven route is system Python + apt Pygame + an explicit HDS system installation; otherwise use a venv created with `--system-site-packages` and run its Python.

## HDS-005 — client installer dependency block is not a valid install path

**Locations:** `install/install-client.sh:59-65`, `:87-94`; `pyproject.toml:32-36`.

There are two independent problems:

1. A backslash-continued `apt-get install` is followed immediately by shell comment lines. After backslash-newline removal, the comment terminates the apt command; the later `python3 python3-pip ...` line becomes a separate command rather than package arguments.
2. The script installs apt `python3-pygame`, then creates an isolated venv and installs `.[client]`, whose dependencies request PyPI `pygame` and `evdev`. The apt module is not visible in that venv. On ARMv7, Pygame has no suitable wheel and source compilation previously OOM-killed the RPi 3A+.

**Impact:** installation can abort before the service is deployed, or repeat the known ARMv7 OOM path.

**Minimum fix:** remove comments from inside the continued command, use the correct apt packages, and make the selected Python environment see apt-installed modules. Add a shell-level sandbox test that validates the actual argv, not only `bash -n`.

## HDS-006 — fresh installer creates the wrong Wayland identity

**Locations:**

- `install/install-client.sh:69-72` creates `hds` as a system user.
- `packaging/systemd/hds-client.service:10,25,42-43` runs as `hds` but points at `/run/user/1000/wayland-0`.

A system user normally receives UID below 1000. `/run/user/1000` belongs to the graphical login user and is typically mode 0700. The hardened service has no capability to bypass that ownership.

**Impact:** the client cannot open the Wayland socket on a fresh installation; likely result is a black panel or SDL display-init failure.

**Minimum fix:** decide explicitly whether HDS runs inside the UID-1000 graphical session or as a system daemon. For Wayland, prefer a user service belonging to the autologin user. Do not hard-code another user's runtime directory.

## HDS-007 — the new vtconsole “unbind” rule performs the opposite operation

**Location:** `packaging/udev/99-hds-vtcon1-unbind.rules:12` (local unpushed commit `2345a37`).

The rule writes:

```sh
echo 1 > /sys/class/vtconsole/vtcon1/bind
```

Official kernel documentation states: `0` unbinds, `1` binds. The file's comment says it intends to unbind. In addition, `install/install-client.sh` never installs this new rule.

**Impact:** the proposed black-screen fix cannot work as described and may re-bind the console. The local commit should not be pushed or deployed unchanged.

**Minimum fix:** use `0`, install the rule explicitly, reload/trigger udev, and verify the resulting `bind` value on the target Pi. Hardware verification is required before acceptance.

---

# High-priority defects — P1

## HDS-008 — client and server implement different SSE protocols

**Server:** `src/hds/domain/models.py:240-249` emits names such as:

- `snapshot.changed`
- `notification.created`
- `notification.dismissed`
- `heartbeat`

**Client:** `src/hds/client/transport_sse.py:29-36` accepts:

- `snapshot.refresh`
- `notification`
- `server.heartbeat`

The server's periodic heartbeat is only an SSE comment (`: heartbeat`), which the client parser intentionally ignores. The client parses `id` but never sends `Last-Event-ID` when reconnecting, and `sse_heartbeat_timeout_sec` is configured but unused.

**Impact:** refresh recovery, notifications, heartbeat health, and replay do not work end-to-end. Client integration tests use a mock protocol that differs from the real server, masking the defect.

**Fix:** define one canonical event enum/wire contract shared by both sides; implement Last-Event-ID persistence, watchdog state transitions, and a real client↔FastAPI SSE integration test.

## HDS-009 — production server has no event producers

**Locations:** `src/hds/server/main.py:188-204`; repository-wide search for `EventBus.publish()`.

The server creates `EventBus`, but does not start tasks that consume adapter event streams or publish snapshot changes. Current adapters also expose empty event iterators. Therefore `/api/v1/events` provides only keepalive comments.

**Impact:** SSE exists structurally but carries no application updates. The UI can only remain at its initial snapshot unless another polling mechanism is added.

**Fix:** add an adapter-event supervisor and/or deterministic snapshot polling/diff publisher. Track task health in diagnostics.

## HDS-010 — render lifecycle is not safely stoppable

**Location:** `src/hds/client/main.py:137-180`, `:297-326`.

- Pygame setup and rendering are submitted separately to the default executor, so same-thread SDL affinity is not guaranteed.
- The render loop has no stop event.
- Cancelling the executor future does not stop its underlying thread.
- Pending tasks are cancelled but not awaited.
- `pygame.quit()` and `TouchInput.stop()` are never called in `finally`.

**Impact:** SIGTERM/restart can leave threads, sockets, or display state behind. Once HDS-001 is fixed, current timeout-based integration tests risk hanging because `asyncio.run()` waits for executor shutdown while the render loop remains infinite.

**Fix:** create one dedicated render thread that owns setup, event pump, drawing, and teardown; control it with `threading.Event`; await async task cancellation.

## HDS-011 — direct evdev touch path is disabled and contains a double-open leak

**Locations:**

- `src/hds/client/main.py:215-219` constructs `TouchInput(use_evdev=False)` and never calls `start()`.
- `src/hds/client/input/evdev_touch.py:182-193` opens `evdev.InputDevice` twice.

**Impact:** the documented evdev fallback is not active. Touch works only if SDL/Wayland converts it into mouse events. If evdev is enabled later, the duplicate open can leak the first descriptor or disable input after a second-open failure.

**Fix:** open once, discover the device by stable udev identity instead of hard-coded `/dev/input/event2`, and explicitly start/stop the reader when direct evdev mode is configured.

## HDS-012 — EventBus can lose or over-evict events silently

**Location:** `src/hds/server/api/v1/event_bus.py:67-113`, `:134-150`; `sse.py:85-130`.

Three defects interact:

1. `deque(maxlen=...)` auto-evicts an event, but `_current_bytes` is not reduced for that automatic eviction. Long-running byte accounting drifts upward and can over-evict the real buffer.
2. `QueueFull` is suppressed silently for slow subscribers; no dropped-event metric or forced snapshot recovery is emitted.
3. Replay is performed before live subscription, leaving a race window in which an event can be published and missed.

**Impact:** clients can miss critical status/notification events and may receive less replay history than configured.

**Fix:** manage count eviction manually, expose dropped-event telemetry, trigger `snapshot.changed` recovery, and atomically obtain replay plus subscription cursor.

## HDS-013 — secret redaction filter does not protect child logger records

**Location:** `src/hds/server/security/auth.py:117-122`.

`install_log_filter()` attaches the filter to the root logger object. Python logger filters are not applied by ancestor loggers to propagated records; handler filters are. A targeted runtime reproducer logged:

```text
api key=SUPERSECRET123456
```

from a child logger despite the installed filter.

**Impact:** a future child logger that includes a secret value can leak it to journald.

**Fix:** install the filter on every root handler (and on subsequently added handlers), or use structured logging with an explicit redacting formatter. Add a regression test using `logging.getLogger('hds.child')`.

## HDS-014 — secret writer contradicts its own safety contract

**Location:** `src/hds/server/security/secrets.py:104-121`.

The docstring promises atomic writing and refusal to overwrite different existing content. The code directly uses `O_TRUNC` and has no `overwrite` argument. Runtime reproduction wrote `A...`, then silently replaced it with `B...`.

**Impact:** callers can destroy the active secret on partial failure; documented guarantees are false.

**Fix:** write an `0600` temp file in the same directory, fsync, then `os.replace`; implement explicit overwrite policy or correct the API/docs.

## HDS-015 — server systemd restart limiting is partly ignored

**Location:** `packaging/systemd/hds-server.service:17-18`.

`StartLimitIntervalSec` is placed in `[Service]`; systemd reports it as an unknown key and ignores it. It belongs in `[Unit]`.

**Impact:** crash-loop limiting does not match the documented policy.

**Fix:** move it to `[Unit]` and add `systemd-analyze verify` to CI.

## HDS-016 — RPi boot configuration installation is incomplete

**Location:** `install/install-client.sh:114-129`.

- Copying `hds.conf` into an arbitrary `hds.d/` directory does not make Raspberry Pi firmware load it unless the main `config.txt` contains a matching `include` directive.
- The script inserts the kernel `video=` argument only by replacing `quiet`; if `quiet` is absent, nothing changes.
- The shipped `cmdline.txt.fragment` is not actually consumed.

**Impact:** a fresh Pi may boot at the wrong display mode despite a successful installer message.

**Fix:** idempotently manage an `include` line and append the cmdline token to the single cmdline line even when `quiet` is absent; back up and verify both files.

## HDS-017 — operator documentation can rotate the client key to the wrong owner

**Location:** `docs/operations/install-client.md:49,105-108,116-119`; compare installer/service user `hds`.

The guide alternates between users `panel` and `hds`; key-update commands create `client.key` owned by `panel`, while the service runs as `hds`.

**Impact:** documented rotation can cause persistent 401 or permission failure.

**Fix:** select one runtime user and replace every command, ownership check, autologin instruction, and verification example consistently.

## HDS-018 — verification CLI rejects the supported RPi Python and misdetects role

**Location:** `src/hds_admin/verify_installation.py:56`, `:173-196`.

- Version check uses `<3.13`, while `pyproject.toml` supports `<3.14` and Raspbian trixie uses Python 3.13.
- Unit autodetection calls `systemctl show -p Id --value` without naming a unit and tends to fall back to `hds-server`.

**Impact:** a correct RPi installation can be reported as failed or checked against the wrong service.

**Fix:** accept 3.13 and require/derive an explicit `--role client|server` from installed unit files.

## HDS-019 — enabling command capabilities exposes success-reporting no-op commands

**Location:** `src/hds/server/api/v1/commands_dispatch.py:56-100`.

When `HDS_CAPABILITIES_ENABLED=1`, `rotate-key` and `restart-adapter` use `_stub_runner`, which returns `accepted=True` without performing the operation.

**Impact:** an operator/API client can receive false confirmation for a security or recovery action.

**Fix:** keep write commands unregistered until real handlers and tests exist, or return `501 Not Implemented`/`accepted=False`.

## HDS-020 — adapter isolation is incomplete

**Location:** `src/hds/adapters/manager.py:119-160`.

- `restart()` sleeps for up to 300 seconds while holding the manager lock.
- `health()` awaits each adapter sequentially with no timeout.
- `SnapshotService` similarly awaits snapshots sequentially; one hung adapter can hang every snapshot request.

**Impact:** one faulty adapter can stall lifecycle and API availability despite the stated failure-isolation goal.

**Fix:** keep locks around state mutation only; apply per-adapter timeouts and collect independent checks concurrently with bounded fan-out.

---

# Medium-priority improvements — P2

1. **Real adapters are not wired into production.** `server.main._build_manager()` registers only fake/placeholder adapters. This agrees with the README's alpha status but not with a production-ready Hermes dashboard.
2. **ETag will churn with real adapters.** `snapshot_endpoint.py` excludes `generated_at` and health timestamps, but newly created `Metric.timestamp` and `Status.since` values remain in the hash.
3. **API error bodies are inconsistent.** Some paths return FastAPI `{"detail": ...}`, others nest `{"error":...}` under `detail`, despite a canonical error contract.
4. **Audit capability denials are missing.** A valid-key request denied by the capabilities gate records auth allow but not capability deny.
5. **Audit-log failure is fail-open.** This may be acceptable for availability, but it needs a health metric/alert because audit loss is currently only a warning.
6. **Synchronous file and psutil calls run inside async endpoints.** Hermes file reads and adapter sampling should move to threads or bounded background sampling.
7. **Duplicate/misleading code remains.** `client/transport.py` contains a placeholder SSE implementation alongside the real module; `AdapterRegistry` is unused; `client/dashboard.py` is an older renderer beside `client/screens/dashboard.py`.
8. **README/docs are stale.** They mention missing `config/`, missing `server/diagnostics/ResourceSampler`, outdated users/paths, an invalid curl example, and a local `.venv/bin/hds-client` executable that is not declared.
9. **No CI pipeline is tracked.** There is no `.github/workflows`; tests, format, type checks, OpenAPI and systemd verification are not enforced remotely.
10. **No reproducible dependency lock or automated vulnerability scan.** Add `uv.lock`/constraints, Dependabot and `pip-audit` before release.
11. **Formatting gate is not clean.** Ruff lint passes, but 30 files fail `ruff format --check`.
12. **Coverage is broad but risk-weighting is weak.** Total is 85%, while the server SSE implementation is only 23% and the client main loop—the main source of blockers—is 69%.
13. **Key preview should not be logged.** `install-server.sh` prints a fragment of the generated key. This is not a practical brute-force break, but violates least-exposure policy and should be replaced by a fingerprint.
14. **Proxy client IP needs an explicit trust model.** `request.client.host` records the proxy address. Do not blindly trust `X-Forwarded-For`; configure trusted proxy hosts first.
15. **Configuration validation is minimal.** Invalid URL, dimensions, FPS, heartbeat and backoff ranges fail late instead of producing a clear startup diagnostic.

---

# What is already good

- Clear layering: domain → adapters → server/client → packaging.
- Strict immutable Pydantic wire models with `extra="forbid"`.
- Strong mypy configuration and clean strict result.
- Constant-time API-key verification and path-based secrets.
- Bounded conceptual SSE replay design and explicit resource budgets.
- Good systemd hardening baseline (`ProtectSystem`, `NoNewPrivileges`, empty capabilities, address-family limits).
- Large, organized test suite with unit, contract, integration and golden tests.
- Valid exported OpenAPI contract.
- Operational documentation records real RPi failures instead of hiding them.
- Small, atomic commit history and clean HDS working tree.

---

# Recommended repair order

## Phase A — restore reproducible boot (must fix first)

1. Fix `hds-server` entry point/unit.
2. Select one RPi Python/runtime model and align installer + service.
3. Align graphical user, UID and Wayland user service.
4. Correct/install the vtconsole rule and verify on hardware.
5. Repair boot config installation and installer dependency command.

**Acceptance:** clean-image NUC + RPi installation succeeds using only repository docs/scripts; both units start after reboot.

## Phase B — repair client state machine

1. Replace flag/list/async-lock bridge with explicit thread-safe channels.
2. Make one render thread own all SDL/Pygame calls and teardown.
3. Make touch, screen switch and snapshot refresh observable in integration tests.

**Acceptance:** full suite passes; repeated SSE refreshes update pixels/data; Dashboard↔Face switches immediately; SIGTERM exits without hanging threads.

## Phase C — unify SSE contract

1. One shared event enum and heartbeat semantics.
2. Real server event producers.
3. Last-Event-ID replay, gap recovery and heartbeat timeout.
4. Correct EventBus accounting/backpressure.

**Acceptance:** real FastAPI server + real client integration test proves reconnect/replay and forced snapshot recovery.

## Phase D — security and release gate

1. Repair redaction and secret write semantics.
2. Fix audit denials/error bodies.
3. Add per-adapter timeouts.
4. Add CI: tests, coverage threshold, Ruff lint+format, mypy, OpenAPI, systemd verify, shellcheck, pip-audit.
5. Update README and operations docs.

**Acceptance:** all gates green and no P0/P1 findings remain.

## Final recommendation

Start with a focused **Phase A + Phase B repair branch**, not cosmetic refactoring. The fastest path to value is to make a fresh install and the current client loop deterministic before adding more screens or adapters.

**Confidence: ★★★★★.** The recommended order follows direct dependency: packaging must boot before runtime can be validated; runtime must be stable before SSE and adapter features can be trusted.

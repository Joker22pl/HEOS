#!/usr/bin/env python3
"""
lab_helper.py — read-only workshop diagnostic helper for gaja-lab-core.

Pure stdlib, zero side effects. Every command is a read operation; nothing
flashes, mounts, writes to disk, or alters system state.

Subcommands (all return JSON to stdout, exit 0 on success, 2 on usage error,
3 on tool missing, 4 on permission denied):

  list-usb          — every USB device (lsusb -v parsed) with VID/PID/class
  list-serial       — every /dev/tty* port with symlink + permission audit
  identify-board    — best-effort board identification from VID/PID
  read-descriptor   — full lsusb -v dump for a single bus/device address
  read-serial-log   — last N lines from a serial port (non-blocking, with timeout)
  check-permissions — can the current user open each serial port + udev rules
  check-toolchain   — which dev tools are available (esptool, mpremote, ...)
  capture-dmesg     — last kernel events matching usb/serial/ch341/cp210x/ftdi

Each subcommand writes a single JSON object on stdout, with at minimum:
  { "ok": true|false, "tool": "...", "data": <payload>, "warnings": [...],
    "errors": [...], "host": <hostname> }

The agent reads stdout verbatim — no need to parse, just hand it to the model.

Usage:
  lab_helper.py list-usb
  lab_helper.py list-serial
  lab_helper.py identify-board
  lab_helper.py read-descriptor 003:042
  lab_helper.py read-serial-log /dev/ttyUSB0 --lines 50 --timeout 2
  lab_helper.py check-permissions
  lab_helper.py check-toolchain
  lab_helper.py capture-dmesg --since "10 min ago"
"""
from __future__ import annotations

import argparse
import grp
import json
import os
import pwd
import re
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

__version__ = "1.0.0"

HOST = socket.gethostname()
TOOL_LSUSB = shutil.which("lsusb")
TOOL_LSUSB_V = shutil.which("lsusb")  # same binary, -v flag
TOOL_DMESG = shutil.which("dmesg")
TOOL_GETFACL = shutil.which("getfacl")
TOOL_STAT = shutil.which("stat")
TOOL_LSOF = shutil.which("lsof")
TOOL_UDEVADM = shutil.which("udevadm")

SERIAL_GLOB = "/dev/tty{USB,ACM,AMA,AMA0,USB0,USB1,USB2,USB3,ACM0,ACM1,ACM2}"
DEV_SERIAL = Path("/dev/serial/by-id")
DEV_TTY = Path("/dev/tty")

DEFAULT_TTY_GROUPS = ("dialout", "tty", "uucp")
DEFAULT_DMESG_LINES = 200

# Common VID/PID → friendly board name. Best-effort only — unknown devices
# return "Unknown (VID:PID)" and the agent is expected to look it up if needed.
BOARD_DB: dict[tuple[str, str], str] = {
    # Espressif
    ("303a", "1001"): "ESP32-S3 (ROM bootloader mode)",
    ("303a", "4001"): "ESP32-S3 (application mode, USB-Serial/JTAG)",
    ("303a", "0002"): "ESP32-S2 (USB-OTG)",
    ("303a", "0001"): "ESP32-S2 (ROM bootloader)",
    ("10c4", "ea60"): "Silicon Labs CP2102/CP2104 (generic USB-UART bridge)",
    # Adafruit
    ("239a", "811b"): "Adafruit Feather ESP32-S3",
    ("239a", "80f4"): "Adafruit Feather RP2040",
    ("239a", "801f"): "Adafruit Trinket M0 (SAMD21)",
    # FTDI
    ("0403", "6001"): "FTDI FT232R (USB-UART bridge)",
    ("0403", "6010"): "FTDI FT2232H (dual UART/FIFO)",
    ("0403", "6011"): "FTDI FT4232H (quad UART)",
    ("0403", "6014"): "FTDI FT232H (single UART, MPSSE)",
    # WCH (CH340/CH341/CH9102 — popular cheap clones)
    ("1a86", "7523"): "WCH CH340/CH341 (USB-UART, very common on clones)",
    ("1a86", "55d4"): "WCH CH9102 (USB-UART, modern CH340 replacement)",
    # STM32
    ("0483", "3748"): "STMicroelectronics STM32 (DFU / bootloader mode)",
    ("0483", "5740"): "STMicroelectronics Virtual COM Port (e.g. Nucleo, Discovery)",
    # Raspberry Pi
    ("2e8a", "000a"): "Raspberry Pi Pico (RP2040, application mode)",
    ("2e8a", "0003"): "Raspberry Pi RP2040 (BOOTSEL / bootloader mode)",
    ("2e8a", "0005"): "Raspberry Pi Pico 2 (RP2350, BOOTSEL mode)",
    # Arduino
    ("2341", "0043"): "Arduino Uno R3",
    ("2341", "004b"): "Arduino Mega 2560",
    ("2341", "004a"): "Arduino Nano",
    ("2341", "8036"): "Arduino Leonardo / Micro (native USB)",
    # Nordic / nRF
    ("1366", "0105"): "Nordic nRF52840 Dongle (OpenOCD + USB CDC)",
    # Teensy
    ("16c0", "0483"): "Teensy 4.x (USB Serial)",
}


# ---------- output envelope --------------------------------------------------


def envelope(
    tool: str,
    data: Any = None,
    *,
    ok: bool = True,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ok": ok,
        "tool": tool,
        "host": HOST,
        "data": data,
        "warnings": list(warnings or []),
        "errors": list(errors or []),
    }
    if extra:
        out.update(extra)
    return out


def emit(payload: dict[str, Any]) -> None:
    """Write JSON to stdout, single line, UTF-8, no trailing newline bloat."""
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")


def fail(tool: str, message: str, code: int = 1, **extra: Any) -> None:
    emit(envelope(tool, ok=False, errors=[message], extra=extra))
    sys.exit(code)


# ---------- shell helpers (only for read-only commands) ----------------------


def run_capture(cmd: list[str], timeout: float = 5.0) -> tuple[int, str, str]:
    """Run cmd, return (rc, stdout, stderr). Timeout-safe."""
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError as e:
        return 127, "", f"command not found: {e}"
    except subprocess.TimeoutExpired as e:
        return 124, e.stdout or "", f"timeout after {timeout}s"
    except OSError as e:
        return 126, "", f"os error: {e}"


def run_capture_pty(cmd: list[str], timeout: float = 5.0) -> tuple[int, str, str]:
    """Same as run_capture but for short cmds where terminal hint helps."""
    return run_capture(cmd, timeout=timeout)


# ---------- command: list-usb -----------------------------------------------


def parse_lsusb_verbose(text: str) -> list[dict[str, Any]]:
    """Parse `lsusb -v` output into per-device dicts. Best-effort."""
    devices: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    indent_marker: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        # New device block starts with "Bus <n> Device <n>: <VID:PID> <stuff>"
        m = re.match(r"Bus\s+(\d+)\s+Device\s+(\d+):\s+ID\s+([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\s*(.*)", line)
        if m:
            if cur is not None:
                devices.append(cur)
            cur = {
                "bus": int(m.group(1)),
                "device": int(m.group(2)),
                "vid": m.group(3).lower(),
                "pid": m.group(4).lower(),
                "raw_name": m.group(5).strip(),
                "name": m.group(5).strip(),
            }
            indent_marker = None
            continue
        if cur is None:
            continue
        # Single-line lsusb: "Bus 003 Device 002: ID 8087:07dc ..."
        m2 = re.match(r"\s*Bus\s+(\d+)\s+Device\s+(\d+):\s+ID\s+([0-9a-fA-F]{4}):([0-9a-fA-F]{4})", line)
        if m2:
            continue  # already captured above
        # Detail lines under -v
        if cur is not None and line.lstrip() != line:
            stripped = line.strip()
            for key, target in (
                ("iManufacturer", "manufacturer"),
                ("iProduct", "product"),
                ("iSerial", "serial"),
                ("bDeviceClass", "device_class"),
                ("bDeviceSubClass", "device_subclass"),
                ("bDeviceProtocol", "device_protocol"),
                ("bInterfaceClass", "interface_class"),
                ("bInterfaceSubClass", "interface_subclass"),
                ("bInterfaceProtocol", "interface_protocol"),
                ("bcdDevice", "bcd_device"),
            ):
                # match "  bLength  9 bDescriptorType  1 bcdUSB  2.00 ..."
                km = re.search(rf"\b{re.escape(key)}\s+(.+?)(?=\s+[a-zA-Z][\w]*\s|\s*$)", line)
                if km:
                    cur[target] = km.group(1).strip()
            # Many "  iManufacturer  1 Espressif" lines
            im = re.match(r"\s*iManufacturer\s+(\d+)\s+(.*)", line)
            if im and "manufacturer" not in cur:
                cur["manufacturer"] = im.group(2).strip()
            ip = re.match(r"\s*iProduct\s+(\d+)\s+(.*)", line)
            if ip and "product" not in cur:
                cur["product"] = ip.group(2).strip()
            isr = re.match(r"\s*iSerial\s+(\d+)\s+(.*)", line)
            if isr and "serial" not in cur:
                cur["serial"] = isr.group(2).strip()
    if cur is not None:
        devices.append(cur)
    # Fill name fallback
    for d in devices:
        parts = [d.get(k, "") for k in ("manufacturer", "product") if d.get(k)]
        if parts:
            d["name"] = " / ".join(parts)
    return devices


def cmd_list_usb(args: argparse.Namespace) -> int:
    if not TOOL_LSUSB:
        return _emit_fail("list-usb", "lsusb not installed (apt: usbutils)", code=3)
    # First fast list (no -v) for a basic inventory, then optional -v.
    rc, out, err = run_capture(["lsusb"], timeout=5.0)
    if rc != 0:
        return _emit_fail("list-usb", f"lsusb failed: {err.strip() or 'unknown'}")
    basic: list[dict[str, Any]] = []
    for line in out.splitlines():
        m = re.match(
            r"Bus\s+(\d+)\s+Device\s+(\d+):\s+ID\s+([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\s*(.*)",
            line.strip(),
        )
        if m:
            basic.append(
                {
                    "bus": int(m.group(1)),
                    "device": int(m.group(2)),
                    "address": f"{m.group(1).zfill(3)}:{m.group(2).zfill(3)}",
                    "vid": m.group(3).lower(),
                    "pid": m.group(4).lower(),
                    "name": m.group(5).strip(),
                    "board_hint": BOARD_DB.get(
                        (m.group(3).lower(), m.group(4).lower()),
                        "Unknown (consult VID:PID online)",
                    ),
                }
            )
    warnings: list[str] = []
    detailed: list[dict[str, Any]] = []
    if args.verbose:
        rc2, out2, err2 = run_capture(["lsusb", "-v"], timeout=15.0)
        if rc2 == 0:
            detailed = parse_lsusb_verbose(out2)
        else:
            warnings.append(f"lsusb -v failed: {err2.strip()}")
    payload = {"basic": basic, "count": len(basic)}
    if detailed:
        payload["detailed"] = detailed
    emit(envelope("list-usb", data=payload, warnings=warnings))
    return 0


# ---------- command: list-serial --------------------------------------------


def list_serial_ports() -> list[Path]:
    """Enumerate /dev/tty{USB,ACM,AMA}* — /dev/tty itself is a char device, not a dir."""
    dev = Path("/dev")
    found: set[Path] = set()
    if not dev.is_dir():
        return []
    for entry in dev.iterdir():
        if entry.name.startswith(("ttyUSB", "ttyACM", "ttyAMA")):
            found.add(entry)
    return sorted(found)


def current_user_groups() -> set[str]:
    import getpass

    user = getpass.getuser()
    out: set[str] = set()
    for g in grp.getgrall():
        if user in g.gr_mem:
            out.add(g.gr_name)
    # Also include the user's primary group
    try:
        primary_gid = pwd.getpwnam(user).pw_gid
        out.add(grp.getgrgid(primary_gid).gr_name)
    except (KeyError, OSError):
        pass
    return out


def audit_port(path: Path, user_groups: set[str]) -> dict[str, Any]:
    info: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        info["error"] = "device node does not exist"
        return info
    try:
        st = path.stat()
        info["mode"] = oct(st.st_mode & 0o777)
        info["uid"] = st.st_uid
        info["gid"] = st.st_gid
        info["size"] = st.st_size
    except OSError as e:
        info["error"] = f"stat failed: {e}"
        return info
    # Group membership
    if st.st_gid in {grp.getgrnam(g).gr_gid for g in user_groups if _group_exists(g)}:
        info["group_ok"] = True
    else:
        info["group_ok"] = False
        info["group_required"] = sorted(DEFAULT_TTY_GROUPS)
    # Readable/writable by current user?
    info["readable"] = os.access(path, os.R_OK)
    info["writable"] = os.access(path, os.W_OK)
    # udev symlink (if any)
    byid = DEV_SERIAL / path.name if False else None  # by-id is by path
    udev_link: str | None = None
    by_id = Path("/dev/serial/by-id")
    if by_id.is_dir():
        for link in by_id.iterdir():
            try:
                if link.resolve() == path.resolve():
                    udev_link = str(link)
                    break
            except OSError:
                continue
    if udev_link:
        info["udev_by_id"] = udev_link
    return info


def _group_exists(name: str) -> bool:
    try:
        grp.getgrnam(name)
        return True
    except KeyError:
        return False


def cmd_list_serial(args: argparse.Namespace) -> int:
    ports = list_serial_ports()
    user_groups = current_user_groups()
    audits = [audit_port(p, user_groups) for p in ports]
    warnings: list[str] = []
    if not ports:
        warnings.append("no /dev/tty{USB,ACM,AMA}* ports present (nothing plugged in?)")
    emit(
        envelope(
            "list-serial",
            data={
                "ports": audits,
                "count": len(audits),
                "user": pwd.getpwuid(os.getuid()).pw_name,
                "user_groups": sorted(user_groups),
            },
            warnings=warnings,
        )
    )
    return 0


# ---------- command: identify-board ----------------------------------------


def cmd_identify_board(args: argparse.Namespace) -> int:
    if not TOOL_LSUSB:
        return _emit_fail("identify-board", "lsusb not installed (apt: usbutils)", code=3)
    rc, out, err = run_capture(["lsusb"], timeout=5.0)
    if rc != 0:
        return _emit_fail("identify-board", f"lsusb failed: {err.strip()}")
    matches: list[dict[str, Any]] = []
    for line in out.splitlines():
        m = re.match(
            r"Bus\s+(\d+)\s+Device\s+(\d+):\s+ID\s+([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\s*(.*)",
            line.strip(),
        )
        if m:
            vid, pid, raw = m.group(3).lower(), m.group(4).lower(), m.group(5).strip()
            hint = BOARD_DB.get((vid, pid), "Unknown — check VID/PID on linux-usb.org or usb-ids.gowdy.us")
            matches.append(
                {
                    "bus": int(m.group(1)),
                    "device": int(m.group(2)),
                    "address": f"{m.group(1).zfill(3)}:{m.group(2).zfill(3)}",
                    "vid": vid,
                    "pid": pid,
                    "name": raw,
                    "board_hint": hint,
                    "is_known": (vid, pid) in BOARD_DB,
                }
            )
    emit(envelope("identify-board", data={"matches": matches, "count": len(matches)}))
    return 0


# ---------- command: read-descriptor ---------------------------------------


def cmd_read_descriptor(args: argparse.Namespace) -> int:
    if not args.address:
        return _emit_fail("read-descriptor", "address required (e.g. 003:042)", code=2)
    if not re.match(r"^\d{3}:\d{3}$", args.address):
        return _emit_fail("read-descriptor", "address must be BBB:DDD (3-digit bus:device)", code=2)
    if not TOOL_LSUSB_V:
        return _emit_fail("read-descriptor", "lsusb not installed", code=3)
    bus, dev = args.address.split(":")
    rc, out, err = run_capture(["lsusb", "-v", "-s", f"{bus}:{dev}"], timeout=10.0)
    if rc != 0:
        return _emit_fail("read-descriptor", f"lsusb failed: {err.strip() or 'unknown'}")
    parsed = parse_lsusb_verbose(out)
    emit(
        envelope(
            "read-descriptor",
            data={"address": args.address, "raw": out, "parsed": parsed[0] if parsed else None},
        )
    )
    return 0


# ---------- command: read-serial-log (NON-WRITING, just reads) -------------


def cmd_read_serial_log(args: argparse.Namespace) -> int:
    """Last N lines from a serial port.

    Read-only: opens O_RDONLY | O_NONBLOCK. If the port produces no data within
    --timeout, we return what we have. NEVER writes to the port.
    """
    if not args.port:
        return _emit_fail("read-serial-log", "port required (e.g. /dev/ttyUSB0)", code=2)
    port = Path(args.port)
    if not port.exists():
        return _emit_fail("read-serial-log", f"{port} does not exist", code=2)
    if not os.access(port, os.R_OK):
        return _emit_fail(
            "read-serial-log",
            f"no read permission on {port} — user must be in 'dialout' or 'tty' group",
            code=4,
        )
    # Build raw read command via stty + cat — avoids pyserial dependency.
    # stty: 8N1, raw, no echo, min=0, time=1 (0.1s per read attempt).
    timeout_decisec = max(1, int(args.timeout * 10))
    lines = max(1, args.lines)
    # Use timeout(1) so we can't block forever
    cmd = [
        "bash",
        "-c",
        (
            f"stty -F {port} 115200 cs8 -cstopb -parenb -icanon -echo -ixon 2>/dev/null; "
            f"timeout {args.timeout} cat {port} 2>/dev/null | head -c 65536"
        ),
    ]
    rc, out, err = run_capture(cmd, timeout=float(args.timeout) + 2.0)
    text = out or ""
    truncated = text.splitlines()[-lines:] if text else []
    warnings: list[str] = []
    if not text:
        warnings.append(
            "no data received within timeout — device may be silent, baud mismatch, or wrong port"
        )
    if err and "Permission denied" in err:
        warnings.append("permission denied on open — add user to 'dialout' group")
    emit(
        envelope(
            "read-serial-log",
            data={
                "port": str(port),
                "lines_requested": lines,
                "lines_returned": len(truncated),
                "bytes_received": len(text),
                "text": "\n".join(truncated),
            },
            warnings=warnings,
        )
    )
    return 0


# ---------- command: check-permissions -------------------------------------


def cmd_check_permissions(args: argparse.Namespace) -> int:
    ports = list_serial_ports()
    user_groups = current_user_groups()
    user = pwd.getpwuid(os.getuid()).pw_name
    group_membership = {
        g: (g in user_groups) for g in DEFAULT_TTY_GROUPS
    }
    port_audits = [audit_port(p, user_groups) for p in ports]
    # Recommend fix
    missing = [g for g in DEFAULT_TTY_GROUPS if g not in user_groups and _group_exists(g)]
    fix_suggestion: list[str] = []
    if missing and ports:
        fix_suggestion.append(
            f"sudo usermod -aG {','.join(missing)} {user}"
        )
        fix_suggestion.append("→ log out and back in (group changes need a new session)")
    # Check udev rules for serial
    udev_rule_files: list[str] = []
    for d in ("/etc/udev/rules.d", "/lib/udev/rules.d"):
        base = Path(d)
        if not base.is_dir():
            continue
        for f in base.iterdir():
            if f.suffix == ".rules":
                try:
                    content = f.read_text(errors="ignore")
                    if any(t in content for t in ("ttyUSB", "ttyACM", "dialout")):
                        udev_rule_files.append(str(f))
                except OSError:
                    continue
    emit(
        envelope(
            "check-permissions",
            data={
                "user": user,
                "groups": sorted(user_groups),
                "serial_group_membership": group_membership,
                "port_count": len(ports),
                "ports": port_audits,
                "missing_groups": missing,
                "fix_suggestion": fix_suggestion,
                "udev_rule_files": udev_rule_files,
            },
            warnings=(
                ["user not in any serial group — cannot open ttyUSB/ttyACM without sudo"]
                if missing and ports
                else []
            ),
        )
    )
    return 0


# ---------- command: check-toolchain --------------------------------------


TOOLCHAIN = [
    ("esptool", "esptool.py"),
    ("mpremote", "mpremote"),
    ("ampy", "ampy"),
    ("rshell", "rshell"),
    ("arduino-cli", "arduino-cli"),
    ("platformio", "platformio"),
    ("openocd", "openocd"),
    ("dfu-util", "dfu-util"),
    ("picotool", "picotool"),
    ("minicom", "minicom"),
    ("screen", "screen"),
    ("tio", "tio"),
    ("putty", "putty"),
]


def cmd_check_toolchain(args: argparse.Namespace) -> int:
    found: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for cmd_name, exec_name in TOOLCHAIN:
        path = shutil.which(exec_name)
        if path:
            rc, out, err = run_capture([exec_name, "--version"], timeout=3.0)
            version = (out or err).strip().splitlines()[0][:120] if (out or err) else "unknown"
            found.append({"name": cmd_name, "path": path, "version": version})
        else:
            missing.append({"name": cmd_name, "install_hint": _install_hint(cmd_name)})
    emit(
        envelope(
            "check-toolchain",
            data={"found": found, "missing": missing, "available_count": len(found)},
            warnings=(
                [f"{len(missing)} toolchain item(s) missing — see install_hint"]
                if missing
                else []
            ),
        )
    )
    return 0


def _install_hint(name: str) -> str:
    return {
        "esptool": "pip install esptool",
        "mpremote": "pip install mpremote",
        "ampy": "pip install adafruit-ampy",
        "rshell": "pip install rshell",
        "arduino-cli": "see https://arduino.github.io/arduino-cli/latest/installation/",
        "platformio": "pip install platformio",
        "openocd": "apt install openocd",
        "dfu-util": "apt install dfu-util",
        "picotool": "https://github.com/raspberrypi/picotool",
        "minicom": "apt install minicom",
        "screen": "apt install screen",
        "tio": "apt install tio",
        "putty": "apt install putty",
    }.get(name, "?")


# ---------- command: capture-dmesg ----------------------------------------


def cmd_capture_dmesg(args: argparse.Namespace) -> int:
    if not TOOL_DMESG:
        return _emit_fail("capture-dmesg", "dmesg not available", code=3)
    # Default: logread of the entire buffer filtered for relevant tokens.
    # dmesg -T gives human timestamps; may need root for some kernels.
    cmd: list[str]
    if args.since:
        # `dmesg -T --since "<X>"` works on util-linux dmesg.
        cmd = [
            "bash",
            "-c",
            (
                f"{shlex_quote('dmesg')} {shlex_quote('-T')} "
                f"{shlex_quote('--since')} {shlex_quote(args.since)} "
                f"{shlex_quote('--level')} {shlex_quote('err,warn,info,debug')} "
                "| tail -n 500 | "
                "grep -E 'usb|serial|tty|ch34|cp210|ftdi|silabs|cdc_acm|pl2303|rndis_host' || true"
            ),
        ]
    else:
        cmd = [
            "bash",
            "-c",
            (
                f"{shlex_quote('dmesg')} {shlex_quote('-T')} {shlex_quote('--nopager')} "
                "| tail -n 500 | "
                "grep -E 'usb|serial|tty|ch34|cp210|ftdi|silabs|cdc_acm|pl2303|rndis_host' || true"
            ),
        ]
    rc, out, err = run_capture(cmd, timeout=5.0)
    if rc != 0 and "permission denied" in (err or "").lower():
        # dmesg may need root
        emit(
            envelope(
                "capture-dmesg",
                ok=False,
                data={"raw": ""},
                errors=[f"dmesg needs root: {err.strip()}"],
                extra={"hint": "run with sudo or add user to 'kmem' group"},
            )
        )
        return 4
    lines = out.splitlines() if out else []
    if args.since is None and lines:
        lines = lines[-args.lines :] if args.lines else lines
    emit(
        envelope(
            "capture-dmesg",
            data={
                "since": args.since,
                "lines_returned": len(lines),
                "text": "\n".join(lines),
            },
            warnings=(
                ["no matching events — device may have been plugged in before this boot"]
                if not lines
                else []
            ),
        )
    )
    return 0


def shlex_quote(s: str) -> str:
    import shlex

    return shlex.quote(s)


# ---------- argument parser -------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lab_helper",
        description="gaja-lab-core read-only workshop diagnostic helper (JSON output)",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("list-usb", help="list every USB device (basic + optional -v details)")
    sp.add_argument("-v", "--verbose", action="store_true", help="include lsusb -v details")
    sp.set_defaults(func=cmd_list_usb)

    sp = sub.add_parser("list-serial", help="list every /dev/tty{USB,ACM,AMA}* + perms")
    sp.set_defaults(func=cmd_list_serial)

    sp = sub.add_parser("identify-board", help="match VID/PID to a known board")
    sp.set_defaults(func=cmd_identify_board)

    sp = sub.add_parser("read-descriptor", help="full lsusb -v dump for one device (BBB:DDD)")
    sp.add_argument("address", help="bus:device address, e.g. 003:042")
    sp.set_defaults(func=cmd_read_descriptor)

    sp = sub.add_parser(
        "read-serial-log",
        help="read last N lines from a serial port (NON-WRITING, raw cat under timeout)",
    )
    sp.add_argument("port", help="e.g. /dev/ttyUSB0")
    sp.add_argument("--lines", type=int, default=50, help="how many trailing lines to keep (default 50)")
    sp.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="seconds to wait for data (default 2.0; cat exits after timeout)",
    )
    sp.set_defaults(func=cmd_read_serial_log)

    sp = sub.add_parser(
        "check-permissions",
        help="audit serial-port perms and report whether current user can open them",
    )
    sp.set_defaults(func=cmd_check_permissions)

    sp = sub.add_parser("check-toolchain", help="which dev tools are available on this host")
    sp.set_defaults(func=cmd_check_toolchain)

    sp = sub.add_parser("capture-dmesg", help="tail kernel log for usb/serial events")
    sp.add_argument("--since", help="e.g. '5 min ago' (passes through to dmesg --since)")
    sp.add_argument("--lines", type=int, default=200, help="if --since omitted, take last N lines (default 200)")
    sp.set_defaults(func=cmd_capture_dmesg)

    return p


def _emit_fail(tool: str, message: str, *, code: int = 1) -> int:
    emit(envelope(tool, ok=False, errors=[message]))
    return code


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args) or 0
    except KeyboardInterrupt:
        emit(envelope(args.command, ok=False, errors=["interrupted"]))
        return 130
    except Exception as e:  # noqa: BLE001 — last-resort guard, must not crash caller
        emit(
            envelope(
                args.command if hasattr(args, "command") else "unknown",
                ok=False,
                errors=[f"{type(e).__name__}: {e}"],
            )
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())

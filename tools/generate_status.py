#!/usr/bin/env python3
"""
generate_status.py — generuje STATUS.md z aktualnego stanu HEOS.

Zbiera:
- Datę wygenerowania
- Wersję HEOS (z README lub git tag)
- Liczbę artefaktów wg typu (z .registry.yaml — generuje gośli brak)
- Wynik skill_audit i heos_lint (wywołuje subprocess)
- Ostatni commit (git log -1)
- Liczbę templates, tools, heos-migration/ plików

Użycie:
    python3 generate_status.py [--root /path/to/HEOS] [--output STATUS.md]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


HEOS_ROOT_DEFAULT = Path(__file__).resolve().parent.parent
OUTPUT_DEFAULT = HEOS_ROOT_DEFAULT / "STATUS.md"


def _git_last_commit(root: Path) -> dict:
    """Zwraca informacje o ostatnim commicie (hash, date, subject)."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H|%ai|%s"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return {}
        parts = result.stdout.strip().split("|", 2)
        if len(parts) >= 3:
            return {"hash": parts[0], "date": parts[1], "subject": parts[2]}
        return {}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {}


def _git_tags(root: Path) -> list[str]:
    """Zwraca listę git tagów."""
    try:
        result = subprocess.run(
            ["git", "tag"], cwd=root, capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return [t.strip() for t in result.stdout.splitlines() if t.strip()]
        return []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def _heos_version(root: Path, tags: list[str]) -> str:
    """Wykrywa wersję HEOS z git tagów (priorytet) lub plików (fallback)."""
    # Priorytet 1: tag v*.*.*
    version_tags = [t for t in tags if t.startswith("v") and "." in t]
    if version_tags:
        return version_tags[-1]  # ostatni
    # Priorytet 2: grep w README.md
    readme = root / "README.md"
    if readme.exists():
        import re
        text = readme.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\*\*Wersja HEOS:\*\*\s*(\S+)", text)
        if m:
            return m.group(1)
    # Priorytet 3: szukaj MASTER-PROMPT/CONSTITUTION w dowolnym miejscu
    import re
    for md in root.rglob("*.md"):
        m = re.search(r"v?(\d+\.\d+)", md.name)
        if m and any(k in md.name for k in ("MASTER-PROMPT", "CONSTITUTION", "MASTER")):
            return f"v{m.group(1)}"
    return "unknown"


def _count_files(root: Path, pattern: str) -> int:
    """Liczy pliki pasujące do wzorca (glob). Pomija katalogi cache i ukryte pliki.

    Wcześniejszy bug: glob('*') łapał też __pycache__/ + .pytest_cache/ (ukryte katalogi),
    co dawało zawyżone "Tools: 25" zamiast realnych 22 .py + 1 .sh = 23 plików.
    """
    return sum(
        1 for p in root.glob(pattern)
        if p.is_file() and not p.name.startswith(".")
    )


def _registry_or_generate(root: Path) -> dict:
    """Zwraca registry — generuje jeśli brak."""
    registry_path = root / ".registry.yaml"
    if not registry_path.exists():
        # Generuj przez generate_registry
        gen_script = root / "tools" / "generate_registry.py"
        if gen_script.exists():
            subprocess.run(
                [sys.executable, str(gen_script), "--root", str(root), "--output", str(registry_path)],
                check=True, capture_output=True, timeout=30,
            )
    if registry_path.exists():
        return yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    return {}


def _run_audit_subprocess(root: Path) -> dict:
    """Wywołuje skill_audit i heos_lint, zwraca podsumowanie."""
    out: dict = {}
    # v1.2: tools/, v1.1: 03-quality/
    audit_script = root / "tools" / "skill_audit.py"
    if not audit_script.exists():
        audit_script = root / "03-quality" / "skill_audit.py"  # backward-compat
    if audit_script.exists():
        try:
            r = subprocess.run(
                [sys.executable, str(audit_script), str(root), "--quiet"],
                capture_output=True, text=True, timeout=60,
            )
            for line in r.stdout.splitlines():
                if "Zbadane Skills:" in line:
                    out["audit_total"] = int(line.split(":")[-1].strip())
                # v1.2 format: "Schema: ✅ 3 PASS | ⚠️  0 WARN | ❌ 1 FAIL"
                if "Schema:" in line and "PASS" in line:
                    import re
                    m = re.search(r"(\d+)\s*PASS", line)
                    if m:
                        out["audit_pass"] = int(m.group(1))
                    m = re.search(r"(\d+)\s*WARN", line)
                    if m:
                        out["audit_warn"] = int(m.group(1))
                    m = re.search(r"(\d+)\s*FAIL", line)
                    if m:
                        out["audit_fail"] = int(m.group(1))
                # v1.1 format: "PASS (kompletne):  3"
                if "PASS (kompletne):" in line:
                    out["audit_pass"] = int(line.split(":")[-1].strip())
                if "WARN" in line and "%" in line and "Schema:" not in line:
                    out["audit_warn"] = int(line.split(":")[-1].strip().split()[0])
                if "FAIL" in line and "%" in line and "Schema:" not in line:
                    out["audit_fail"] = int(line.split(":")[-1].strip().split()[0])
        except subprocess.TimeoutExpired:
            out["audit_error"] = "timeout"
    return out


def _run_lint_subprocess(root: Path) -> dict:
    """Wywołuje heos_lint, zwraca podsumowanie."""
    out: dict = {}
    lint_script = root / "tools" / "heos_lint.py"
    if not lint_script.exists():
        lint_script = root / "03-quality" / "heos_lint.py"  # backward-compat
    if lint_script.exists():
        try:
            r = subprocess.run(
                [sys.executable, str(lint_script), str(root)],
                capture_output=True, text=True, timeout=60,
            )
            for line in r.stdout.splitlines():
                if "ERROR:" in line:
                    import re
                    m = re.search(r"❌ ERROR:\s*(\d+)", line)
                    if m:
                        out["lint_error"] = int(m.group(1))
                if "WARN:" in line:
                    import re
                    m = re.search(r"⚠️\s*WARN:\s*(\d+)", line)
                    if m:
                        out["lint_warn"] = int(m.group(1))
                if "INFO:" in line:
                    import re
                    m = re.search(r"ℹ️\s*INFO:\s*(\d+)", line)
                    if m:
                        out["lint_info"] = int(m.group(1))
        except subprocess.TimeoutExpired:
            out["lint_error_text"] = "timeout"
    return out


def _render_markdown(stats: dict) -> str:
    """Generuje treść STATUS.md."""
    now = stats["generated_at"]
    version = stats["heos_version"]
    total = stats["artifacts_total"]
    by_type = stats["artifacts_by_type"]
    last_commit = stats.get("last_commit", {})
    audit = stats.get("audit", {})
    lint = stats.get("lint", {})
    templates = stats["templates_count"]
    tools = stats["tools_count"]
    migration = stats["migration_count"]
    backup = stats.get("backup_status", "not present")

    lines = [
        "# HEOS — STATUS",
        "",
        f"**Wygenerowano:** {now}  ",
        f"**Wersja HEOS:** `{version}`  ",
        f"**Auto-generowany:** ✅ (z `tools/generate_status.py`)",
        "",
        "---",
        "",
        "## Artefakty",
        "",
        f"Łącznie: **{total}**",
        "",
        "| Typ | Liczba |",
        "|---|---|",
    ]
    for t in ["skill", "adr", "lessons", "checklist", "playbook"]:
        n = by_type.get(t, 0)
        if n > 0:
            lines.append(f"| {t} | {n} |")

    lines.extend([
        "",
        "## Jakość",
        "",
        f"- **Skill audit:** {audit.get('audit_pass', '?')} PASS / {audit.get('audit_warn', '?')} WARN / {audit.get('audit_fail', '?')} FAIL (z {audit.get('audit_total', '?')} zbadanych)",
        f"- **HEOS lint:** {lint.get('lint_error', 0)} ERROR / {lint.get('lint_warn', 0)} WARN / {lint.get('lint_info', 0)} INFO",
        "",
        "## Struktura",
        "",
        f"- **Templates:** {templates} (`HEOS/templates/`)",
        f"- **Tools:** {tools} (`HEOS/tools/`)",
        f"- **Migration infra:** {migration} (`HEOS/heos-migration/`)",
        f"- **Backup:** {backup}",
        "",
        "## Git",
        "",
    ])
    if last_commit:
        lines.append(f"- **Ostatni commit:** `{last_commit.get('hash', '?')[:8]}` — {last_commit.get('subject', '?')}")
        lines.append(f"  - Data: {last_commit.get('date', '?')}")
    else:
        lines.append("- **Ostatni commit:** (brak danych git)")

    tags = stats.get("git_tags", [])
    if tags:
        lines.append(f"- **Tagi:** {', '.join(tags)}")

    lines.extend([
        "",
        "---",
        "",
        "_Nie edytuj ręcznie. Wygeneruj ponownie:_",
        "```bash",
        "python3 HEOS/tools/generate_status.py",
        "```",
    ])
    return "\n".join(lines) + "\n"


def _check_backup() -> str:
    """Sprawdza czy jest backup zgodny z v1.2 (heos-pre-v1.2-*.tar.gz)."""
    backup_glob = Path.home() / "hermes-backups" / "heos-pre-v1.2-*.tar.gz"
    backups = list(backup_glob.parent.glob("heos-pre-v1.2-*.tar.gz"))
    if not backups:
        return "❌ brak (`~/hermes-backups/heos-pre-v1.2-*.tar.gz` nie istnieje)"
    latest = max(backups, key=lambda p: p.stat().st_mtime)
    size_mb = latest.stat().st_size / (1024 * 1024)
    return f"✅ {latest.name} ({size_mb:.1f} MB)"


def generuj_status(root: Path, output: Path) -> dict:
    """Generuje STATUS.md. Zwraca statystyki."""
    registry = _registry_or_generate(root)
    artifacts = registry.get("artifacts", {})
    by_type = {t: len(v) for t, v in artifacts.items()}
    total = sum(by_type.values())
    tags = _git_tags(root)
    version = _heos_version(root, tags)
    last_commit = _git_last_commit(root)
    audit = _run_audit_subprocess(root)
    lint = _run_lint_subprocess(root)
    backup = _check_backup()

    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "heos_version": version,
        "artifacts_total": total,
        "artifacts_by_type": by_type,
        "last_commit": last_commit,
        "git_tags": tags,
        "audit": audit,
        "lint": lint,
        "templates_count": _count_files(root / "templates", "*"),
        "tools_count": _count_files(root / "tools", "*"),
        "migration_count": _count_files(root / "heos-migration", "*") if (root / "heos-migration").is_dir() else 0,
        "backup_status": backup,
    }
    content = _render_markdown(stats)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Generuj STATUS.md dla HEOS")
    parser.add_argument("--root", default=str(HEOS_ROOT_DEFAULT), help="Katalog HEOS")
    parser.add_argument("--output", default=str(OUTPUT_DEFAULT), help="Plik wyjściowy")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not root.is_dir():
        print(f"❌ Katalog nie istnieje: {root}", file=sys.stderr)
        return 2
    stats = generuj_status(root, output)
    print(f"✅ Wygenerowano STATUS.md: {output}")
    print(f"   Wersja HEOS: {stats['heos_version']}")
    print(f"   Artefakty: {stats['artifacts_total']} ({stats['artifacts_by_type']})")
    print(f"   Templates: {stats['templates_count']}, Tools: {stats['tools_count']}, Migration: {stats['migration_count']}")
    print(f"   Backup: {stats['backup_status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

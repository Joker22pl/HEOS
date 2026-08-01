"""Regression tests for HEOS pre-rollout quality gates."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import generate_status
import skill_audit

TOOLS_DIR = Path(__file__).resolve().parent
HEOS_ROOT = TOOLS_DIR.parent


def _write_skill(path: Path, *, with_code: bool = True) -> None:
    code = "```bash\necho ok\n```" if with_code else "No executable example."
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""---
type: skill
id: skill-{path.parent.name if path.name == 'SKILL.md' else path.stem}
name: {path.parent.name if path.name == 'SKILL.md' else path.stem}
title: Test Skill
status: draft
owner: gaja
created_at: '2026-07-31'
updated_at: '2026-07-31'
review_due: '2027-01-31'
version: 0.1.0
heos_standard_version: '1.2'
tags: [test]
related: []
quality_schema: pending
quality_technical: pending
quality_operational: unmeasured
---
# Test Skill
## Cel
Test.
## Zakres
Test.
## Kiedy używać
- Test.
## Kiedy nie używać
- Test.
## Workflow
1. Test.
## Przykłady
{code}
## Lessons Learned
- Test.
""",
        encoding="utf-8",
    )


def test_cli_technical_failure_returns_nonzero(tmp_path: Path) -> None:
    _write_skill(tmp_path / "skills" / "broken.md", with_code=False)
    result = subprocess.run(
        [sys.executable, str(TOOLS_DIR / "skill_audit.py"), str(tmp_path), "--level", "technical", "--quiet"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "Technical: ✅ 0 PASS | ❌ 1 FAIL" in result.stdout


def test_heos_audit_discovers_all_flat_and_directory_skills(tmp_path: Path) -> None:
    _write_skill(tmp_path / "skills" / "flat.md")
    _write_skill(tmp_path / "skills" / "directory" / "SKILL.md")
    reports = skill_audit.audytuj_katalog(tmp_path)
    assert {r.path.relative_to(tmp_path).as_posix() for r in reports} == {
        "skills/flat.md",
        "skills/directory/SKILL.md",
    }


def test_heos_current_inventory_audits_all_eight_skills() -> None:
    reports = skill_audit.audytuj_katalog(HEOS_ROOT)
    assert len(reports) == 8


def test_version_selection_uses_semver_not_lexical_order(tmp_path: Path) -> None:
    assert generate_status._heos_version(tmp_path, ["v1.6.9", "v1.6.13", "v1.5.5"]) == "v1.6.13"


def test_current_repository_version_is_latest_semver_tag() -> None:
    """
    Repozytorium musi zgłaszać aktualnie NAJWYŻSZY SemVer tag jako wersję HEOS.
    Poprzednia wersja tego testu hardkodowała 'v1.6.13' — pękł przy każdym nowym tagu.
    Fix: wylicz oczekiwaną wartość z posortowanych SemVer tagów (jak sama
    implementacja `generate_status._heos_version`), bez hardcoded `latest`.
    """
    tags = generate_status._git_tags(HEOS_ROOT)
    assert tags, "Brak tagów git w repo — nie da się zweryfikować wersji."

    def semver_key(tag: str) -> tuple[int, ...]:
        # strip leading 'v'
        body = tag[1:] if tag.startswith("v") else tag
        return tuple(int(x) for x in body.split("."))

    expected = max(tags, key=semver_key)
    actual = generate_status._heos_version(HEOS_ROOT, tags)
    assert actual == expected, (
        f"_heos_version powinien zwrócić najwyższy SemVer tag ({expected}), "
        f"dostał {actual}."
    )


def test_ci_preserves_pytest_failure_status() -> None:
    workflow = (HEOS_ROOT / ".github" / "workflows" / "lint.yml").read_text(encoding="utf-8")
    assert "pytest --tb=long -v" in workflow
    assert "| tail -50" not in workflow


def test_ci_does_not_ignore_update_quality_drift() -> None:
    workflow = (HEOS_ROOT / ".github" / "workflows" / "lint.yml").read_text(encoding="utf-8")
    assert "tools/update_quality.py || true" not in workflow


def test_weekly_report_propagates_failed_audit(monkeypatch) -> None:
    import weekly_report

    results = iter([
        {"pass": 7, "warn": 0, "fail": 1, "total": 8, "returncode": 1},
        {"pass": 120, "warn": 0, "fail": 0, "total": 120, "returncode": 0},
    ])
    monkeypatch.setattr(weekly_report, "_run_audit", lambda _target: next(results))
    monkeypatch.setattr(sys, "argv", ["weekly_report.py"])
    assert weekly_report.main() == 1


def test_weekly_report_runtime_profile_findings_are_advisory(monkeypatch) -> None:
    import weekly_report

    results = iter([
        {"pass": 8, "warn": 0, "fail": 0, "total": 8, "returncode": 0},
        {"pass": 112, "warn": 0, "fail": 11, "total": 123, "returncode": 1},
    ])
    monkeypatch.setattr(weekly_report, "_run_audit", lambda _target: next(results))
    monkeypatch.setattr(sys, "argv", ["weekly_report.py"])
    assert weekly_report.main() == 0


def test_weekly_report_calls_all_level_strict(monkeypatch, tmp_path: Path) -> None:
    import weekly_report

    captured: dict[str, list[str]] = {}

    class Result:
        returncode = 0
        stdout = "Zbadane Skills: 1\nSchema: ✅ 1 PASS | ⚠️  0 WARN | ❌ 0 FAIL\n"
        stderr = ""

    def fake_run(command, **kwargs):
        captured["command"] = command
        return Result()

    monkeypatch.setattr(weekly_report.subprocess, "run", fake_run)
    stats = weekly_report._run_audit(tmp_path)
    assert captured["command"][-4:] == ["--level", "all", "--strict", "--quiet"]
    assert stats["returncode"] == 0

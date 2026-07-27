"""
Testy jednostkowe dla heos_lint.py v1.2.

Backward-compat: pliki v1.1 (bez nowych pól) → WARN, nie ERROR.
Nowe pliki v1.2 (z pełnymi metadanymi) → bez findings (jeśli poprawne).
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from heos_lint import lint, Finding, DOZWOLONE_STATUSY


def _write_skill(tmp: Path, name: str, content: str) -> Path:
    """Helper — zapisz plik Skill w katalogu HEOS-typu."""
    p = tmp / "02-artifacts" / "skills" / name / "SKILL.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _write_adr(tmp: Path, num: int, title: str, content: str) -> Path:
    p = tmp / "02-artifacts" / "decision-records" / f"ADR-{num:03d}-{title}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def test_empty_dir_no_findings():
    """Pusty katalog HEOS → 0 findings."""
    with tempfile.TemporaryDirectory() as tmp:
        findings = lint(Path(tmp))
        assert findings == [], f"Oczekiwano 0 findings, dostałem: {findings}"


def test_v11_skill_backward_compatible_warn():
    """Skill v1.1 (bez type, brak pełnych metadanych) → WARN MISSING_FIELDS, nie ERROR."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _write_skill(tmp, "my-skill", """---
name: my-skill
description: Test skill
status: active
domain: cross-cutting
---

# My Skill

## Cel
Test
""")
        findings = lint(tmp)
        errors = [f for f in findings if f.severity == "ERROR"]
        warns = [f for f in findings if f.severity == "WARN"]
        assert errors == [], f"v1.1 Skill nie powinien mieć ERROR: {errors}"
        # Powinien mieć WARN o brakujących polach
        assert any(f.code == "MISSING_FIELDS" for f in warns), f"Oczekiwano WARN MISSING_FIELDS, dostałem: {warns}"


def test_v12_skill_full_metadata_no_findings():
    """Skill v1.2 z pełnymi metadanymi → brak ERROR (mogą być INFO o orphanach)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _write_skill(tmp, "good-skill", """---
type: skill
id: skill-good-skill
name: good-skill
title: Good Skill
status: accepted
owner: gaja
created_at: "2026-07-23"
updated_at: "2026-07-23"
review_due: "2027-01-23"
version: "1.0.0"
heos_standard_version: "1.2"
tags: [cross-cutting]
related: []
quality_schema: pass
quality_technical: pending
quality_operational: unmeasured
---

# Good Skill
""")
        findings = lint(tmp)
        errors = [f for f in findings if f.severity == "ERROR"]
        assert errors == [], f"v1.2 Skill z pełnymi metadanymi nie powinien mieć ERROR: {errors}"


def test_v11_adr_accepted_status_backward_compat():
    """ADR v1.1 (Nygard) z status 'Accepted' → nie ERROR (alias działa)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _write_adr(tmp, 1, "test", """# ADR-001: Test

| Pole | Wartość |
|---|---|
| **Status** | Accepted |
| **Data** | 2026-07-23 |
| **Autor** | Gaja |

## Kontekst
Test context
""")
        findings = lint(tmp)
        errors = [f for f in findings if f.severity == "ERROR"]
        assert errors == [], f"v1.1 ADR 'Accepted' nie powinien mieć ERROR: {errors}"


def test_invalid_status_is_error():
    """Nieznany status → ERROR."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _write_skill(tmp, "bad", """---
type: skill
id: skill-bad
name: bad
title: Bad
status: INVALID_STATUS
owner: gaja
created_at: "2026-07-23"
updated_at: "2026-07-23"
review_due: "2027-01-23"
version: "1.0.0"
heos_standard_version: "1.2"
tags: []
---

# Bad
""")
        findings = lint(tmp)
        errors = [f for f in findings if f.severity == "ERROR"]
        assert any(f.code == "INVALID_STATUS" for f in errors), f"Oczekiwano ERROR INVALID_STATUS: {errors}"


def test_broken_ref_is_error():
    """related do nieistniejącego ADR → ERROR BROKEN_REF."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _write_adr(tmp, 1, "real", """# ADR-001: Real

| Pole | Wartość |
|---|---|
| **Status** | Accepted |
| **Data** | 2026-07-23 |
""")
        # Skill cytujący ADR-999 (nie istnieje)
        _write_skill(tmp, "broken", """---
type: skill
id: skill-broken
name: broken
title: Broken
status: accepted
owner: gaja
created_at: "2026-07-23"
updated_at: "2026-07-23"
review_due: "2027-01-23"
version: "1.0.0"
heos_standard_version: "1.2"
tags: []
related: [ADR-999]
---

# Broken
""")
        findings = lint(tmp)
        errors = [f for f in findings if f.severity == "ERROR"]
        assert any(f.code == "BROKEN_REF" for f in errors), f"Oczekiwano ERROR BROKEN_REF: {errors}"


def test_orphan_adr_info():
    """ADR bez cytowań → INFO ORPHAN_ADR (nie ERROR)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _write_adr(tmp, 1, "orphan", """# ADR-001: Orphan

| Pole | Wartość |
|---|---|
| **Status** | Accepted |
| **Data** | 2026-07-23 |
""")
        findings = lint(tmp)
        infos = [f for f in findings if f.severity == "INFO"]
        assert any(f.code == "ORPHAN_ADR" for f in infos), f"Oczekiwano INFO ORPHAN_ADR: {infos}"


def test_v11_skill_with_related_adrs_works():
    """Skill v1.1 z `related-adrs` (zamiast `related`) → nie powinien mieć BROKEN_REF dla istniejącego ADR."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _write_adr(tmp, 1, "real", """# ADR-001: Real

| Pole | Wartość |
|---|---|
| **Status** | Accepted |
| **Data** | 2026-07-23 |
""")
        _write_skill(tmp, "v11-skill", """---
name: v11-skill
status: active
related-adrs: [ADR-001]
---

# V11 Skill
""")
        findings = lint(tmp)
        broken = [f for f in findings if f.code == "BROKEN_REF"]
        assert broken == [], f"v1.1 Skill z related-adrs do istniejącego ADR nie powinien mieć BROKEN_REF: {broken}"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))

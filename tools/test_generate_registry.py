"""
Testy jednostkowe dla generate_registry.py.

Sprawdza:
- Generuje .registry.yaml w HEOS root
- Zawiera wszystkie 7+ artefaktów (Skills + ADR)
- Status, tagi, id poprawne
- Backward-compat z v1.1 (ADR w formacie Nygard)
"""
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_registry


def _write_skill(tmp: Path, path: str, content: str) -> None:
    p = tmp / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_empty_dir_generates_empty_registry():
    """Pusty katalog → registry z 0 artefaktami."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        out = tmp / ".registry.yaml"
        stats = generate_registry.generuj_registry(tmp, out)
        assert stats["total"] == 0
        assert out.exists()
        r = yaml.safe_load(out.read_text())
        assert r["_meta"]["total_artifacts"] == 0


def test_v11_skills_in_01_domains_counted():
    """Skills w 01-domains/X/skills/ → type=skill, domain=X."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _write_skill(tmp, "01-domains/embedded/skills/test-skill/SKILL.md", """---
name: test-skill
status: active
---

# Test
""")
        out = tmp / ".registry.yaml"
        stats = generate_registry.generuj_registry(tmp, out)
        assert stats["total"] == 1
        assert stats["by_type"].get("skill") == 1
        r = yaml.safe_load(out.read_text())
        skill = r["artifacts"]["skill"][0]
        assert skill["type"] == "skill"
        assert skill["tags"] == ["embedded"]


def test_v11_adr_parsed_correctly():
    """ADR v1.1 (Nygard) → type=adr, id=adr-NNN, status z tabelki."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _write_skill(tmp, "02-artifacts/decision-records/ADR-001-test.md", """# ADR-001: Test ADR

| Pole | Wartość |
|---|---|
| **Status** | Accepted |
| **Data** | 2026-07-23 |
| **Autor** | Gaja |

## Kontekst
Test
""")
        out = tmp / ".registry.yaml"
        stats = generate_registry.generuj_registry(tmp, out)
        assert stats["by_type"].get("adr") == 1
        r = yaml.safe_load(out.read_text())
        adr = r["artifacts"]["adr"][0]
        assert adr["id"] == "adr-001"
        assert adr["status"] == "accepted"
        assert adr["type"] == "adr"


def test_v12_skill_with_full_metadata():
    """Skill v1.2 z pełnymi metadanymi → wszystkie pola w registry."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _write_skill(tmp, "02-artifacts/skills/full-skill/SKILL.md", """---
type: skill
id: skill-full-skill
name: full-skill
title: Full Skill
status: accepted
owner: gaja
created_at: "2026-07-23"
updated_at: "2026-07-23"
review_due: "2027-01-23"
version: "1.0.0"
heos_standard_version: "1.2"
tags: [embedded, esp32]
related: [ADR-001]
---

# Full
""")
        out = tmp / ".registry.yaml"
        stats = generate_registry.generuj_registry(tmp, out)
        r = yaml.safe_load(out.read_text())
        skill = r["artifacts"]["skill"][0]
        assert skill["id"] == "skill-full-skill"
        assert skill["title"] == "Full Skill"
        assert skill["heos_standard_version"] == "1.2"
        assert "esp32" in skill["tags"]


def test_excludes_templates_and_migration():
    """Pliki w templates/ i heos-migration/ NIE są w registry."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # Skill w templates (szablon)
        _write_skill(tmp, "templates/skill.md", """---
type: skill
name: skill-template
status: draft
---
# Template
""")
        # Skill w heos-migration
        _write_skill(tmp, "heos-migration/plan.md", """---
type: plan
name: migration-plan
status: draft
---
# Plan
""")
        out = tmp / ".registry.yaml"
        stats = generate_registry.generuj_registry(tmp, out)
        assert stats["total"] == 0, f"Pliki w templates/heos-migration nie powinny być w registry: {stats}"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))

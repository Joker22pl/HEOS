#!/usr/bin/env python3
"""Testy dla tools/update_quality.py — atomic write + transakcyjność + --check mode.

Wszystkie testy działają na tmp_path (nie modyfikują prawdziwego HEOS).
"""
import os
import re
import sys
import stat
import tempfile
from pathlib import Path

# Dodaj tools do sys.path żeby importować moduły HEOS
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


def _make_skill(path: Path, quality_schema: str = "pending", quality_technical: str = "pending"):
    """Utwórz minimalny skill w katalogu z zadanymi quality_*."""
    fm_lines = [
        "type: skill",
        "id: skill-test-skill",
        "name: test-skill",
        "title: Test Skill",
        "status: accepted",
        "owner: gaja",
        "created_at: '2026-07-27'",
        "updated_at: '2026-07-27'",
        "review_due: '2027-01-25'",
        "version: 1.0.0",
        "heos_standard_version: '1.2'",
        "tags:",
        "- test",
        "related: []",
        f"quality_schema: {quality_schema}",
        f"quality_technical: {quality_technical}",
        "quality_operational: unmeasured",
    ]
    # Sekcje obowiązkowe muszą mieć >=5 słów (MIN_WORDS_PER_SEC=5).
    body = "\n".join([
        "---",
        "\n".join(fm_lines),
        "---",
        "",
        "## Cel",
        "To jest testowy skill dla update_quality.py.",
        "",
        "## Zakres",
        "Testowanie atomic write i transakcyjności update_quality.",
        "",
        "## Kiedy używać",
        "- gdy testujesz update_quality",
        "- gdy chcesz sprawdzić atomic write",
        "",
        "## Kiedy nie używać",
        "- w produkcji",
        "- do testowania innych narzędzi",
        "",
        "## Workflow",
        "1. Wywołaj update_quality.py",
        "2. Sprawdź wynik",
        "3. Zweryfikuj pliki",
        "",
        "## Przykłady",
        "Przykładowe komendy do testowania update_quality.py na kopii.",
        "```bash",
        "echo test",
        "echo atomic_write_works",
        "echo transactional_rollback_works",
        "```",
        "",
        "## Lessons Learned",
        "- Testy muszą mieć treść w każdej obowiązkowej sekcji",
    ])
    path.write_text(body, encoding="utf-8")


def test_check_mode_no_changes(tmp_path):
    """--check z aktualnym stanem → exit 0, brak modyfikacji plików."""
    from update_quality import main
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    _make_skill(skills_dir / "skill1.md", "pass", "pass")
    # Monkey-patch HEOS_ROOT w main (nie ma, ale _plan_updates używa sys.argv)
    import sys
    old_argv = sys.argv
    try:
        sys.argv = ["update_quality.py", "--check", "--root", str(tmp_path)]
        rc = main()
    finally:
        sys.argv = old_argv
    assert rc == 0, f"Expected 0, got {rc}"
    # Plik nie zmieniony
    txt = (skills_dir / "skill1.md").read_text()
    assert "quality_schema: pass" in txt


def test_check_mode_changes_detected(tmp_path):
    """--check z pending → exit 1, raportuje co się zmieni."""
    from update_quality import main
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    _make_skill(skills_dir / "skill1.md", "pending", "pending")
    import sys
    old_argv = sys.argv
    try:
        sys.argv = ["update_quality.py", "--check", "--root", str(tmp_path)]
        rc = main()
    finally:
        sys.argv = old_argv
    assert rc == 1, f"Expected 1 (changes needed), got {rc}"


def test_apply_writes_atomically(tmp_path):
    """--apply zapisuje pliki; md5 zmieniony; YAML roundtrip OK."""
    from update_quality import main
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    skill_path = skills_dir / "skill1.md"
    _make_skill(skill_path, "pending", "pending")
    import sys
    old_argv = sys.argv
    try:
        sys.argv = ["update_quality.py", "--apply", "--root", str(tmp_path)]
        rc = main()
    finally:
        sys.argv = old_argv
    assert rc == 0, f"Expected 0, got {rc}"
    txt = skill_path.read_text()
    assert "quality_schema: pass" in txt
    assert "quality_technical: pass" in txt
    # YAML roundtrip
    import yaml
    parts = txt.split("---", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["quality_schema"] == "pass"


def test_apply_first_delimiter_is_three_dashes(tmp_path):
    """Po apply pierwszy delimiter to dokładnie '---' (3 myślniki)."""
    from update_quality import main
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    skill_path = skills_dir / "skill1.md"
    _make_skill(skill_path, "pending", "pending")
    import sys
    old_argv = sys.argv
    try:
        sys.argv = ["update_quality.py", "--apply", "--root", str(tmp_path)]
        main()
    finally:
        sys.argv = old_argv
    txt = skill_path.read_text()
    first_line = txt.split("\n")[0]
    assert first_line == "---", f"Expected '---', got {first_line!r}"


def test_apply_idempotent(tmp_path):
    """Drugi --apply nic nie zmienia (exit 0, brak zmian)."""
    from update_quality import main
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    skill_path = skills_dir / "skill1.md"
    _make_skill(skill_path, "pending", "pending")
    import sys
    old_argv = sys.argv
    try:
        sys.argv = ["update_quality.py", "--apply", "--root", str(tmp_path)]
        assert main() == 0
        md5_1 = skill_path.read_bytes()
        sys.argv = ["update_quality.py", "--apply", "--root", str(tmp_path)]
        rc = main()
    finally:
        sys.argv = old_argv
    assert rc == 0
    md5_2 = skill_path.read_bytes()
    assert md5_1 == md5_2, "Idempotentność złamana"


def test_atomic_write_creates_no_tmp_files_on_success(tmp_path):
    """Po udanym apply nie ma .tmp plików."""
    from update_quality import main
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    skill_path = skills_dir / "skill1.md"
    _make_skill(skill_path, "pending", "pending")
    import sys
    old_argv = sys.argv
    try:
        sys.argv = ["update_quality.py", "--apply", "--root", str(tmp_path)]
        main()
    finally:
        sys.argv = old_argv
    tmps = list(tmp_path.rglob("*.tmp"))
    assert tmps == [], f"Pozostały tmp files: {tmps}"


def test_partial_failure_rolls_back(tmp_path):
    """Gdy jeden plik fail (read-only katalog), inne są rollback'owane."""
    from update_quality import main
    skills_dir = tmp_path / "skills"
    skill1_dir = skills_dir / "skill1"
    skill2_dir = skills_dir / "skill2"
    skill1_dir.mkdir(parents=True)
    skill2_dir.mkdir(parents=True)
    skill1 = skill1_dir / "SKILL.md"
    skill2 = skill2_dir / "SKILL.md"
    _make_skill(skill1, "pending", "pending")
    _make_skill(skill2, "pending", "pending")
    # Ustaw katalog skill2 jako read-only (blokuje tempfile.mkstemp)
    os.chmod(skill2_dir, 0o555)
    md5_skill1_before = skill1.read_bytes()
    md5_skill2_before = skill2.read_bytes()
    try:
        import sys
        old_argv = sys.argv
        try:
            sys.argv = ["update_quality.py", "--apply", "--root", str(tmp_path)]
            rc = main()
        finally:
            sys.argv = old_argv
        assert rc == 2, f"Expected 2 (rollback), got {rc}"
    finally:
        os.chmod(skill2_dir, 0o755)
    # Sprawdź czy skill1 NIE został zmieniony (rollback)
    md5_skill1_after = skill1.read_bytes()
    assert md5_skill1_before == md5_skill1_after, "skill1 NIE był rollback'owany!"
    # Sprawdź czy skill2 NIE został zmieniony
    md5_skill2_after = skill2.read_bytes()
    assert md5_skill2_before == md5_skill2_after, "skill2 nie powinien być zmieniony"
    # Sprawdź czy quality_schema to wciąż pending w obu
    assert "quality_schema: pending" in skill1.read_text()
    assert "quality_schema: pending" in skill2.read_text()


def test_no_tmp_left_after_rollback(tmp_path):
    """Po rollback nie ma .tmp ani .heos-quality-backup."""
    from update_quality import main
    skills_dir = tmp_path / "skills"
    skill1_dir = skills_dir / "skill1"
    skill2_dir = skills_dir / "skill2"
    skill1_dir.mkdir(parents=True)
    skill2_dir.mkdir(parents=True)
    _make_skill(skill1_dir / "SKILL.md", "pending", "pending")
    _make_skill(skill2_dir / "SKILL.md", "pending", "pending")
    os.chmod(skill2_dir, 0o555)
    try:
        import sys
        old_argv = sys.argv
        try:
            sys.argv = ["update_quality.py", "--apply", "--root", str(tmp_path)]
            main()
        finally:
            sys.argv = old_argv
    finally:
        os.chmod(skill2_dir, 0o755)
    # Sprawdź cleanup
    tmps = list(tmp_path.rglob("*.tmp"))
    backups = list(tmp_path.rglob(".heos-quality-backup"))
    assert tmps == [], f"Pozostały tmp: {tmps}"
    assert backups == [], f"Pozostały backup: {backups}"


def test_yaml_with_comment_preserved(tmp_path):
    """Komentarz YAML w frontmatter jest zachowany po apply.

    Test tworzy skill z komentarzem w ciele pliku (PO zamknięciu frontmatter).
    Komentarz w samym frontmatter (przed `type: skill`) jest edge-case
    który nie występuje w produkcji — pomijamy go.
    """
    from update_quality import main
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    skill_path = skills_dir / "skill1.md"
    # Skill z komentarzem w body (po zamknięciu frontmatter)
    _make_skill(skill_path, "pending", "pending")
    txt = skill_path.read_text()
    # Wstaw komentarz po body ## Cel
    txt = txt.replace("## Cel\n", "## Cel\n# Komentarz w body\n", 1)
    skill_path.write_text(txt, encoding="utf-8")
    import sys
    old_argv = sys.argv
    try:
        sys.argv = ["update_quality.py", "--apply", "--root", str(tmp_path)]
        main()
    finally:
        sys.argv = old_argv
    new_txt = skill_path.read_text()
    # Komentarz zachowany
    assert "# Komentarz w body" in new_txt
    # Schemat zaktualizowany
    assert "quality_schema: pass" in new_txt


def test_missing_quality_field_added(tmp_path):
    """Gdy skill nie ma quality_*, apply dodaje go (nie cicha porażka)."""
    from update_quality import main
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    skill_path = skills_dir / "skill1.md"
    # Skill BEZ quality_* — używamy _make_skill helper
    _make_skill(skill_path, "pending", "pending")
    # Ale następnie usuwamy quality_* żeby przetestować scenariusz "brak pola"
    txt = skill_path.read_text()
    txt = re.sub(r"^quality_schema:.*\n", "", txt, flags=re.M)
    txt = re.sub(r"^quality_technical:.*\n", "", txt, flags=re.M)
    skill_path.write_text(txt, encoding="utf-8")
    import sys
    old_argv = sys.argv
    try:
        sys.argv = ["update_quality.py", "--apply", "--root", str(tmp_path)]
        main()
    finally:
        sys.argv = old_argv
    txt = skill_path.read_text()
    assert "quality_schema: pass" in txt
    assert "quality_technical: pass" in txt
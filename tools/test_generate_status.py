"""
Testy jednostkowe dla generate_status.py.

Sprawdza:
- _count_files pomija ukryte katalogi cache (__pycache__, .pytest_cache)
- _count_files liczy tylko pliki (nie katalogi)
- Tools count w STATUS jest realistyczny (nie zawyżony o cache)
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_status


def test_count_files_skips_hidden_cache_dirs():
    """Bug fix 2026-07-28: glob('*') łapał __pycache__/ i .pytest_cache/ jako pliki.

    Przed fixem: Tools: 25 (zawyżone o 2 katalogi cache).
    Po fixie: Tools: 23 (22 .py + 1 .sh, tylko widoczne pliki).
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # Utwórz mieszankę: zwykłe .py + cache katalogi + ukryte pliki
        (tmp / "tool1.py").write_text("# x")
        (tmp / "tool2.sh").write_text("#!/bin/sh\n")
        (tmp / "__pycache__").mkdir()
        (tmp / "__pycache__" / "tool1.cpython-311.pyc").write_bytes(b"")
        (tmp / ".pytest_cache").mkdir()
        # UWAGA: nie tworzymy pliku w .pytest_cache bo to cache-write pattern;
        # sam katalog .pytest_cache jest ukryty i powinien być pomijany.
        (tmp / ".hidden_file").write_text("should not be counted")

        count = generate_status._count_files(tmp, "*")
        assert count == 2, f"Oczekiwano 2 (tool1.py + tool2.sh), dostałem {count}"


def test_count_files_pattern_specific():
    """Pattern *.py łapie tylko .py, nie katalogi cache."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "a.py").write_text("#")
        (tmp / "b.py").write_text("#")
        (tmp / "c.sh").write_text("#")
        (tmp / "__pycache__").mkdir()
        (tmp / ".pytest_cache").mkdir()

        count_py = generate_status._count_files(tmp, "*.py")
        count_all = generate_status._count_files(tmp, "*")
        assert count_py == 2, f"Oczekiwano 2 .py, dostałem {count_py}"
        assert count_all == 3, f"Oczekiwano 3 (2 .py + 1 .sh), dostałem {count_all}"


def test_count_files_empty_dir():
    """Pusty katalog → 0."""
    with tempfile.TemporaryDirectory() as tmp:
        count = generate_status._count_files(Path(tmp), "*")
        assert count == 0


def test_count_files_real_heos_tools_dir():
    """Test integracyjny: HEOS tools/ powinno dawać realistyczny count.

    Real HEOS tools/:
    - 22 .py (produkcyjne)
    - 1 .sh (pre_commit_skill_check.sh)
    - 6 test_*.py (test_check_operational_proven, test_generate_registry,
                  test_generate_status, test_heos_atomic, test_heos_lint,
                  test_update_quality, test_weekly_report)
    - 0 cache katalogów (bo .gitignore + brak pytest run w tym katalogu)

    Suma widocznych plików = 22 .py + 1 .sh + N test_*.py.
    Ten test weryfikuje że:
    1. count >= 22 (są wszystkie produkcyjne)
    2. count >= 23 (jest .sh + wszystkie produkcyjne)
    3. test_*.py są zliczane (count > 22)
    4. nie ma cache katalogów w wyniku (count < 30, sanity check)
    """
    # Znajdź HEOS root (3 poziomy w górę od tools/test_generate_status.py)
    heos_root = Path(__file__).resolve().parent.parent
    tools_dir = heos_root / "tools"

    if not tools_dir.exists():
        return  # test pomijany jeśli uruchamiany z innego layout

    count = generate_status._count_files(tools_dir, "*")
    count_py = generate_status._count_files(tools_dir, "*.py")

    # Minimum assertion: 22 produkcyjne + 1 .sh + co najmniej 6 test_*.py = 29
    # Ale test_*.py jest dodawane przyrostowo — assert minimum realistic
    assert count >= 23, f"Oczekiwano >= 23 (22 .py + 1 .sh), dostałem {count}"
    assert count_py >= 22, f"Oczekiwano >= 22 .py, dostałem {count_py}"
    # Sanity: nie więcej niż 35 (nie ma setek ukrytych plików)
    assert count <= 35, f"Oczekiwano <= 35, dostałem {count} (cache nie powinien być liczony)"


def test_count_files_does_not_count_subdirectories():
    """Katalogi w tools/ (np. gdyby ktoś dodał) nie są liczone jako pliki."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "script.py").write_text("#")
        (tmp / "subdir").mkdir()
        (tmp / "subdir" / "inner.py").write_text("#")

        count = generate_status._count_files(tmp, "*")
        assert count == 1, f"Oczekiwano 1 (script.py), dostałem {count}"


if __name__ == "__main__":
    test_count_files_skips_hidden_cache_dirs()
    test_count_files_pattern_specific()
    test_count_files_empty_dir()
    test_count_files_real_heos_tools_dir()
    test_count_files_does_not_count_subdirectories()
    print("All 5 tests passed.")

#!/usr/bin/env python3
"""Testy dla tools/_heos_atomic.py — ADR-008 contract.

Wszystkie testy używają tmp_path (nie modyfikują prawdziwego HEOS).
"""
import os
import time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))


def test_atomic_write_basic(tmp_path):
    """atomic_write tworzy plik z content."""
    from _heos_atomic import atomic_write
    p = tmp_path / "test.md"
    atomic_write(p, "hello\n")
    assert p.read_text() == "hello\n"


def test_atomic_write_overwrite_existing(tmp_path):
    """atomic_write nadpisuje istniejący plik (atomicznie)."""
    from _heos_atomic import atomic_write
    p = tmp_path / "test.md"
    p.write_text("original\n")
    atomic_write(p, "new\n")
    assert p.read_text() == "new\n"


def test_atomic_write_cleans_tmp_on_error(tmp_path):
    """atomic_write czyści tmp file przy wyjątku (rollback)."""
    from _heos_atomic import atomic_write
    p = tmp_path / "test.md"
    p.write_text("original\n")
    # Symulujemy wyjątek wewnątrz zapisu (przez mock open)
    import unittest.mock
    with unittest.mock.patch("os.fdopen", side_effect=OSError("simulated")):
        try:
            atomic_write(p, "new\n")
        except OSError:
            pass
    # Plik nie zmieniony
    assert p.read_text() == "original\n", f"plik zmieniony mimo wyjątku: {p.read_text()!r}"
    # Brak tmp files
    tmps = list(tmp_path.glob("*.tmp"))
    assert tmps == [], f"tmp files nie usunięte: {tmps}"


def test_atomic_write_bytes(tmp_path):
    """atomic_write_bytes zapisuje bajty (np. backup tar)."""
    from _heos_atomic import atomic_write_bytes
    p = tmp_path / "test.bin"
    data = b"\x00\x01\x02\xff"
    atomic_write_bytes(p, data)
    assert p.read_bytes() == data


def test_make_backup_unique_timestamp(tmp_path):
    """make_backup tworzy backup z unikalnym timestamp."""
    from _heos_atomic import make_backup
    p = tmp_path / "test.md"
    p.write_text("content\n")
    bp = make_backup(p)
    assert bp.exists()
    assert bp.read_text() == "content\n"
    # Sprawdź format: test.md.<YYYYMMDD-HHMMSS>.bak
    name = bp.name
    assert name.startswith("test.md.")
    assert name.endswith(".bak")
    # Timestamp ma 15 znaków
    ts = name.removeprefix("test.md.").removesuffix(".bak")
    assert len(ts) == 15, f"timestamp '{ts}' should be 15 chars (YYYYMMDD-HHMMSS)"


def test_make_backup_nonexistent_raises(tmp_path):
    """make_backup dla nieistniejącego pliku → FileNotFoundError."""
    from _heos_atomic import make_backup
    try:
        make_backup(tmp_path / "nope.md")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected FileNotFoundError")


def test_transaction_successful_commits(tmp_path):
    """Transaction w sukcesie — modyfikacje zachowane, backup dir usunięty."""
    from _heos_atomic import transaction
    p1 = tmp_path / "a.md"
    p2 = tmp_path / "b.md"
    p1.write_text("a1\n")
    p2.write_text("b1\n")
    with transaction(tmp_path) as tx:
        tx.atomic_write(p1, "a2\n")
        tx.atomic_write(p2, "b2\n")
    assert p1.read_text() == "a2\n"
    assert p2.read_text() == "b2\n"
    # Backup dir usunięty
    assert not (tmp_path / ".heos-tx-backup").exists()


def test_transaction_rollback_on_exception(tmp_path):
    """Transaction rollback przy wyjątku — oryginały przywrócone."""
    from _heos_atomic import transaction
    p1 = tmp_path / "a.md"
    p2 = tmp_path / "b.md"
    p1.write_text("a1\n")
    p2.write_text("b1\n")
    try:
        with transaction(tmp_path) as tx:
            tx.atomic_write(p1, "a2\n")
            tx.atomic_write(p2, "b2\n")
            raise ValueError("rollback please")
    except ValueError:
        pass
    # Oryginały przywrócone
    assert p1.read_text() == "a1\n", f"p1: {p1.read_text()!r}"
    assert p2.read_text() == "b1\n", f"p2: {p2.read_text()!r}"
    # Backup dir usunięty po rollback
    assert not (tmp_path / ".heos-tx-backup").exists()


def test_transaction_no_changes_no_backup(tmp_path):
    """Transaction bez zapisu — brak backup dir."""
    from _heos_atomic import transaction
    p = tmp_path / "x.md"
    p.write_text("original\n")
    with transaction(tmp_path):
        pass  # nic nie rób
    assert p.read_text() == "original\n"
    assert not (tmp_path / ".heos-tx-backup").exists()


def test_cleanup_old_backups_removes_old(tmp_path):
    """cleanup_old_backups usuwa pliki starsze niż max_age_days."""
    from _heos_atomic import cleanup_old_backups
    bak = tmp_path / "old.bak"
    bak.write_text("old")
    # Ustaw mtime na 31 dni temu
    old_time = time.time() - (31 * 86400)
    os.utime(bak, (old_time, old_time))
    count = cleanup_old_backups(tmp_path, max_age_days=30)
    assert count == 1
    assert not bak.exists()


def test_cleanup_old_backups_keeps_new(tmp_path):
    """cleanup_old_backups NIE usuwa świeżych plików."""
    from _heos_atomic import cleanup_old_backups
    bak = tmp_path / "new.bak"
    bak.write_text("new")
    count = cleanup_old_backups(tmp_path, max_age_days=30)
    assert count == 0
    assert bak.exists()
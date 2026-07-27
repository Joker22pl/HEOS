#!/usr/bin/env python3
"""HEOS atomic write contract (ADR-008).

Wspólne helpery do bezpiecznych zapisów plików w HEOS. Wszystkie narzędzia
HEOS które modyfikują pliki MUSZĄ używać tych helperów (nie write_text
bezpośrednio).

Funkcje:
- atomic_write(path, content): atomiczny zapis pliku tekstowego
  (tempfile + flush + fsync + os.replace)
- atomic_write_bytes(path, data): jak wyżej dla bajtów
- make_backup(path): tworzy .bak z timestamp (unikalna nazwa)
- TransactionContext: context manager dla transakcyjnych zapisów
  wielu plików (rollback przy wyjątku)
"""
from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def _atomic_write_inner(target: Path, write_fn) -> None:
    """Wewnętrzny helper: pisze write_fn(file) do tempfile, fsync, rename.

    write_fn(file_handle) → zapisuje do otwartego pliku.
    """
    target_dir = target.parent
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=str(target_dir),
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            write_fn(f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, target)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def atomic_write(path: Path, content: str) -> None:
    """Atomiczny zapis pliku tekstowego (ADR-008)."""
    target = Path(path)
    _atomic_write_inner(target, lambda f: f.write(content))


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Atomiczny zapis bajtów (np. backup tar.gz)."""
    target = Path(path)
    def write_bytes(f):
        f.buffer.write(data)
    _atomic_write_inner(target, write_bytes)


def make_backup(path: Path) -> Path:
    """Tworzy backup pliku z timestamp w nazwie.

    Zwraca ścieżkę do backupu. Format:
    <name>.<YYYYMMDD-HHMMSS>.bak (unikalny nawet przy wielu wywołaniach).

    Przykład:
        make_backup(Path('skills/foo.md'))
        → Path('skills/foo.20260727-143012.bak')
    """
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"Nie można zrobić backupu: {target} nie istnieje")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = target.with_name(f"{target.name}.{ts}.bak")
    # Handle kolizji (dwa backupy w tej samej sekundzie — rzadkie, ale możliwe)
    counter = 1
    while backup.exists():
        backup = target.with_name(f"{target.name}.{ts}-{counter}.bak")
        counter += 1
    # Czytaj oryginał binarnie (żeby nie modyfikować encoding)
    data = target.read_bytes()
    atomic_write_bytes(backup, data)
    return backup


@contextmanager
def transaction(root: Path):
    """Context manager dla transakcyjnych zapisów wielu plików.

    Wzorzec:
        with transaction(heos_root) as tx:
            tx.make_backup(file_path)
            tx.atomic_write(file_path, new_content)
        # przy wyjątku wewnątrz with: rollback wszystkich zmian

    Wszystkie pliki zmodyfikowane wewnątrz bloku są śledzone.
    Przy wyjściu z bloku (normalnie lub przez wyjątek) — backup
    directory jest usuwany (sukces) lub odtwarzany (rollback).

    Wymagania:
    - tx.atomic_write(path, content) — zapisuje i śledzi
    - tx.make_backup(path) — tworzy backup PRZED zapisem (opcjonalne,
      dla narzędzi które chcą zachować oryginał)
    """
    backup_dir = root / ".heos-tx-backup"
    modified: dict[Path, Path] = {}  # path → backup_path

    class Transaction:
        def atomic_write(self, path: Path, content: str) -> None:
            target = Path(path)
            if target not in modified:
                # Pierwszy zapis — tworzymy backup
                if target.exists():
                    bp = backup_dir / f"{target.relative_to(root).as_posix()}.bak"
                    bp.parent.mkdir(parents=True, exist_ok=True)
                    data = target.read_bytes()
                    atomic_write_bytes(bp, data)
                    modified[target] = bp
            # Zapis nowej treści
            atomic_write(target, content)

        def make_backup(self, path: Path) -> Path:
            target = Path(path)
            if not target.exists():
                raise FileNotFoundError(target)
            bp = backup_dir / f"{target.relative_to(root).as_posix()}.bak"
            bp.parent.mkdir(parents=True, exist_ok=True)
            data = target.read_bytes()
            atomic_write_bytes(bp, data)
            modified[target] = bp
            return bp

        def _cleanup_backup(self) -> None:
            """Usuń backup dir i wszystkie pliki."""
            if not backup_dir.exists():
                return
            for p in sorted(backup_dir.rglob("*"), reverse=True):
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    try:
                        p.rmdir()
                    except OSError:
                        pass
            if backup_dir.exists():
                try:
                    backup_dir.rmdir()
                except OSError:
                    pass

        def _rollback(self) -> None:
            """Przywróć zmienione pliki z backupów."""
            for original, backup in modified.items():
                if backup.exists():
                    data = backup.read_bytes()
                    atomic_write_bytes(original, data)

    tx = Transaction()
    try:
        yield tx
    except Exception:
        # Rollback: przywróć pliki z backupów
        tx._rollback()
        tx._cleanup_backup()
        raise
    else:
        # Sukces: usuń backup dir
        tx._cleanup_backup()


def cleanup_old_backups(root, pattern: str = "*.bak", max_age_days: int = 30) -> int:
    """Usuń stare .bak pliki (cleanup utility).

    Zwraca liczbę usuniętych plików.
    """
    import time
    root = Path(root)
    count = 0
    now = time.time()
    for bak in root.rglob(pattern):
        if bak.is_file():
            try:
                if now - bak.stat().st_mtime > max_age_days * 86400:
                    bak.unlink()
                    count += 1
            except OSError:
                pass
    return count

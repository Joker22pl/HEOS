#!/usr/bin/env python3
"""Aktualizuj quality_* pola w frontmatter na podstawie wyników audytu.

Użycie:
    python3 tools/update_quality.py [--check | --apply] [--root HEOS_ROOT]

Tryby:
    --check (domyślny): raportuje co by się zmieniło, exit 1 jeśli cokolwiek.
                 NIE zapisuje. Bezpieczne dla CI.
    --apply:            zapisuje zmiany atomowo. Atomic write + transakcyjność.
                 Rollback przy błędzie (żaden plik nie jest zmodyfikowany
                 jeśli całość się nie powiedzie).

Wymusza atomic write contract (ADR-008):
- tempfile w tym samym katalogu co plik docelowy
- flush + fsync przed rename
- os.replace (atomowa rename)
- rollback przy błędzie

Czyta każdy skill, uruchamia audyt, ustawia:
- quality_schema: pass (Schema 7/7 PASS) | fail (Schema FAIL)
- quality_technical: pass (Technical PASS) | fail (Technical FAIL)
- quality_operational: zostawia bez zmian (wymaga manualnej oceny)
"""
import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from skill_audit import audytuj_katalog

HEOS_ROOT = Path(__file__).parent.parent


def _parsuj_frontmatter(tekst: str) -> tuple[str | None, str]:
    """Zwraca (frontmatter_yaml_albo_None, rest_po_drugim_---).

    Caller dodaje '---' na początku i '---' przed rest.
    """
    if not tekst.startswith("---"):
        return None, tekst
    parts = tekst.split("---", 2)
    if len(parts) < 3:
        return None, tekst
    return parts[1], parts[2]


def _ensure_trailing_newline(text: str) -> str:
    """Gwarantuje że text kończy się single \\n."""
    if not text.endswith("\n"):
        return text + "\n"
    # Jeśli kończy się wieloma \n, zostaw — to author intent.
    return text


def _ensure_leading_newline(text: str) -> str:
    """Gwarantuje że text zaczyna się od \\n (chyba że jest pusty)."""
    if not text:
        return ""
    if not text.startswith("\n"):
        return "\n" + text
    return text


def _ustaw_quality(fm_text: str, key: str, value: str) -> str:
    """Ustaw key: value w frontmatter (YAML-aware regex).

    Jeśli klucz istnieje → replace in-place.
    Jeśli klucz nie istnieje → dodaj na końcu frontmatter (przed ostatnim
    quality_* jeśli istnieje, lub na samym końcu).

    Wynik ZAWSZE kończy się single \\n. To gwarantuje że caller
    (który wstawi '---' po fm) nie sklei jakoś wartości.

    Nie psuje komentarzy ani porządku kluczy (regex operuje na pojedynczej
    linii, nie na całym bloku).
    """
    pattern = re.compile(rf"^{key}:\s*\S+", re.M)
    if pattern.search(fm_text):
        result = pattern.sub(f"{key}: {value}", fm_text)
        return _ensure_trailing_newline(result)
    # Nie ma klucza — dodaj na końcu frontmatter.
    # Sprawdź czy są inne quality_* — jeśli tak, dodaj za ostatnim.
    quality_lines = list(re.finditer(r"^quality_\w+:\s*\S+\s*$", fm_text, re.M))
    if quality_lines:
        last = quality_lines[-1]
        # Wstaw po ostatnim quality_*
        insert_pos = last.end()
        result = fm_text[:insert_pos] + f"\n{key}: {value}" + fm_text[insert_pos:]
        return _ensure_trailing_newline(result)
    # Brak quality_* — dodaj na samym końcu
    result = _ensure_trailing_newline(fm_text) + f"{key}: {value}\n"
    return result


def _atomic_write(path: Path, content: str) -> None:
    """Zapisz content do path atomowo.

    Procedura:
    1. tempfile w tym samym katalogu (rename atomowy tylko w obrębie fs)
    2. flush + fsync (wymusza zapis na dysk)
    3. os.replace (atomowa zamiana)
    4. Cleanup tmp przy wyjątku
    """
    path_dir = path.parent
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path_dir),
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        # Rollback — usuń tmp jeśli istnieje
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def _cleanup_old_baks(root: Path) -> int:
    """Usuń .bak pliki pozostawione przez poprzednie uruchomienia."""
    count = 0
    for bak in root.rglob("*.bak"):
        if bak.is_file():
            try:
                bak.unlink()
                count += 1
            except OSError:
                pass
    return count


def _plan_updates(root: Path) -> list[dict]:
    """Faza 1: oblicz co by się zmieniło. NIC nie zapisuje.

    Returns: lista dict {path, old_schema, new_schema, old_tech, new_tech}
    """
    plans = []
    raporty = audytuj_katalog(root)
    for r in raporty:
        if r.is_not_skill:
            continue
        txt = r.path.read_text(encoding="utf-8")
        fm, _rest = _parsuj_frontmatter(txt)
        if fm is None:
            continue
        new_schema = "pass" if r.schema_status == "PASS" else "fail"
        new_technical = "pass" if r.technical_status == "PASS" else "fail"
        cur_schema_m = re.search(r"^quality_schema:\s*(\S+)", fm, re.M)
        cur_tech_m = re.search(r"^quality_technical:\s*(\S+)", fm, re.M)
        cur_schema = cur_schema_m.group(1) if cur_schema_m else None
        cur_tech = cur_tech_m.group(1) if cur_tech_m else None
        # Pomiń jeśli bez zmian
        if cur_schema == new_schema and cur_tech == new_technical:
            continue
        plans.append({
            "path": r.path,
            "old_schema": cur_schema,
            "new_schema": new_schema,
            "old_tech": cur_tech,
            "new_tech": new_technical,
        })
    return plans


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", default=True,
                       help="Tylko raportuj (default). Exit 1 jeśli cokolwiek do zmiany.")
    group.add_argument("--apply", action="store_true",
                       help="Zapisz zmiany atomowo.")
    parser.add_argument("--root", default=str(HEOS_ROOT))
    args = parser.parse_args()
    root = Path(args.root).resolve()

    plans = _plan_updates(root)
    if not plans:
        print("✅ Brak zmian — wszystko aktualne")
        return 0

    mode = "APPLY" if args.apply else "CHECK"
    print(f"\n[{mode}] {len(plans)} plik(ów) wymaga aktualizacji:")
    for p in plans:
        rel = p["path"].relative_to(root)
        print(f"  {rel}: schema {p['old_schema']}→{p['new_schema']}, "
              f"technical {p['old_tech']}→{p['new_tech']}")

    if not args.apply:
        # CHECK mode — exit 1 gdy cokolwiek do zmiany (CI gate)
        print(f"\n[{mode}] Użyj --apply żeby zastosować zmiany.")
        return 1 if plans else 0

    # APPLY mode — transakcja
    print(f"\n[APPLY] Zapisuję {len(plans)} plik(ów)...")
    # Faza 1: backup wszystkich (do jednego katalogu)
    backup_dir = root / ".heos-quality-backup"
    backup_dir.mkdir(exist_ok=True)
    backup_paths = []
    try:
        for p in plans:
            backup_path = backup_dir / f"{p['path'].relative_to(root).as_posix()}.bak"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path.write_text(p["path"].read_text(encoding="utf-8"), encoding="utf-8")
            backup_paths.append(backup_path)
        # Faza 2: atomic write każdego (z rollback przy wyjątku)
        for i, p in enumerate(plans):
            txt = p["path"].read_text(encoding="utf-8")
            fm, rest = _parsuj_frontmatter(txt)
            if fm is None:
                raise RuntimeError(f"Brak frontmatter w {p['path']}")
            new_fm = _ustaw_quality(fm, "quality_schema", p["new_schema"])
            new_fm = _ustaw_quality(new_fm, "quality_technical", p["new_tech"])
            # new_fm zawsze kończy się \n (gwarantowane przez _ustaw_quality).
            # rest normalizujemy żeby zaczynał się od \n (separator od '---').
            # Pusty rest → "" (nie wstawiamy \n na początku pustego).
            rest_norm = _ensure_leading_newline(rest) if rest else ""
            new_txt = f"---{new_fm}---{rest_norm}"
            _atomic_write(p["path"], new_txt)
            print(f"  ✓ {p['path'].relative_to(root)}")
        # Faza 3: cleanup backup dir (sukces)
        for bp in backup_paths:
            bp.unlink()
        # Sprzątnij puste podkatalogi
        for d in sorted(backup_dir.rglob("*"), reverse=True):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
        if backup_dir.exists() and not any(backup_dir.iterdir()):
            backup_dir.rmdir()
        print(f"\n[APPLY] Sukces — {len(plans)} plik(ów) zaktualizowanych.")
        return 0
    except Exception as e:
        # Rollback — przywróć z backup
        print(f"\n[APPLY] Błąd: {e}. Rollback...")
        for bp in backup_paths:
            if bp.exists():
                original = root / bp.relative_to(backup_dir).with_suffix("")
                # Ścieżka oryginalna nie ma sufiksu .bak
                rel = bp.relative_to(backup_dir)
                # Strip .bak z końca
                if rel.suffix == ".bak":
                    original = root / rel.with_suffix("")
                else:
                    original = root / rel
                if original.exists():
                    original.write_text(bp.read_text(encoding="utf-8"), encoding="utf-8")
                bp.unlink()
        # Cleanup backup dir
        if backup_dir.exists():
            for d in sorted(backup_dir.rglob("*"), reverse=True):
                if d.is_file():
                    d.unlink()
                elif d.is_dir():
                    d.rmdir()
            if backup_dir.exists():
                backup_dir.rmdir()
        print(f"[APPLY] Rollback zakończony. Repo w stanie sprzed --apply.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
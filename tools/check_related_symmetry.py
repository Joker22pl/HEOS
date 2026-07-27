#!/usr/bin/env python3
"""Sprawdź i opcjonalnie napraw asymetrię cross-references w HEOS.

Reguła: jeśli A → B to B → A (symetria w grafie relacji).
heos_lint.py NIE sprawdza asymetrii — to jest luka.

Użycie:
    python3 tools/check_related_symmetry.py [--dry-run] [--root HEOS_ROOT]
"""
import argparse
import re
import sys
from pathlib import Path

HEOS_ROOT = Path(__file__).parent.parent


def _collect_artefakty(root: Path) -> dict[str, tuple[Path, set[str]]]:
    """Zwraca {id: (path, related_set)} dla każdego artefaktu z related."""
    out: dict[str, tuple[Path, set[str]]] = {}
    for p in root.rglob("*.md"):
        if "archive" in p.parts or "templates" in p.parts or "joker-deliverables" in p.parts:
            continue
        if not p.name.endswith(".md"):
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        m = re.match(r"---\n(.*?)\n---", txt, re.DOTALL)
        if not m:
            continue
        fm = m.group(1)
        id_m = re.search(r"^id:\s*(\S+)", fm, re.M)
        if not id_m:
            continue
        my_id = id_m.group(1)
        # Format 1: lista (related:\n  - X\n  - Y)
        rels: set[str] = set()
        rel_list_m = re.search(r"^related:\n((?:\s*-\s*\S+\n?)+)", fm, re.M)
        if rel_list_m:
            rels.update(re.findall(r"-\s*(\S+)", rel_list_m.group(1)))
        # Format 2: inline (related: [X, Y])
        rel_inline_m = re.search(r"^related:\s*\[([^\]]*)\]", fm, re.M)
        if rel_inline_m:
            for item in rel_inline_m.group(1).split(","):
                item = item.strip()
                if item:
                    rels.add(item)
        # Format 3: scalar (related: X)
        rel_scalar_m = re.search(r"^related:\s*(\S+)$", fm, re.M)
        if rel_scalar_m and not rel_list_m and not rel_inline_m:
            rels.add(rel_scalar_m.group(1))
        out[my_id] = (p, rels)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Pokaż braki, nie naprawiaj")
    parser.add_argument("--root", default=str(HEOS_ROOT))
    args = parser.parse_args()
    root = Path(args.root).resolve()

    artefakty = _collect_artefakty(root)
    asym = []
    for src, (path, targets) in artefakty.items():
        for t in targets:
            if t in artefakty:
                if src not in artefakty[t][1]:
                    asym.append((src, t))
            # else: broken ref, handled by heos_lint

    if not asym:
        print("✅ Brak asymetrii cross-references — graf spójny")
        return 0

    print(f"⚠️  Znaleziono {len(asym)} asymetrii cross-references:")
    for src, t in asym:
        print(f"  {src} → {t} (ale {t} nie ma {src})")

    if args.dry_run:
        return 1

    # Napraw: dodaj src do t.related
    # ADR-008: transakcja — albo wszystkie pliki zaktualizowane, albo żaden
    fixed = 0
    from _heos_atomic import transaction
    try:
        with transaction(root) as tx:
            for src, t in asym:
                path, rels = artefakty[t]
                if src in rels:
                    continue
                txt = path.read_text(encoding="utf-8")
                # Dodaj src do related w frontmatter
                if re.search(r"^related:\n", txt, re.M):
                    # Zachowaj spójny format: dodaj na końcu listy related (przed quality_/description)
                    new_txt = re.sub(r"(related:\n((?:\s*-\s*\S+\n?)+))",
                                     lambda m: m.group(1) + f"- {src}\n" if not m.group(1).endswith(f"- {src}\n") else m.group(1),
                                     txt, count=1)
                else:
                    # Brak related — dodaj blok przed quality
                    new_txt = re.sub(r"(quality_)", f"related:\n- {src}\n\n\\1", txt, count=1)
                # ADR-008: atomic write + backup via transaction
                tx.atomic_write(path, new_txt)
                fixed += 1
    except Exception as e:
        # transaction automatycznie rollback
        print(f"\n❌ Błąd podczas naprawy: {e}. Rollback wykonany przez transaction.")
        return 2
    print(f"\nNaprawiono: {fixed}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
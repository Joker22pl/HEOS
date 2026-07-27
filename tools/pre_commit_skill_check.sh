#!/usr/bin/env bash
# HEOS pre-commit hook — Skill audit (3-poziomowy)
#
# Wywoływany przez pre-commit (jako local hook). Sprawdza:
#   1. Czy w staged zmianach są pliki Skills (skills/*.md, */SKILL.md)
#   2. Jeśli tak — uruchamia skill_audit.py z poziomem schema
#   3. Blokuje commit jeśli którykolwiek ma FAIL Schema
#
# Wzorzec: HEOS v1.2 standard Skills (7 obowiązkowych sekcji)
# HEOS_CONSTITUTION: https://github.com/Joker22pl/gaja-projekty/blob/main/HEOS/CONSTITUTION.md
#
# Użycie:
#   - Automatycznie przez pre-commit (pass_filenames: false, always_run: false)
#   - Ręcznie: ./pre_commit_skill_check.sh
#
# Exit codes:
#   0 — OK (brak Skill files do sprawdzenia LUB wszystkie PASS)
#   1 — FAIL Schema w co najmniej jednym Skillu
#   2 — błąd wewnętrzny (brak skill_audit.py, brak git)

set -e

# === Konfiguracja ===
HEOS_ROOT="${HEOS_ROOT:-$(dirname "$(dirname "$(readlink -f "$0")")")}"
SKILL_AUDIT="$HEOS_ROOT/tools/skill_audit.py"

# Sprawdź czy skill_audit istnieje
if [ ! -f "$SKILL_AUDIT" ]; then
  echo "❌ HEOS pre-commit: nie znaleziono skill_audit.py w $SKILL_AUDIT"
  exit 2
fi

# Sprawdź czy jesteśmy w git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "⚠️  HEOS pre-commit: brak git repo, pomijam"
  exit 0
fi

# === Sprawdź staged files ===
# Wykrywamy: skills/*.md (HEOS v1.2 flat) + */SKILL.md (HEOS v1.1 / runtime profil)
# Ścieżki w git diff są względne do git root (z prefiksem HEOS/ dla submodułu)
STAGED_SKILLS=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null | \
  grep -E '(/skills/.*\.md|/SKILL\.md)$' || true)

if [ -z "$STAGED_SKILLS" ]; then
  # Brak Skills w staged → OK
  exit 0
fi

echo "🔍 HEOS pre-commit: sprawdzam $(echo "$STAGED_SKILLS" | wc -l) plik(ów) Skill..."
echo ""

# === Uruchom audyt ===
# Określ root dla audytu:
# - skill_audit.py szuka <root>/skills/*.md (HEOS v1.2 flat layout)
# - Domyślnie root = $HEOS_ROOT (rodzic katalogu skills/)
# - Jeśli $HEOS_ROOT nie istnieje → audytuj najbliższy git root (fallback dla subprojektów)
GIT_ROOT=$(git rev-parse --show-toplevel)
if [ -d "$HEOS_ROOT/skills" ]; then
  AUDIT_ROOT="$HEOS_ROOT"
elif [ -d "$GIT_ROOT/skills" ]; then
  AUDIT_ROOT="$GIT_ROOT"
else
  echo "⚠️  HEOS pre-commit: brak katalogu skills/ ani w $HEOS_ROOT ani w $GIT_ROOT"
  exit 0
fi

# Uruchom — wyjście do stdout/stderr, exit code ma znaczenie
if python3 "$SKILL_AUDIT" "$AUDIT_ROOT" --level schema --quiet; then
  echo ""
  echo "✅ HEOS pre-commit: Skills OK"
  exit 0
else
  echo ""
  echo "❌ HEOS pre-commit: JEDEN LUB WIĘCEJ Skills ma FAIL Schema"
  echo "   Napraw brakujące sekcje: Cel, Zakres, Kiedy używać, Kiedy nie używać,"
  echo "   Workflow, Przykłady, Lessons Learned"
  echo "   Szczegóły: python3 $SKILL_AUDIT --help"
  echo ""
  echo "   Aby pominąć (niezalecane): git commit --no-verify"
  exit 1
fi

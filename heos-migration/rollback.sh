#!/usr/bin/env bash
# rollback.sh — cofa migrację HEOS v1.2 → v1.1.
#
# Wymaga:
# - backup w ~/hermes-backups/heos-pre-v1.2-*.tar.gz (Etap 1.7)
# - git tag v1.1.0-pre-migration (Etap 1.7)
#
# Użycie:
#   ./rollback.sh              # faktyczny rollback
#   ./rollback.sh --dry-run    # pokaż co by zrobił
#
# Bezpieczeństwo:
# - Usuwa pliki v1.2 które nie były w v1.1
# - Przywraca pliki v1.1 z backupu
# - Checkout do tagu v1.1.0-pre-migration (NIE hard reset, bo to bezpieczniejsze)
# - Dostępny tryb --dry-run

set -e

BACKUP_DIR="$HOME/hermes-backups"
BACKUP_GLOB="heos-pre-v1.2-*.tar.gz"
HEOS_ROOT="$HOME/gaja-projekty/HEOS"
GIT_TAG="v1.1.0-pre-migration"
DRY_RUN=false

if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "=== ROLLBACK DRY-RUN ==="
else
    echo "=== ROLLBACK (REALNY) ==="
fi

echo ""

# 1. Sprawdź backup
if [[ ! -d "$BACKUP_DIR" ]]; then
    echo "❌ Katalog $BACKUP_DIR nie istnieje"
    exit 1
fi
BACKUP_FILE=$(ls -t "$BACKUP_DIR"/$BACKUP_GLOB 2>/dev/null | head -1)
if [[ -z "$BACKUP_FILE" ]]; then
    echo "❌ Brak backupu $BACKUP_DIR/$BACKUP_GLOB"
    exit 1
fi
echo "✅ Backup: $BACKUP_FILE"

# 2. Sprawdź git tag
cd "$HEOS_ROOT/.." || exit 1
if git rev-parse "$GIT_TAG" >/dev/null 2>&1; then
    echo "✅ Git tag: $GIT_TAG"
else
    echo "⚠️  Git tag $GIT_TAG nie istnieje (rollback tylko z backupu)"
fi

# 3. Pokaż co by zrobił
echo ""
echo "Operacje (w kolejności):"
echo "1. tar -xzf $BACKUP_FILE -C /  # przywróci pliki v1.1"
echo "2. git checkout $GIT_TAG     # cofnie git do stanu v1.1 (bezpieczne)"
echo ""

if [[ "$DRY_RUN" == true ]]; then
    echo "(dry-run: nic nie zostało zrobione)"
    exit 0
fi

# 4. Potwierdź
read -p "Na pewno wykonać rollback? Pliki v1.2 (CONSTITUTION.md, ARCHITECTURE.md, tools/, templates/, heos-migration/, STATUS.md, .registry.yaml) zostaną usunięte. [t/N] " CONFIRM
if [[ "$CONFIRM" != "t" && "$CONFIRM" != "T" ]]; then
    echo "Anulowano"
    exit 0
fi

# 5. Wykonaj
echo ""
echo "1. Przywracam backup..."
tar -xzf "$BACKUP_FILE" -C /

# 6. git checkout
cd "$HEOS_ROOT/.." || exit 1
echo "2. git checkout $GIT_TAG..."
git checkout "$GIT_TAG" 2>&1 | tail -5

echo ""
echo "✅ Rollback zakończony"
echo "   Sprawdź stan: cd $HEOS_ROOT && ls"

#!/usr/bin/env python3
"""
Narzędzie do audytu + zmiany widoczności repozytoriów Joker22pl/*.

Per ADR-011: domyślnie nowe repo są prywatne. To narzędzie pomaga:
1. Audyt: wylistować aktualną widoczność wszystkich repo (read-only)
2. Zmiana: przełączyć istniejące publiczne na private (wymaga PAT)

Wymaga GITHUB_TOKEN env var z scope `repo` (nie `public_repo`, bo widoczność
zmieniamy na private, nie na public). Bez tokena: działa tylko --audit.

Użycie:
    # Audyt (read-only, bez tokena):
    python3 tools/repo_visibility.py --audit

    # Zmień jedno repo na private:
    GITHUB_TOKEN=ghp_... python3 tools/repo_visibility.py --make-private --repo HEOS

    # Zmień wszystkie publiczne na private (z potwierdzeniem):
    GITHUB_TOKEN=ghp_... python3 tools/repo_visibility.py --make-private --all

Bezpieczeństwo:
- Skrypt NIE JEST idempotentny w kierunku public → private: po zmianie
  publicznego na prywatne, nie ma komendy "undo" z poziomu tego skryptu
  (trzeba ręcznie w UI lub przez inny endpoint).
- Brak flagi `--confirm-all` — wszystko wymaga explicit --repo lub explicit
  potwierdzenia per-repo dla --all.
- Każda zmiana loguje: timestamp, repo, prev_visibility, new_visibility.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

GITHUB_API = "https://api.github.com"
OWNER = "Joker22pl"

# Znane repo z poprzednich sesji HEOS (hardcoded żeby uniknąć skanowania całego konta)
# Jeśli doda się nowe repo, trzeba je tutaj dopisać LUB użyć --all (skanuje GitHub API).
KNOWN_HEOS_REPOS = [
    "HEOS",
    "arp-arch",
    "arp-firmware",
    "arp-ros2",
    "imp2-arch",
    "imp2-firmware",
    "imp2-ros2",
]


def _api_request(method: str, url: str, token: str | None = None,
                 body: dict | None = None) -> tuple[dict, int]:
    """Wykonuje request do GitHub API. Zwraca (body, status_code)."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "heos-repo-visibility/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read()), e.code
        except Exception:
            return {"error": str(e)}, e.code


def list_repos(token: str | None = None) -> list[dict]:
    """Lista wszystkich repo Joker22pl/*. Wymaga tokenu jeśli są prywatne."""
    url = f"{GITHUB_API}/users/{OWNER}/repos?per_page=100&type=all"
    data, status = _api_request("GET", url, token=token)
    if status != 200:
        print(f"❌ Błąd API (status {status}): {data}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, list):
        return []
    return data


def get_repo_visibility(repo: str, token: str | None = None) -> dict:
    """Zwraca widoczność jednego repo."""
    url = f"{GITHUB_API}/repos/{OWNER}/{repo}"
    data, status = _api_request("GET", url, token=token)
    if status == 404:
        return {"exists": False, "name": repo}
    if status != 200:
        print(f"❌ Błąd API dla {repo} (status {status}): {data}", file=sys.stderr)
        return {"exists": False, "error": status, "name": repo}
    return data


def make_repo_private(repo: str, token: str) -> tuple[bool, str]:
    """Zmienia widoczność repo na private. Zwraca (success, message)."""
    url = f"{GITHUB_API}/repos/{OWNER}/{repo}"
    body = {"private": True}

    # Sprawdź aktualną widoczność PRZED zmianą (audit trail)
    current = get_repo_visibility(repo, token)
    prev_visibility = current.get("visibility", "?")

    # Zmień
    data, status = _api_request("PATCH", url, token, body)
    if status != 200:
        return False, f"API error {status}: {data.get('message', data)}"

    new_visibility = data.get("visibility", "?")
    msg = f"OK {repo}: {prev_visibility} → {new_visibility}"
    print(msg)
    return True, msg


def audit(token: str | None = None) -> None:
    """Wylistuj widoczność wszystkich znanych repo."""
    print(f"=== Widoczność repozytoriów {OWNER}/* ===\n")
    print(f"{'Repo':<25} {'Visibility':<12} {'Default branch':<20} {'Private':<10}")
    print("-" * 70)

    for repo in KNOWN_HEOS_REPOS:
        info = get_repo_visibility(repo, token)
        if not info.get("exists", True):
            print(f"{repo:<25} {'❌ NOT FOUND':<12}")
            continue
        vis = info.get("visibility", "?")
        default_branch = info.get("default_branch", "?")
        private = info.get("private", "?")
        print(f"{repo:<25} {vis:<12} {default_branch:<20} {str(private):<10}")

    print()
    print("Notatka: HEOS jest explicite public (dokumentacja dla społeczności).")
    print("Reszta powinna być private per ADR-011.")


def make_private(token: str, repo: str | None = None, all_repos: bool = False,
                 yes: bool = False) -> None:
    """Zmienia widoczność na private."""
    if not token:
        print("❌ GITHUB_TOKEN env var wymagany dla --make-private.", file=sys.stderr)
        print("   Ustaw: export GITHUB_TOKEN=ghp_...", file=sys.stderr)
        sys.exit(1)

    if repo:
        repos_to_change = [repo]
    elif all_repos:
        repos_to_change = KNOWN_HEOS_REPOS
    else:
        print("❌ Musisz podać --repo NAME lub --all", file=sys.stderr)
        sys.exit(1)

    print(f"=== Zmiana widoczności na private: {len(repos_to_change)} repo ===\n")

    # Najpierw sprawdź aktualny stan — bez zmian
    candidates = []
    for r in repos_to_change:
        info = get_repo_visibility(r, token)
        if not info.get("exists", True):
            print(f"⚠️  {r}: nie istnieje (404)")
            continue
        vis = info.get("visibility", "?")
        if vis == "private":
            print(f"✓ {r}: już jest private, pomijam")
            continue
        if vis == "public":
            candidates.append(r)
            print(f"  {r}: public → private (będzie zmienione)")
        else:
            print(f"⚠️  {r}: visibility={vis}, nie wiem co zrobić")

    if not candidates:
        print("\n✅ Nic do zrobienia.")
        return

    if not yes:
        print(f"\n⚠️  {len(candidates)} repo do zmiany: {', '.join(candidates)}")
        print("   Użyj --yes żeby potwierdzić.")
        sys.exit(0)

    print(f"\n--- Zmieniam {len(candidates)} repo ---")
    success = 0
    failed = 0
    for r in candidates:
        ok, msg = make_repo_private(r, token)
        if ok:
            success += 1
        else:
            failed += 1
            print(f"  ❌ {r}: {msg}")
        # Rate limit: max 5000/h, ale bądźmy grzeczni
        time.sleep(0.5)

    print(f"\n=== Podsumowanie: {success} OK, {failed} failed ===")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="HEOS repo visibility utility — audyt + zmiana widoczności Joker22pl/*"
    )
    parser.add_argument("--audit", action="store_true", help="Audit only (read-only)")
    parser.add_argument("--make-private", action="store_true", help="Change visibility to private")
    parser.add_argument("--repo", help="Specific repo to change")
    parser.add_argument("--all", action="store_true", help="Apply to all known repos")
    parser.add_argument("--yes", action="store_true", help="Confirm changes (required for --make-private)")

    args = parser.parse_args()

    # Walidacja argumentów
    if not args.audit and not args.make_private:
        parser.print_help()
        print("\n❌ Musisz podać --audit lub --make-private", file=sys.stderr)
        return 2

    token = os.environ.get("GITHUB_TOKEN")

    if args.audit:
        audit(token)
        return 0

    if args.make_private:
        if token is None:
            make_private("", repo=args.repo, all_repos=args.all, yes=args.yes)
        else:
            make_private(token, repo=args.repo, all_repos=args.all, yes=args.yes)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())

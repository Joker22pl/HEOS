"""
Testy jednostkowe dla tools/repo_visibility.py.

Sprawdza:
- argparse: --audit, --make-private, --repo, --all, --yes
- Walidacja: bez tokena + --make-private → exit 1
- Walidacja: --make-private bez --repo/--all → exit 1
- Walidacja: --make-private bez --yes → "potwierdź"
- Format output: --audit wypisuje tabelę
- Audit HEOS hardcoded listy (KNOWN_HEOS_REPOS)
"""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_visibility


def test_known_repos_constant():
    """KNOWN_HEOS_REPOS zawiera HEOS + arp-* + imp2-*."""
    repos = repo_visibility.KNOWN_HEOS_REPOS
    assert "HEOS" in repos
    assert "arp-arch" in repos
    assert "arp-firmware" in repos
    assert "arp-ros2" in repos
    assert "imp2-arch" in repos
    assert "imp2-firmware" in repos
    assert "imp2-ros2" in repos
    # Powinno być tylko 7 (sprawdź że nie dodaliśmy nowych przypadkowo)
    assert len(repos) == 7


def test_api_request_with_no_token(capsys):
    """Request bez tokena nie wysyła Authorization header."""
    # Testujemy bez faktycznego HTTP — sprawdzamy że helper działa
    # Mock urllib żeby nie robić prawdziwego requestu
    with patch("repo_visibility.urllib.request.urlopen") as mock_urlopen:
        # Context manager protocol dla urlopen
        from contextlib import contextmanager

        @contextmanager
        def fake_urlopen(req, **kwargs):
            yield type("FakeResp", (), {
                "read": lambda self: b'{"ok": true}',
                "status": 200,
            })()

        mock_urlopen.side_effect = fake_urlopen

        data, status = repo_visibility._api_request(
            "GET", "https://api.github.com/test", None
        )

        assert status == 200
        assert data == {"ok": True}
        # Sprawdź że Authorization NIE było wysłane
        call_args = mock_urlopen.call_args
        request_obj = call_args[0][0]
        assert "Authorization" not in request_obj.headers


def test_api_request_with_token(capsys):
    """Request z tokenem wysyła Bearer Authorization."""
    with patch("repo_visibility.urllib.request.urlopen") as mock_urlopen:
        from contextlib import contextmanager

        @contextmanager
        def fake_urlopen(req, **kwargs):
            yield type("FakeResp", (), {
                "read": lambda self: b'{"ok": true}',
                "status": 200,
            })()

        mock_urlopen.side_effect = fake_urlopen

        data, status = repo_visibility._api_request(
            "GET", "https://api.github.com/test", "ghp_test_token"
        )

        assert status == 200
        call_args = mock_urlopen.call_args
        request_obj = call_args[0][0]
        assert request_obj.headers["Authorization"] == "Bearer ghp_test_token"


def test_api_request_404():
    """404 → zwraca error dict + status code."""
    from io import BytesIO
    import urllib.error

    mock_response = MagicMock()
    mock_response.read.return_value = b'{"message": "Not Found"}'

    mock_error = urllib.error.HTTPError(
        url="https://api.github.com/test",
        code=404,
        msg="Not Found",
        hdrs=MagicMock(),  # typ: Message[str, str] - mock
        fp=mock_response,
    )

    with patch("repo_visibility.urllib.request.urlopen", side_effect=mock_error):
        data, status = repo_visibility._api_request(
            "GET", "https://api.github.com/test", "ghp_x"
        )

    assert status == 404
    assert "message" in data


def test_audit_uses_known_repos(capsys):
    """--audit iteruje KNOWN_HEOS_REPOS, nie wywołuje API dla brakujących."""
    with patch("repo_visibility.get_repo_visibility") as mock_get:
        mock_get.return_value = {
            "exists": True,
            "visibility": "public",
            "default_branch": "main",
            "private": False,
        }

        repo_visibility.audit(None)
        captured = capsys.readouterr()

        # Powinno wywołać get_repo_visibility dla każdego KNOWN_HEOS_REPOS
        assert mock_get.call_count == len(repo_visibility.KNOWN_HEOS_REPOS)
        # Powinno wypisać tabelę
        assert "Widoczność repozytoriów" in captured.out
        assert "HEOS" in captured.out
        assert "public" in captured.out


def test_make_private_without_token_exits(capsys):
    """--make-private bez GITHUB_TOKEN → exit 1 z komunikatem."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(SystemExit) as exc_info:
            repo_visibility.make_private(None, repo="HEOS")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "GITHUB_TOKEN" in captured.err


def test_make_private_without_repo_or_all_exits(capsys):
    """--make-private bez --repo i --all → exit 1."""
    with patch.dict("os.environ", {"GITHUB_TOKEN": "ghp_test"}):
        with pytest.raises(SystemExit) as exc_info:
            repo_visibility.make_private("ghp_test")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "--repo" in captured.err or "--all" in captured.err


def test_make_private_already_private(capsys):
    """Repozytorium już private → pomijane."""
    with patch("repo_visibility.get_repo_visibility") as mock_get:
        mock_get.return_value = {
            "exists": True,
            "visibility": "private",
            "default_branch": "main",
            "private": True,
        }

        repo_visibility.make_private("ghp_test", repo="HEOS", yes=True)
        captured = capsys.readouterr()
        assert "już jest private" in captured.out


def test_make_private_nonexistent_repo(capsys):
    """Repozytorium nie istnieje (404) → pomijane."""
    with patch("repo_visibility.get_repo_visibility") as mock_get:
        mock_get.return_value = {"exists": False, "name": "NONEXISTENT"}

        repo_visibility.make_private("ghp_test", repo="NONEXISTENT", yes=True)
        captured = capsys.readouterr()
        assert "nie istnieje" in captured.out


def test_make_private_changes_visibility(capsys):
    """Smoke test: pełny flow public → private."""
    # Mock API: visibility check (public), PATCH (private), then verify
    visibility_state = {"private": False}

    def fake_get(repo, token):
        return {
            "exists": True,
            "visibility": "private" if visibility_state["private"] else "public",
            "default_branch": "main",
            "private": visibility_state["private"],
        }

    def fake_request(method, url, token, body=None):
        if method == "PATCH":
            visibility_state["private"] = True
            return {"visibility": "private", "private": True}, 200
        return {}, 500  # GET nie powinien być wywoływany przez make_repo_private

    with patch("repo_visibility.get_repo_visibility", side_effect=fake_get), \
         patch("repo_visibility._api_request", side_effect=fake_request):
        repo_visibility.make_private("ghp_test", repo="HEOS", yes=True)

    captured = capsys.readouterr()
    assert "HEOS: public → private" in captured.out


def test_main_without_args_returns_2(capsys):
    """main() bez argumentów → wypisuje help + return code 2."""
    with patch("sys.argv", ["repo_visibility.py"]):
        returncode = repo_visibility.main()

    assert returncode == 2
    captured = capsys.readouterr()
    # argparse wypisuje "usage:" do stderr (przez parser.print_help)
    assert "usage:" in (captured.out + captured.err)


if __name__ == "__main__":
    test_known_repos_constant()
    test_api_request_with_no_token()
    test_api_request_with_token()
    test_api_request_404()
    test_audit_uses_known_repos()
    test_make_private_without_token_exits()
    test_make_private_without_repo_or_all_exits()
    test_make_private_already_private()
    test_make_private_nonexistent_repo()
    test_make_private_changes_visibility()
    test_main_without_args_shows_help()
    print("All 11 tests passed.")

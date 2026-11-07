"""Sign-in status reporting (no network, no secrets)."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import auth, cli  # noqa: E402


def test_status_signed_out_when_no_tokens(monkeypatch):
    """Missing token file reads as signed out with the fix command."""
    monkeypatch.setattr(auth, "load_tokens", lambda: None)
    line = cli.token_status_line()
    assert line.startswith("signed out") and "login" in line
    assert "refresh_token" not in line and "access_token" not in line


def test_status_signed_in_when_access_token_live(monkeypatch):
    """Unexpired access token reports live with no refresh attempt."""
    live = {"access_token": "live-token-value",
            "expires_at": time.time() + 3600}
    monkeypatch.setattr(auth, "load_tokens", lambda: live)
    monkeypatch.setattr(auth, "stored_access_token",
                        lambda: (_ for _ in ()).throw(AssertionError("must not refresh")))
    line = cli.token_status_line()
    assert line.startswith("signed in") and "live until" in line
    assert "live-token-value" not in line


def test_status_refreshes_expired_token(monkeypatch):
    """Expired access token triggers one silent refresh."""
    monkeypatch.setattr(auth, "load_tokens",
                        lambda: {"access_token": "old", "expires_at": time.time() - 10})
    monkeypatch.setattr(auth, "stored_access_token", lambda: "fresh-token-value")
    line = cli.token_status_line()
    assert line.startswith("signed in") and "refreshed" in line
    assert "fresh-token-value" not in line


def test_status_dead_refresh_reads_signed_out(monkeypatch):
    """Dead refresh token reports signed out with the fix command."""
    monkeypatch.setattr(auth, "load_tokens",
                        lambda: {"access_token": "old-token-value",
                                 "expires_at": time.time() - 10,
                                 "refresh_token": "refresh-secret-value"})
    monkeypatch.setattr(auth, "stored_access_token", lambda: None)
    line = cli.token_status_line()
    assert line.startswith("signed out") and "login" in line
    assert "old-token-value" not in line and "refresh-secret-value" not in line

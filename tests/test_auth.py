import io
import json
import os
import stat
import sys
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import api, auth  # noqa: E402


def _isolate_store(monkeypatch, tmp_path):
    monkeypatch.setenv("REINVENT26_TOKEN_FILE", str(tmp_path / "tokens.json"))
    monkeypatch.setenv("REINVENT26_NO_KEYCHAIN", "1")


def test_pkce_rfc7636_vector():
    assert auth.challenge_for(
        "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    ) == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"


def test_verifier_and_state_fresh_each_attempt():
    v1, v2 = auth.new_verifier(), auth.new_verifier()
    assert v1 != v2 and 43 <= len(v1) <= 128
    assert auth.new_state() != auth.new_state()


def test_authorize_url_exact_redirect_no_tokens():
    url = auth.authorize_url("http://localhost:8484/callback", "CH", "ST")
    assert "response_type=code" in url
    assert f"client_id={auth.CLIENT_ID}" in url
    assert "identity_provider=AWSBuilderID" in url
    assert "code_challenge_method=S256" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8484%2Fcallback" in url
    assert "access_token" not in url and "refresh_token" not in url


def test_store_roundtrip_0600(monkeypatch, tmp_path):
    _isolate_store(monkeypatch, tmp_path)
    payload = {"access_token": "a", "refresh_token": "r",
               "expires_at": 9999999999.0}
    auth.save_tokens(payload)
    assert auth.load_tokens() == payload
    mode = stat.S_IMODE(os.stat(str(tmp_path / "tokens.json")).st_mode)
    assert mode == 0o600


def test_stored_token_valid_returns_without_network(monkeypatch, tmp_path):
    _isolate_store(monkeypatch, tmp_path)
    auth.save_tokens({"access_token": "live", "refresh_token": "r",
                      "expires_at": 9999999999.0})

    def fail(*a, **k):
        raise AssertionError("network used for valid token")

    monkeypatch.setattr(auth, "_http_post_form", fail)
    assert auth.stored_access_token() == "live"


def test_expired_token_refreshes_silently(monkeypatch, tmp_path):
    _isolate_store(monkeypatch, tmp_path)
    auth.save_tokens({"access_token": "old", "refresh_token": "r",
                      "expires_at": 1.0})
    monkeypatch.setattr(auth, "_http_post_form",
                        lambda url, fields: {
                            "access_token": "new",
                            "refresh_token": "r2",
                            "expires_in": 3600})
    assert auth.stored_access_token() == "new"
    assert auth.load_tokens()["refresh_token"] == "r2"


def test_dead_refresh_returns_none(monkeypatch, tmp_path):
    _isolate_store(monkeypatch, tmp_path)
    auth.save_tokens({"access_token": "old", "refresh_token": "dead",
                      "expires_at": 1.0})

    def fail(*a, **k):
        raise OSError("token endpoint down")

    monkeypatch.setattr(auth, "_http_post_form", fail)
    assert auth.stored_access_token() is None


def test_handle_401_ignores_explicit_tokens(monkeypatch, tmp_path):
    _isolate_store(monkeypatch, tmp_path)
    auth.save_tokens({"access_token": "stored", "refresh_token": "r",
                      "expires_at": 9999999999.0})
    assert auth.handle_401("user-override-token") is None
    assert auth.handle_401(None) is None


def _http_401():
    return urllib.error.HTTPError(
        "https://x", 401, "Unauthorized", {}, io.BytesIO(b"{}"))


class _Resp:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_api_401_refreshes_once_then_retries(monkeypatch):
    seen = []
    responses = iter([_http_401(), _Resp({"ok": True}),
                        _http_401(), _http_401()])

    def fake_urlopen(req, timeout=None):
        seen.append(req.get_header("Authorization"))
        nxt = next(responses)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    monkeypatch.setattr(api, "_on_401", lambda old: "fresh-token",
                        raising=False)
    try:
        assert api._request("GET", "/v1/events", token="stale") == {"ok": True}
        assert seen == ["Bearer stale", "Bearer fresh-token"]
        with __import__("pytest").raises(api.EventsError):
            api._request("GET", "/v1/events", token="stale")
        assert seen[-1] == "Bearer fresh-token"  # second 401 raises, no loop
    finally:
        monkeypatch.setattr(api, "_on_401", None, raising=False)


def test_login_stores_tokens(monkeypatch, tmp_path):
    _isolate_store(monkeypatch, tmp_path)
    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda url: True)
    monkeypatch.setattr(auth, "_receive_code", lambda port, state: "code-1")
    monkeypatch.setattr(auth, "exchange_code",
                        lambda code, uri, verifier: {
                            "access_token": "a1", "refresh_token": "r1",
                            "expires_in": 3600})
    payload = auth.login()
    assert payload["access_token"] == "a1"
    assert auth.load_tokens()["refresh_token"] == "r1"

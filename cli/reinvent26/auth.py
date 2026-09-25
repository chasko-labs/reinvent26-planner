"""Builder ID OAuth login with PKCE S256 (stdlib only).

Flow values come from the canonical Events API auth docs:
authorize/token endpoints at oauth.awsevents.com, public client id,
scope openid+email+events/access, identity_provider=AWSBuilderID,
loopback redirect http://localhost:8484-8489/callback (exact match).

Tokens are never logged or put in urls: the browser opens an authorize
url carrying only the public challenge+state, and the code exchange is
a POST body. Access tokens live 60 minutes, refresh tokens 30 days.
Storage prefers the OS keychain and falls back to a 0600 file.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

AUTHORIZE_URL = "https://oauth.awsevents.com/oauth2/authorize"
TOKEN_URL = "https://oauth.awsevents.com/oauth2/token"
CLIENT_ID = "7vmom55m1qstvq8i71ph127bfq"
SCOPE = "openid email events/access"
IDENTITY_PROVIDER = "AWSBuilderID"
REDIRECT_PORTS = (8484, 8485, 8486, 8487, 8488, 8489)
CALLBACK_PATH = "/callback"
EXPIRY_SKEW = 60


class AuthError(Exception):
    """Sign-in required or refresh failed: run `reinvent26 login`."""


def token_file() -> str:
    override = os.environ.get("REINVENT26_TOKEN_FILE")
    if override:
        return override
    return os.path.join(
        os.path.expanduser("~"), ".config", "reinvent26", "tokens.json")


def _keychain_available() -> bool:
    if os.environ.get("REINVENT26_NO_KEYCHAIN"):
        return False
    return shutil.which("security") is not None or \
        shutil.which("secret-tool") is not None


def _keychain_get() -> dict | None:
    try:
        if shutil.which("security") is not None:
            out = subprocess.run(
                ["security", "find-generic-password", "-s",
                 "reinvent26", "-w"],
                capture_output=True, timeout=10, text=True,
            )
            if out.returncode == 0 and out.stdout.strip():
                return json.loads(out.stdout.strip())
        elif shutil.which("secret-tool") is not None:
            out = subprocess.run(
                ["secret-tool", "lookup", "service", "reinvent26"],
                capture_output=True, timeout=10, text=True,
            )
            if out.returncode == 0 and out.stdout.strip():
                return json.loads(out.stdout.strip())
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return None


def _keychain_set(payload: dict) -> bool:
    blob = json.dumps(payload)
    try:
        if shutil.which("security") is not None:
            subprocess.run(
                ["security", "delete-generic-password", "-s", "reinvent26"],
                capture_output=True, timeout=10,
            )
            out = subprocess.run(
                ["security", "add-generic-password", "-s", "reinvent26",
                 "-a", "attendee", "-w", blob],
                capture_output=True, timeout=10,
            )
            return out.returncode == 0
        if shutil.which("secret-tool") is not None:
            out = subprocess.run(
                ["secret-tool", "store", "--label=reinvent26",
                 "service", "reinvent26"],
                input=blob, capture_output=True, timeout=10, text=True,
            )
            return out.returncode == 0
    except (OSError, subprocess.SubprocessError):
        pass
    return False


def load_tokens() -> dict | None:
    """Stored tokens from keychain or file, or None when never signed in."""
    if _keychain_available():
        found = _keychain_get()
        if found:
            return found
    path = token_file()
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def save_tokens(payload: dict) -> str:
    """Store tokens; returns 'keychain' or the file path used."""
    if _keychain_available() and _keychain_set(payload):
        return "keychain"
    path = token_file()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    os.chmod(path, 0o600)
    return path


def _b64url_nopad(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def new_verifier() -> str:
    """Fresh PKCE verifier per attempt: 43-128 chars from a secure source."""
    return _b64url_nopad(secrets.token_bytes(48))[:128]


def challenge_for(verifier: str) -> str:
    """S256 code challenge: base64url(sha256(verifier)), no padding."""
    return _b64url_nopad(hashlib.sha256(verifier.encode()).digest())


def new_state() -> str:
    return _b64url_nopad(secrets.token_bytes(16))


def authorize_url(redirect_uri: str, challenge: str, state: str) -> str:
    return AUTHORIZE_URL + "?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": SCOPE,
        "identity_provider": IDENTITY_PROVIDER,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    })


def _http_post_form(url: str, fields: dict) -> dict:
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode() or "{}")


def exchange_code(code: str, redirect_uri: str, verifier: str) -> dict:
    return _http_post_form(TOKEN_URL, {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "redirect_uri": redirect_uri,
        "code": code,
        "code_verifier": verifier,
    })


def refresh_tokens(refresh_token: str) -> dict:
    return _http_post_form(TOKEN_URL, {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "refresh_token": refresh_token,
    })


def _store_from_response(resp: dict) -> dict:
    payload = {
        "access_token": resp["access_token"],
        "refresh_token": resp.get("refresh_token", ""),
        "expires_at": time.time() + int(resp.get("expires_in", 3600)),
    }
    if not payload["refresh_token"]:
        stored = load_tokens() or {}
        payload["refresh_token"] = stored.get("refresh_token", "")
    save_tokens(payload)
    return payload


def _receive_code(port: int, expected_state: str, timeout: int = 180) -> str:
    """Serve one /callback request on 127.0.0.1:port; return the auth code."""
    result: dict = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != CALLBACK_PATH:
                self.send_response(404)
                self.end_headers()
                return
            params = urllib.parse.parse_qs(parsed.query)
            result["code"] = (params.get("code") or [None])[0]
            result["state"] = (params.get("state") or [None])[0]
            self.send_response(200, "OK")
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(
                b"signed in at the provider; return to the cli.")

        def log_message(self, *a):
            pass

    server = HTTPServer(("127.0.0.1", port), Handler)
    server.timeout = timeout
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    thread.join(timeout + 5)
    server.server_close()
    if not result.get("code"):
        raise AuthError("no authorization code arrived; try login again")
    if result.get("state") != expected_state:
        raise AuthError("state mismatch; possible CSRF, try login again")
    return result["code"]


def login() -> dict:
    """Interactive Builder ID sign-in; stores tokens, returns the payload."""
    import webbrowser

    verifier = new_verifier()
    state = new_state()
    challenge = challenge_for(verifier)
    last_error: Exception | None = None
    for port in REDIRECT_PORTS:
        redirect_uri = f"http://localhost:{port}{CALLBACK_PATH}"
        try:
            url = authorize_url(redirect_uri, challenge, state)
            print(f"# opening browser for Builder ID sign-in "
                  f"(or open this url):\n# {url}")
            webbrowser.open(url)
            code = _receive_code(port, state)
        except OSError as e:
            last_error = e
            continue
        resp = exchange_code(code, redirect_uri, verifier)
        return _store_from_response(resp)
    raise AuthError(f"could not listen on ports {REDIRECT_PORTS}: {last_error}")


def refresh_now() -> str:
    """One silent refresh; returns the new access token or raises AuthError."""
    stored = load_tokens()
    if not stored or not stored.get("refresh_token"):
        raise AuthError("no stored sign-in; run `reinvent26 login`")
    try:
        resp = refresh_tokens(stored["refresh_token"])
    except Exception as e:
        raise AuthError(f"refresh failed ({e}); run `reinvent26 login`") from e
    return _store_from_response(resp)["access_token"]


def stored_access_token() -> str | None:
    """Valid stored access token, refreshing silently once when expired.

    Returns None when never signed in or the refresh token is dead
    (caller reports sign-in required; data commands never pop a browser).
    """
    stored = load_tokens()
    if not stored or not stored.get("access_token"):
        return None
    if stored.get("expires_at", 0) > time.time() + EXPIRY_SKEW:
        return stored["access_token"]
    try:
        return refresh_now()
    except AuthError:
        return None


def handle_401(old_token: str | None) -> str | None:
    """401 hook for the api layer: refresh once when the failing request
    used the stored login token. Returns the new token, or None when the
    request used an explicit token (leave the user's override alone)."""
    if not old_token:
        return None
    stored = load_tokens()
    if not stored or old_token != stored.get("access_token"):
        return None
    try:
        return refresh_now()
    except AuthError:
        return None

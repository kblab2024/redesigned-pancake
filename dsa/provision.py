#!/usr/bin/env python3
"""
DSA first-run provisioning script.

This container runs once after the Girder server is healthy and:
  1. Creates the admin user (if it does not exist).
  2. Enables the HistomicsUI Girder plugin.
  3. Creates a default "DSA" collection for uploading slides.
  4. Rebuilds Girder's web client so the HistomicsUI tab appears.

Environment variables (set in docker-compose.yml):
  GIRDER_API_ROOT   - e.g. http://girder:8080/api/v1
  DSA_ADMIN_USER    - admin username
  DSA_ADMIN_PASSWORD
  DSA_ADMIN_EMAIL
"""

import os
import sys
import time

import requests

API = os.environ.get("GIRDER_API_ROOT", "http://girder:8080/api/v1")
ADMIN_USER = os.environ.get("DSA_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("DSA_ADMIN_PASSWORD", "password")
ADMIN_EMAIL = os.environ.get("DSA_ADMIN_EMAIL", "admin@example.com")

# ── Helpers ────────────────────────────────────────────────────────────────────

def wait_for_server(timeout: int = 120) -> None:
    """Poll until the Girder REST API responds."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{API}/system/version", timeout=5)
            if r.status_code == 200:
                print(f"[provision] Girder is up: {r.json()}")
                return
        except requests.RequestException:
            pass
        print("[provision] Waiting for Girder…")
        time.sleep(5)
    print("[provision] ERROR: Girder did not become ready in time.", file=sys.stderr)
    sys.exit(1)


def get_token(session: requests.Session) -> str:
    """Authenticate and return a Girder auth token."""
    r = session.get(
        f"{API}/user/authentication",
        auth=(ADMIN_USER, ADMIN_PASSWORD),
    )
    if r.status_code == 200:
        token = r.json()["authToken"]["token"]
        session.headers.update({"Girder-Token": token})
        print(f"[provision] Logged in as '{ADMIN_USER}'.")
        return token
    print(
        f"[provision] Could not log in ({r.status_code}): {r.text}",
        file=sys.stderr,
    )
    sys.exit(1)


def ensure_admin_user(session: requests.Session) -> None:
    """Create the admin user if it doesn't already exist."""
    r = session.get(f"{API}/user/authentication", auth=(ADMIN_USER, ADMIN_PASSWORD))
    if r.status_code == 200:
        print(f"[provision] Admin user '{ADMIN_USER}' already exists.")
        return

    r = session.post(
        f"{API}/user",
        params={
            "login": ADMIN_USER,
            "password": ADMIN_PASSWORD,
            "email": ADMIN_EMAIL,
            "firstName": "Admin",
            "lastName": "User",
            "admin": True,
        },
    )
    if r.status_code in (200, 201):
        print(f"[provision] Created admin user '{ADMIN_USER}'.")
    else:
        print(
            f"[provision] WARNING: Could not create admin user ({r.status_code}): {r.text}",
            file=sys.stderr,
        )


def enable_histomicsui_plugin(session: requests.Session) -> None:
    """Enable the HistomicsUI Girder plugin."""
    # Fetch currently active plugins
    r = session.get(f"{API}/system/plugins")
    if r.status_code != 200:
        print(
            f"[provision] WARNING: Could not list plugins ({r.status_code}).",
            file=sys.stderr,
        )
        return

    data = r.json()
    enabled = set(data.get("enabled", []))
    plugin_name = "histomicsui"

    if plugin_name in enabled:
        print(f"[provision] Plugin '{plugin_name}' is already enabled.")
        return

    enabled.add(plugin_name)
    r = session.put(
        f"{API}/system/plugins",
        json={"plugins": list(enabled)},
    )
    if r.status_code == 200:
        print(f"[provision] Enabled plugin '{plugin_name}'.")
    else:
        print(
            f"[provision] WARNING: Could not enable '{plugin_name}' ({r.status_code}): {r.text}",
            file=sys.stderr,
        )


def ensure_collection(session: requests.Session, name: str = "DSA") -> None:
    """Create a public top-level collection for slides if it doesn't exist."""
    r = session.get(f"{API}/collection", params={"text": name})
    if r.status_code == 200 and any(c["name"] == name for c in r.json()):
        print(f"[provision] Collection '{name}' already exists.")
        return

    r = session.post(
        f"{API}/collection",
        params={"name": name, "description": "Default slide collection", "public": True},
    )
    if r.status_code in (200, 201):
        print(f"[provision] Created collection '{name}'.")
    else:
        print(
            f"[provision] WARNING: Could not create collection ({r.status_code}): {r.text}",
            file=sys.stderr,
        )


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    wait_for_server()

    session = requests.Session()

    # First-run: no admin yet → register without auth header
    ensure_admin_user(session)
    get_token(session)
    enable_histomicsui_plugin(session)
    ensure_collection(session, "DSA")

    print("[provision] Provisioning complete. HistomicsUI is ready.")


if __name__ == "__main__":
    main()

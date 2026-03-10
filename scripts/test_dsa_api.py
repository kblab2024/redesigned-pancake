#!/usr/bin/env python3
"""
test_dsa_api.py — Smoke-test the Digital Slide Archive REST API.

This script exercises the most common workflows:
  1. Authenticate as admin and verify the server version.
  2. List available collections.
  3. Create a temporary test folder and upload a small synthetic PNG.
  4. Verify the upload via the items API.
  5. Clean up (delete the test folder).

Usage:
    python3 scripts/test_dsa_api.py [--host HOST] [--port PORT]
                                    [--user USER] [--password PASSWORD]

Example:
    python3 scripts/test_dsa_api.py
    python3 scripts/test_dsa_api.py --host localhost --port 8080
"""

import argparse
import io
import struct
import sys
import zlib

import requests


# ── Argument parsing ───────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="DSA REST API smoke test")
    p.add_argument("--host", default="localhost", help="DSA host (default: localhost)")
    p.add_argument("--port", default=8080, type=int, help="DSA port (default: 8080)")
    p.add_argument("--user", default="admin", help="Admin username (default: admin)")
    p.add_argument("--password", default="password", help="Admin password (default: password)")
    return p.parse_args()


# ── Minimal synthetic PNG factory ─────────────────────────────────────────────

def _make_png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    """Build a single PNG chunk."""
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def make_tiny_png(width: int = 4, height: int = 4) -> bytes:
    """Return a minimal valid 4×4 RGB PNG as bytes."""
    # Signature
    sig = b"\x89PNG\r\n\x1a\n"
    # IHDR: width, height, bit depth=8, colour=2 (RGB), compression=0, filter=0, interlace=0
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = _make_png_chunk(b"IHDR", ihdr_data)
    # IDAT: raw scanlines (filter byte 0x00 per row) → deflate compressed
    raw_rows = b"".join(b"\x00" + b"\xFF\x00\x00" * width for _ in range(height))
    idat = _make_png_chunk(b"IDAT", zlib.compress(raw_rows))
    # IEND
    iend = _make_png_chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


# ── API helpers ────────────────────────────────────────────────────────────────

class DSAClient:
    """Thin wrapper around the Girder REST API."""

    def __init__(self, base_url: str, user: str, password: str) -> None:
        self.base = base_url.rstrip("/")
        self.session = requests.Session()
        self._authenticate(user, password)

    def _authenticate(self, user: str, password: str) -> None:
        r = self.session.get(
            f"{self.base}/user/authentication",
            auth=(user, password),
            timeout=10,
        )
        _check(r, "Authentication")
        token = r.json()["authToken"]["token"]
        self.session.headers.update({"Girder-Token": token})
        print(f"  ✓ Authenticated as '{user}'")

    def server_version(self) -> dict:
        r = self.session.get(f"{self.base}/system/version", timeout=10)
        _check(r, "Server version")
        return r.json()

    def list_collections(self) -> list:
        r = self.session.get(f"{self.base}/collection", timeout=10)
        _check(r, "List collections")
        return r.json()

    def find_collection(self, name: str) -> dict | None:
        for col in self.list_collections():
            if col["name"] == name:
                return col
        return None

    def create_folder(self, parent_id: str, parent_type: str, name: str) -> dict:
        r = self.session.post(
            f"{self.base}/folder",
            params={
                "parentType": parent_type,
                "parentId": parent_id,
                "name": name,
                "public": False,
                "reuseExisting": True,
            },
            timeout=10,
        )
        _check(r, f"Create folder '{name}'")
        return r.json()

    def upload_file(self, folder_id: str, filename: str, data: bytes) -> dict:
        # Step 1: create upload session
        r = self.session.post(
            f"{self.base}/file",
            params={
                "parentType": "folder",
                "parentId": folder_id,
                "name": filename,
                "size": len(data),
                "mimeType": "image/png",
            },
            timeout=10,
        )
        _check(r, "Create upload session")
        upload_id = r.json()["_id"]

        # Step 2: send file bytes
        r = self.session.post(
            f"{self.base}/file/chunk",
            params={"uploadId": upload_id, "offset": 0},
            data=data,
            headers={"Content-Type": "application/octet-stream"},
            timeout=30,
        )
        _check(r, "Upload chunk")
        return r.json()

    def list_items(self, folder_id: str) -> list:
        r = self.session.get(
            f"{self.base}/item",
            params={"folderId": folder_id},
            timeout=10,
        )
        _check(r, "List items")
        return r.json()

    def delete_folder(self, folder_id: str) -> None:
        r = self.session.delete(f"{self.base}/folder/{folder_id}", timeout=10)
        _check(r, "Delete folder")


def _check(r: requests.Response, label: str) -> None:
    if r.status_code not in (200, 201):
        print(
            f"\n❌ {label} failed (HTTP {r.status_code}):\n{r.text}",
            file=sys.stderr,
        )
        sys.exit(1)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    base_url = f"http://{args.host}:{args.port}/api/v1"

    print(f"\n🔬 DSA REST API smoke test → {base_url}\n")
    print("── Step 1: Authentication ─────────────────────────────────────────")
    client = DSAClient(base_url, args.user, args.password)

    print("\n── Step 2: Server version ─────────────────────────────────────────")
    version = client.server_version()
    print(f"  ✓ Server: {version.get('release', version)}")

    print("\n── Step 3: Collections ────────────────────────────────────────────")
    collections = client.list_collections()
    if collections:
        for col in collections:
            print(f"  • {col['name']}  (id={col['_id']})")
    else:
        print("  (no collections found)")

    print("\n── Step 4: Upload test ────────────────────────────────────────────")
    # Find or use the first available collection
    col = client.find_collection("DSA") or (collections[0] if collections else None)
    if col is None:
        print("  ⚠  No collection available – skipping upload test.", file=sys.stderr)
    else:
        folder = client.create_folder(col["_id"], "collection", "_api_test_tmp")
        print(f"  ✓ Created folder '{folder['name']}' (id={folder['_id']})")

        png_bytes = make_tiny_png()
        uploaded = client.upload_file(folder["_id"], "test_image.png", png_bytes)
        print(f"  ✓ Uploaded 'test_image.png' ({len(png_bytes)} bytes)")

        items = client.list_items(folder["_id"])
        assert any(i["name"] == "test_image.png" for i in items), "Uploaded item not found!"
        print(f"  ✓ Item visible in folder listing ({len(items)} item(s))")

        client.delete_folder(folder["_id"])
        print("  ✓ Cleaned up test folder")

    print("\n✅ All checks passed — DSA REST API is functional.\n")


if __name__ == "__main__":
    main()

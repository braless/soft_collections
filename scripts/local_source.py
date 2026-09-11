#!/usr/bin/env python3
"""Build apps/Local/apps.json from the IPA files committed in apps/Local/.

Every other folder under apps/ is backed by a GitHub repository and generated
with ``uvx altgen``. Local is not: drop a .ipa into apps/Local/, commit it, and
this script turns the folder into an ordinary AltStore source — completely
offline.

  * app identity (name, bundle identifier, version, build number, minimum iOS
    version) is read from the IPA's own Info.plist, so nothing has to be filled
    in per file;
  * several IPAs sharing a bundle identifier become several versions of one
    app, newest first;
  * the icon is taken from the IPA (Apple's "CgBI" PNGs are re-encoded into
    standard PNGs) unless apps/Local/icons/<bundle-id>.png already exists;
  * no screenshots and no news images are generated, by design.

Download URLs point at the committed files, so the raw URL of an IPA is its
download URL.

Run from anywhere:  python3 scripts/local_source.py
"""

from __future__ import annotations

import json
import plistlib
import re
import struct
import subprocess
import sys
import zipfile
import zlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DIR = ROOT / "apps" / "Local"
ICON_DIR = LOCAL_DIR / "icons"
CONFIG_PATH = LOCAL_DIR / "config.toml"
OUTPUT = LOCAL_DIR / "apps.json"

DEFAULT_SLUG = "braless/soft_collections"
RAW_PATH = "apps/Local"
GITHUB_FILE_LIMIT = 100 * 1024 * 1024  # GitHub rejects blobs above 100 MB

SOURCE_NAME = "Local"
SOURCE_SUBTITLE = "IPAs committed straight into this repository"
SOURCE_DESCRIPTION = (
    "Locally committed IPA builds. Generated from apps/Local/ by "
    "scripts/local_source.py — no GitHub release lookup involved."
)
DEFAULT_DEVELOPER = "Local"
DEFAULT_TINT = "#3B82F6"


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def repo_slug() -> str:
    """``owner/name`` of the origin remote, so raw URLs survive a rename."""
    try:
        url = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        url = ""
    match = re.search(r"github\.com[:/]([^/]+)/(.+?)(?:\.git)?/?$", url)
    return f"{match.group(1)}/{match.group(2)}" if match else DEFAULT_SLUG


def commit_date(path: Path) -> str:
    """YYYY-MM-DD of the last commit touching ``path`` (stable across runs).

    Falls back to the file's mtime when git is unavailable, e.g. for a file
    that has not been committed yet.
    """
    try:
        done = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path.relative_to(ROOT))],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        )
        if done.returncode == 0 and done.stdout.strip():
            return done.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d")


def version_key(version: str) -> tuple:
    """Sort key that orders 1.10 after 1.9 instead of lexicographically."""
    parts = re.split(r"[._\-+~]", version)
    return tuple((0, int(p)) if p.isdigit() else (1, p) for p in parts)


def version_from_filename(name: str) -> str:
    """Last dotted number in a file name: Foo-Bar-1.2.3.ipa -> 1.2.3."""
    match = re.search(r"(\d+(?:\.\d+)+)", name)
    return match.group(1) if match else ""


# ---------------------------------------------------------------------------
# PNG handling — iOS app bundles ship Apple "CgBI" PNGs Pillow cannot read
# ---------------------------------------------------------------------------

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _read_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    pos = 8
    chunks: list[tuple[bytes, bytes]] = []
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        ctype = data[pos + 4 : pos + 8]
        chunks.append((ctype, data[pos + 8 : pos + 8 + length]))
        pos += 12 + length
        if ctype == b"IEND":
            break
    return chunks


def png_size(data: bytes) -> tuple[int, int]:
    """Width/height from IHDR, which is at the same place in CgBI files."""
    for ctype, cdata in _read_chunks(data):
        if ctype == b"IHDR":
            width, height = struct.unpack(">II", cdata[:8])
            return width, height
    raise ValueError("no IHDR chunk")


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def _png_chunk(tag: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + tag
        + payload
        + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
    )


def _decode_cgbi(data: bytes) -> bytes | None:
    """Turn an Apple-optimised PNG into a standard one, or return None.

    CgBI files drop the zlib header, store premultiplied BGRA and may keep the
    raw deflate stream, so the scanlines have to be re-filtered by hand.
    """
    if data[12:16] != b"CgBI":
        return None
    chunks = _read_chunks(data)
    ihdr = next((c for t, c in chunks if t == b"IHDR"), None)
    if ihdr is None:
        return None
    width, height, depth, color_type = struct.unpack(">IIBB", ihdr[:10])
    if depth != 8 or color_type not in (2, 6):
        return None
    channels = 4 if color_type == 6 else 3
    stride = width * channels

    raw = zlib.decompress(b"".join(c for t, c in chunks if t == b"IDAT"), -15)
    rows: list[bytearray] = []
    prev = bytearray(stride)
    pos = 0
    for _ in range(height):
        ftype = raw[pos]
        pos += 1
        line = bytearray(raw[pos : pos + stride])
        pos += stride
        for i in range(stride):
            a = line[i - channels] if i >= channels else 0
            b = prev[i]
            c = prev[i - channels] if i >= channels else 0
            x = line[i]
            if ftype == 1:
                x += a
            elif ftype == 2:
                x += b
            elif ftype == 3:
                x += (a + b) >> 1
            elif ftype == 4:
                x += _paeth(a, b, c)
            line[i] = x & 0xFF
        rows.append(line)
        prev = line

    # BGRA -> RGBA, and undo premultiplication so the icon keeps its edges.
    for line in rows:
        for i in range(0, stride, channels):
            b, g, r = line[i], line[i + 1], line[i + 2]
            if channels == 4:
                a = line[i + 3]
                if 0 < a < 255:
                    r = min(255, r * 255 // a)
                    g = min(255, g * 255 // a)
                    b = min(255, b * 255 // a)
                line[i], line[i + 1], line[i + 2] = r, g, b
            else:
                line[i], line[i + 1], line[i + 2] = r, g, b

    body = b"".join(b"\x00" + bytes(line) for line in rows)
    header = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    return (
        PNG_SIGNATURE
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", zlib.compress(body, 9))
        + _png_chunk(b"IEND", b"")
    )


def normalise_png(data: bytes) -> bytes:
    """Standard PNG bytes: CgBI input is decoded, anything else passes through."""
    try:
        return _decode_cgbi(data) or data
    except (zlib.error, struct.error, IndexError, ValueError):
        return data


# ---------------------------------------------------------------------------
# IPA reading
# ---------------------------------------------------------------------------

def find_app_root(names: set[str]) -> str | None:
    """The ``....app/`` prefix of the main bundle inside an .ipa.

    The shallowest ``*.app`` that has an ``Info.plist`` right below it wins, so
    nested frameworks and bundles are ignored. Directory entries are optional
    in a zip, so the roots have to be derived from the file names themselves.
    """
    counts: dict[str, int] = {}
    for name in names:
        for match in re.finditer(r"(?:^|/)([^/]+\.app)/", name):
            root = name[: match.end()]
            counts[root] = counts.get(root, 0) + 1

    best: tuple[tuple[int, int, int], str] | None = None
    for root, count in counts.items():
        if root + "Info.plist" not in names:
            continue
        score = (0 if root.startswith("Payload/") else 1, root.count("/"), -count)
        if best is None or score < best[0]:
            best = (score, root)
    return best[1] if best else None


def read_ipa(path: Path) -> dict:
    """Identity of the app inside an .ipa, plus its best icon, if any."""
    if not zipfile.is_zipfile(path):
        raise ValueError("not a zip archive (a .ipa is a zip)")

    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        prefix = find_app_root(names)
        if prefix is None:
            raise ValueError("no *.app/Info.plist inside (not a normal .ipa?)")
        info = plistlib.loads(archive.read(prefix + "Info.plist"))

        icon_bytes: bytes | None = None
        best = -1
        for name in names:
            if not name.startswith(prefix) or "/" in name[len(prefix) :]:
                continue
            if not name.lower().endswith(".png"):
                continue
            data = archive.read(name)
            try:
                width, height = png_size(data)
            except (ValueError, struct.error, IndexError):
                continue
            if width * height > best:
                best = width * height
                icon_bytes = normalise_png(data)

    bundle_id = str(info.get("CFBundleIdentifier") or "").strip()
    if not bundle_id:
        raise ValueError("Info.plist has no CFBundleIdentifier")

    name = (
        info.get("CFBundleDisplayName")
        or info.get("CFBundleName")
        or path.stem
    )
    version = str(info.get("CFBundleShortVersionString") or "").strip()
    if not version:
        version = version_from_filename(path.name) or str(info.get("CFBundleVersion") or "1.0")

    return {
        "bundle_identifier": bundle_id,
        "name": str(name).strip() or path.stem,
        "version": version,
        "build": str(info.get("CFBundleVersion") or "").strip(),
        "min_os": str(info.get("MinimumOSVersion") or "").strip(),
        "icon": icon_bytes,
    }


def load_defaults() -> dict:
    """Optional apps/Local/config.toml — every value has a built-in default."""
    defaults = {"developer_name": DEFAULT_DEVELOPER, "tint_color": DEFAULT_TINT}
    if not CONFIG_PATH.exists():
        return defaults
    with open(CONFIG_PATH, "rb") as handle:
        config = tomllib.load(handle)
    table = config.get("defaults") or {}
    for key in defaults:
        if table.get(key):
            defaults[key] = str(table[key])
    return defaults


def existing_bundle_ids() -> dict[str, str]:
    """Bundle identifiers already provided by the generated app sources."""
    found: dict[str, str] = {}
    for source in sorted((ROOT / "apps").glob("*/apps.json")):
        if source.parent == LOCAL_DIR:
            continue
        try:
            document = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for app in document.get("apps") or []:
            bundle_id = app.get("bundleIdentifier")
            if bundle_id:
                found.setdefault(bundle_id, str(source.relative_to(ROOT)))
    return found


def main() -> int:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    ICON_DIR.mkdir(parents=True, exist_ok=True)

    defaults = load_defaults()
    slug = repo_slug()
    raw_base = f"https://raw.githubusercontent.com/{slug}/refs/heads/main/{RAW_PATH}"
    taken = existing_bundle_ids()

    ipas = sorted(
        (p for p in LOCAL_DIR.glob("*.ipa") if not p.name.startswith(".")),
        key=lambda p: p.name.casefold(),
    )
    if not ipas:
        print(f"no .ipa files in {LOCAL_DIR.relative_to(ROOT)} - writing an empty source")

    apps: dict[str, dict] = {}
    conflicts: list[str] = []
    failures: list[str] = []

    for ipa in ipas:
        size = ipa.stat().st_size
        if size > GITHUB_FILE_LIMIT:
            failures.append(
                f"{ipa.name}: {size / 1048576:.1f} MB — GitHub rejects files above 100 MB"
            )
            continue
        try:
            info = read_ipa(ipa)
        except (ValueError, zipfile.BadZipFile, plistlib.InvalidFileException) as exc:
            failures.append(f"{ipa.name}: {exc}")
            continue

        bundle_id = info["bundle_identifier"]
        if bundle_id in taken:
            conflicts.append(f"{ipa.name}: {bundle_id} is already in {taken[bundle_id]}")
            continue

        # Icon: a hand-placed override wins, then a sidecar next to the IPA,
        # then whatever came out of the bundle.
        icon_path = ICON_DIR / f"{bundle_id}.png"
        sidecar = ipa.with_suffix(".png")
        if icon_path.exists():
            pass
        elif sidecar.exists():
            icon_path.write_bytes(sidecar.read_bytes())
        elif info["icon"]:
            icon_path.write_bytes(info["icon"])

        date = commit_date(ipa)
        description = f"Locally committed build: {ipa.name} ({size / 1048576:.1f} MB)."
        if info["build"]:
            description += f" Build {info['build']}."
        version_entry = {
            "version": info["version"],
            "date": date,
            "localizedDescription": description,
            # Percent-encoded: AltStore hands this string to URL(string:),
            # which rejects raw non-ASCII characters.
            "downloadURL": f"{raw_base}/{quote(ipa.name)}",
            "size": size,
        }
        if info["build"]:
            version_entry["buildVersion"] = info["build"]
        if info["min_os"]:
            version_entry["minOSVersion"] = info["min_os"]

        app = apps.get(bundle_id)
        if app is None:
            app = {
                "name": info["name"],
                "bundleIdentifier": bundle_id,
                "developerName": defaults["developer_name"],
                "subtitle": "Locally committed IPA",
                "localizedDescription": (
                    f"{info['name']} — committed to this repository as an IPA "
                    f"under {RAW_PATH}/."
                ),
                "tintColor": defaults["tint_color"],
                "versions": [],
            }
            if icon_path.exists():
                app["iconURL"] = f"{raw_base}/icons/{quote(icon_path.name)}"
            apps[bundle_id] = app
        elif "iconURL" not in app and icon_path.exists():
            app["iconURL"] = f"{raw_base}/icons/{quote(icon_path.name)}"

        app["versions"].append(version_entry)
        print(f"  {ipa.name}: {info['name']} {info['version']} ({bundle_id})")

    for app in apps.values():
        app["versions"].sort(key=lambda v: version_key(v["version"]), reverse=True)
        # Same version twice (two signed copies, say): keep the newest one.
        unique: list[dict] = []
        for entry in app["versions"]:
            if not any(other["version"] == entry["version"] for other in unique):
                unique.append(entry)
        app["versions"] = unique

    document = {
        "name": SOURCE_NAME,
        "subtitle": SOURCE_SUBTITLE,
        "description": SOURCE_DESCRIPTION,
        "iconURL": f"https://raw.githubusercontent.com/{slug}/refs/heads/main/assets/icon.png",
        "website": f"https://github.com/{slug}",
        "tintColor": defaults["tint_color"],
        "apps": sorted(apps.values(), key=lambda a: a["name"].casefold()),
    }
    OUTPUT.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({len(apps)} app(s), {len(ipas)} IPA file(s))")

    if conflicts:
        print("\nerror: these IPAs clash with an app that already has a source:", file=sys.stderr)
        for line in conflicts:
            print(f"  {line}", file=sys.stderr)
        print("  all-apps.json cannot hold two apps with one bundle identifier.", file=sys.stderr)
    if failures:
        print("\nerror: these files could not be used:", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
    return 1 if (conflicts or failures) else 0


if __name__ == "__main__":
    sys.exit(main())

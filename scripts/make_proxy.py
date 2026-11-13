#!/usr/bin/env python3
"""Build a gh-proxy.com mirror of one or more AltStore sources.

GitHub can be unreachable or slow from mainland China, so the files a source
points at may fail to load even when the source JSON is reachable. This script
prefixes only the URLs AltStore/SideStore actually fetches:

  https://raw.githubusercontent.com/...                        -> https://gh-proxy.com/<same>
  https://github.com/<owner>/<repo>/releases/download/...      -> https://gh-proxy.com/<same>
  https://github.com/<owner>/<repo>/releases/latest/download/  -> https://gh-proxy.com/<same>

GitHub pages opened in a browser (`website`, `news[].url`, release tag links)
are deliberately left untouched. Running the script on an already-proxied file
is a no-op. Only the standard library is required.

Usage:
  python3 scripts/make_proxy.py                                  # all-apps.json -> all-apps-proxy.json
  python3 scripts/make_proxy.py apps/Foo/apps.json apps/Foo/apps-proxy.json
  python3 scripts/make_proxy.py --all                            # root + every app source
  python3 scripts/make_proxy.py --prefix https://gh-proxy.com/
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PREFIX = "https://gh-proxy.com/"
RAW_HOST_PREFIX = "https://raw.githubusercontent.com/"

# Match release asset downloads, including GitHub's /latest/download/ spelling.
# Release pages under /releases/tag/ are intentionally excluded.
RELEASE_DOWNLOAD = re.compile(
    r"^https://github\.com/[^/]+/[^/]+/releases/(?:latest/)?download/"
)


def is_fetch_url(value: str) -> bool:
    """Return True for GitHub file URLs that should go through the proxy."""
    return value.startswith(RAW_HOST_PREFIX) or RELEASE_DOWNLOAD.match(value) is not None


def rewrite(node: object, prefix: str, counter: list[int]) -> object:
    """Recursively prefix GitHub fetch URLs while copying all other values."""
    if isinstance(node, str):
        if is_fetch_url(node):
            counter[0] += 1
            return prefix + node
        return node
    if isinstance(node, list):
        return [rewrite(item, prefix, counter) for item in node]
    if isinstance(node, dict):
        return {key: rewrite(value, prefix, counter) for key, value in node.items()}
    return node


def generate(input_path: Path, output_path: Path, prefix: str) -> int | None:
    """Write one proxy source; return the rewritten URL count, or None on error."""
    try:
        source = json.loads(input_path.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"Error: cannot read {input_path}: {exc}", file=sys.stderr)
        return None
    except json.JSONDecodeError as exc:
        print(f"Error: {input_path} is not valid JSON: {exc}", file=sys.stderr)
        return None

    counter = [0]
    proxied = rewrite(source, prefix, counter)

    # newline="\n" keeps generated JSON in LF, matching the tracked sources.
    try:
        with output_path.open("w", encoding="utf-8", newline="\n") as output:
            json.dump(proxied, output, ensure_ascii=False, indent=2)
            output.write("\n")
    except OSError as exc:
        print(f"Error: cannot write {output_path}: {exc}", file=sys.stderr)
        return None

    print(f"Rewrote {counter[0]} GitHub URL(s): {input_path} -> {output_path}")
    return counter[0]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write gh-proxy.com mirrors of AltStore sources."
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        help="source to read (default: <repo>/all-apps.json)",
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        help="file to write (default: <repo>/all-apps-proxy.json)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="generate a proxy mirror for the combined source and every apps/*/apps.json",
    )
    parser.add_argument(
        "--prefix",
        default=DEFAULT_PREFIX,
        help=f"proxy to prepend to GitHub URLs (default: {DEFAULT_PREFIX})",
    )
    args = parser.parse_args()

    if args.all and (args.input or args.output):
        parser.error("--all cannot be combined with input/output paths")

    if args.all:
        sources: list[tuple[Path, Path]] = []
        combined = REPO_ROOT / "all-apps.json"
        if combined.is_file():
            sources.append((combined, REPO_ROOT / "all-apps-proxy.json"))
        sources.extend(
            (source, source.with_name("apps-proxy.json"))
            for source in sorted((REPO_ROOT / "apps").glob("*/apps.json"))
        )

        if not sources:
            print("No AltStore sources found — nothing to proxy.")
            return 0

        rewritten = 0
        for input_path, output_path in sources:
            count = generate(input_path, output_path, args.prefix)
            if count is None:
                return 1
            rewritten += count
        print(f"Generated {len(sources)} proxy source(s), rewrote {rewritten} GitHub URL(s).")
        return 0

    input_path = args.input if args.input is not None else REPO_ROOT / "all-apps.json"
    output_path = args.output if args.output is not None else REPO_ROOT / "all-apps-proxy.json"
    return 0 if generate(input_path, output_path, args.prefix) is not None else 1


if __name__ == "__main__":
    sys.exit(main())
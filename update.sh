#!/usr/bin/env bash
# soft_collections — regenerate app source(s), then merge them into the repo-root all-apps.json.
# Run: ./update.sh              (regenerate every app source, then merge)
#      ./update.sh <AppName>    (regenerate just one app, then merge)
# A single-app run is enough for local verification after editing a
# config.toml — the CI workflow regenerates and commits everything on push,
# so there is no need to update every app locally.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

target="${1:-}"

if [[ -n "$target" && ! -f "apps/$target/config.toml" ]]; then
  echo "Error: no config.toml at apps/$target/config.toml" >&2
  echo "Usage: ./update.sh [<AppName>]" >&2
  exit 1
fi

# apps/Local holds committed IPAs rather than a GitHub repo. A full run leaves
# it alone (local.yml regenerates it on every apps/Local change), but asking
# for it explicitly regenerates it offline.
if [[ "$target" == "Local" ]]; then
  echo "==> Updating apps/Local (offline, from the committed IPAs)"
  "${PYTHON:-python3}" scripts/local_source.py
fi

# 1. Regenerate each apps/<AppName>/apps.json from its config.toml —
#    every app, or only the targeted one.
#    apps/Local/ is skipped on purpose: it holds committed IPAs rather than a
#    GitHub repo, and scripts/local_source.py builds its source offline
#    (.github/workflows/local.yml runs it on every apps/Local change).
for app_dir in apps/*/; do
  if [[ "$app_dir" == "apps/Local/" ]]; then
    continue
  fi
  if [[ -f "$app_dir/config.toml" ]]; then
    name="${app_dir%/}"
    if [[ -n "$target" && "$name" != "apps/$target" ]]; then
      continue
    fi
    echo "==> Updating $name"
    (cd "$app_dir" && uvx altgen -c config.toml)
  fi
done

# 2. Merge every existing source into the repo-root all-apps.json. All sources
#    are inputs whether or not they were regenerated this run, so the merged
#    file always reflects the full gallery.
apps=()
for app_dir in apps/*/; do
  if [[ -f "$app_dir/apps.json" ]]; then
    apps+=("$app_dir/apps.json")
  fi
done

if [[ ${#apps[@]} -gt 0 ]]; then
  echo "==> Merging ${#apps[@]} source(s) into all-apps.json"
  uvx altgen merge -c assets/merge.toml "${apps[@]}"
else
  echo "No app sources found — nothing to merge."
fi

# soft_collections — Agent Guide

## Project Goal

Generate AltStore sources (`apps.json`) for IPA projects on GitHub.

- Generator: Python **AltGen**, invoked via `uvx altgen`

## Comments

Write comments in English. Any comment you add or modify in code
(`config.toml`, Python, shell scripts, etc.) must be written in English —
never in Chinese or other languages.

## Reading JSON

Prefer `jq` to read or inspect JSON files (`apps.json`, `all-apps.json`), e.g.
`jq '.apps | length' PiliPlus/apps.json` or `jq '.apps[0]' PiliPlus/apps.json`.
Only read the full file when you actually need the whole content.

## Directory Layout

Each IPA gets its own folder under `apps/`, e.g. `apps/PiliPlus/`:

```
apps/<AppName>/
├── config.toml      # altgen configuration file
├── news.toml        # news image config (name, tagline, optional colors)
├── icon.png         # app icon
├── images/          # screenshots + news.png promo image
│   ├── home.png     # screenshots (referenced from [app] screenshots)
│   └── news.png     # generated promo image (referenced from [news] image_url)
└── apps.json        # generated AltStore source (gitignored), do not hand-edit
```

Each folder's `apps.json` is an independent AltStore source.

## apps/Local — hand-committed IPAs

`apps/Local/` is the one folder that is **not** an altgen source. It holds
`.ipa` files committed by hand, and its `config.toml` carries defaults for the
offline generator rather than altgen settings.

- **Never run `uvx altgen -c config.toml` inside `apps/Local`** — `update.sh`
  skips the folder for exactly that reason.
- `scripts/local_source.py` (Python standard library only, no network) reads
  each IPA's `Info.plist` for name/bundle id/version/build/min iOS version,
  extracts an icon into `apps/Local/icons/`, and writes
  `apps/Local/apps.json`. Never hand-write those entries.
- `.github/workflows/local.yml` runs that script and merges the result into
  `all-apps.json`; `update.yml` ignores the folder (`paths-ignore`) but still
  merges `apps/Local/apps.json` with every other source, because `update.sh`
  collects all `apps/*/apps.json`.
- `apps/Local/apps.json` is gitignored like every other generated source;
  `apps/Local/icons/` is committed.
- A bundle identifier that already exists in another folder is a hard error:
  the merge rejects duplicates.

## Generating apps.json

`./update.sh` regenerates every app source and merges them into
`all-apps.json`. After editing a `config.toml`, regenerate just that app to
verify it — you don't need to update the other apps locally (the CI workflow
regenerates and commits everything on push):

```bash
./update.sh <AppName>                            # single app — enough for local verification
cd apps/<AppName> && uvx altgen -c config.toml   # equivalent, lower-level; note: config.toml, not config.json
```

altgen reads the GitHub Releases API; if rate-limited or the repo is private,
pass a token (`--token` > `GITHUB_TOKEN` env > `[github].token` in
config.toml).

**Rule: after ANY `config.toml` change, regenerate — never leave the two out
of sync, and never hand-edit `apps.json`.**

`.github/workflows/update.yml` regenerates and commits `apps.json` and
`all-apps.json` on every push to `main`, every 6 hours, and on manual
`workflow_dispatch`. (Both files are tracked despite `.gitignore`, so leave
any local regenerated changes for the workflow to commit.)

## Merging into all-apps.json

After all app sources are regenerated, merge them into the repo-root
`all-apps.json` (the "ultimate" AltStore source for the whole project).
The whole flow — regenerate every source, then merge — is scripted in
`./update.sh` (run from anywhere); prefer it over the individual commands.

```bash
uvx altgen merge -c assets/merge.toml apps/<AppName>/apps.json ...
```

Pass **every** `apps/<AppName>/apps.json` in the repo as an input. The merge
config lives in `assets/merge.toml`: merge mode only reads `[source]` (root
metadata: name, icon_url, tint_color) and `[output]` (`path = "../all-apps.json"`,
resolved against the config's directory → repo root).

**Rule: after any `config.toml` change, regenerate with `./update.sh
<AppName>` and check the diff — never leave `config.toml` and its `apps.json`
out of sync. You don't need the full `./update.sh` locally: `apps.json` and
`all-apps.json` are regenerated and committed by the CI workflow on every push
to `main`, so a single-app run is enough to verify the sources. (Both files
are tracked despite `.gitignore`, so a local regenerate shows them as modified
in `git status` — leave them for the workflow to commit.) To refresh them
immediately, run the `Update all-apps.json` workflow manually
(`workflow_dispatch`).**

## Generating News Images

Each app has a shared `news.png` ("NEW UPDATE" — icon, name, tagline)
referenced by all its news entries via `[news] image_url`. Re-render every
app's image (from each app's `news.toml`: `name`, `tagline`, optional
`[colors]`) with:

```bash
./update_news.sh
```

or a single app with `.venv/bin/python3 templates/render_news.py --out
apps/<AppName>`.
Unset colors are auto-derived from `config.toml` tints and the icon's dominant
color (needs the uv venv set up once: `uv venv && uv pip install -r
requirements.txt`; Pillow is the only image dependency — no external
rasterizer). The rendered `apps/<AppName>/images/news.png` stays in the working
tree — the URL in `config.toml` `[news] image_url` already points at it. Do
not auto-commit it.

## Icon Color Sampling (PIL)

Sampling a dominant color from an icon — for a new app's `tint_color`, or the
news background derived by `render_news.py` — is already implemented in
`templates/render_news.py` → `extract_icon_color()` (it downsamples the icon
with Pillow and buckets the pixels). Just call it:

```bash
PYTHONPATH=templates .venv/bin/python3 -c \
  "from render_news import extract_icon_color; from pathlib import Path; \
   print(extract_icon_color(Path('apps/<AppName>/icon.png')))"
```

**Pillow/PIL is installed only in the project venv (`.venv/`), not in the
system Python** — any command that imports PIL (`render_news.py`,
`extract_icon_color`) must run with the venv's interpreter:
`.venv/bin/python3` (or `source .venv/bin/activate` first). The bare system
`python3` will raise `ModuleNotFoundError: No module named 'PIL'`.

When a new app lacks an official tint, use the result as `[app] tint_color`
(brand color) — but eyeball the icon first: a multi-color or pale icon may
not have an obvious single brand color, so the sample needs human
confirmation.

## Adding a New App

End-to-end procedure lives in the **add-app** skill — invoke it with
`/add-app` (it also auto-loads when you ask to add a new app). It covers
extracting fields from the project's own AltStore source (when one exists),
the folder/config/icon/news setup, tint sampling, `apps.json` generation,
merge, and README update. The reference sections below ([Icon Color Sampling
(PIL)](#icon-color-sampling-pil), [Generating News
Images](#generating-news-images), [Merging into
all-apps.json](#merging-into-all-appsjson)) remain authoritative for the
shared details.

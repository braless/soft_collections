---
name: add-app
description: Add a new app to the soft_collections repo. When the project already ships its own AltStore source (apps.json), extracts the fields it needs from that source to pre-fill config.toml. Creates apps/<AppName>/, writes config.toml and news.toml, downloads icon + screenshots, samples a tint color from the icon, renders images/news.png, generates apps.json with altgen (local verification only), and adds the README "Available Apps" entry. Both apps.json and all-apps.json are generated and committed by the CI workflow — never update or commit them locally. Use whenever the user wants to add a new app / a new IPA source to the gallery.
---

# Adding a New App to soft_collections

End-to-end procedure for adding one IPA project to the gallery. Shared
reference details (icon color sampling, news rendering) live in AGENTS.md —
the key gotchas are inlined here, and links point at the full sections.

When the project already ships its own AltStore source, extract its metadata
first (step 2) so `config.toml` is pre-filled from the source instead of being
re-derived from the README by hand.

## Procedure

1. **Create the folder**
   ```bash
   mkdir -p apps/<AppName>/images
   ```
   Use the project's display name (match the GitHub repo's casing).

2. **Extract fields from the project's AltStore source (when it provides one)**

   Many projects maintain their own AltStore source — an `apps.json` — in the
   repo (repo root, an `altstore`/`AltStore` folder, or a dedicated branch) or
   hosted and linked from the README (often an "AltStore" / "Add to AltStore"
   badge). When one exists, prefer it as the source of truth for the fields
   below over hand-deriving them. **altgen regenerates the version list from
   GitHub Releases, so only the app-level metadata and the latest version are
   needed — not the full version history.**

   a. **Locate it** — grep the README for a source URL or `apps.json` path, or
      list the repo tree:
      ```bash
      # any JSON links in the README (source URL, altstore badge)
      curl -sL https://raw.githubusercontent.com/<owner>/<repo>/<default-branch>/README.md \
        | grep -oE 'https?://[^ )">]+\.json' | sort -u
      ```
   b. **Fetch and inspect** it (pick the `.apps[]` entry matching the app):
      ```bash
      curl -sL <source-url> \
        | jq '.apps[0] | {name, bundleIdentifier, developerName, subtitle, localizedDescription, iconURL, tintColor, minOSVersion: .versions[0].minOSVersion, downloadURL: .versions[0].downloadURL}'
      ```
   c. **Map to `config.toml`** (AltStore JSON key → TOML key):

      | AltStore source field | `config.toml` |
      |---|---|
      | `apps[0].name` | `[app] name` (and the folder name) |
      | `apps[0].bundleIdentifier` | `[app] bundle_identifier` |
      | `apps[0].developerName` | `[app] developer_name` |
      | `apps[0].subtitle` | `[app] subtitle` |
      | `apps[0].localizedDescription` | `[app] description` (trim long release-note blobs) |
      | `apps[0].tintColor` | `[app] tint_color` — ⚠️ AltStore stores it **without** `#` (e.g. `ff375f`); write it as `#ff375f` |
      | `apps[0].screenshots` (objects' `imageURL`, or strings) | download to `images/*` (step 3) |
      | `apps[0].versions[0].minOSVersion` | `[app] min_os_version` |
      | `apps[0].versions[0].downloadURL` | ipa filename → `[versions] asset_pattern` |
      | `apps[0].versions[0].version` | leading `v` → `[versions] strip_v_prefix` |
      | root `name` / `subtitle` / `description` / `website` | `[source] *` |

   d. **Caveats**
      - Still download the icon/screenshots into `apps/<AppName>/` and point
        `icon_url` / `screenshots` at the
        `raw.githubusercontent.com/braless/soft_collections/...` URLs — **never** copy
        the source's remote asset URLs into `config.toml`; soft_collections hosts its
        own copies.
      - `localizedDescription` is often a release-note-style blob; shorten it
        for `[app] description` (a one-to-two sentence summary reads better).
      - When the source has no `tintColor`, sample one from the icon instead
        (step 5).
      - If the repo provides no source (or it is stale/broken), skip this step
        and derive the fields from the README as before.

3. **Download icon and screenshots**
   Fetch from the project's GitHub repo (e.g. `raw.githubusercontent.com`, or
   the repo's `assets/` folder) into `apps/<AppName>/icon.png` and
   `apps/<AppName>/images/*.png` (~3 portrait shots, e.g. `home.png`,
   `detail.png`, `comment.png`). When a source was found in step 2, its
   `iconURL` / `screenshots` tell you exactly which files to grab.

   ⚠️ **If no screenshots can be found** (no `screenshots` field in the source,
   no `images`/`assets` folder in the repo, README links broken, etc.), still
   download the icon and finish the rest of the flow — just remember that the
   screenshots are missing, and output the warning at the end (step 10).

4. **Write `config.toml`** modeled on `apps/PiliPlus/config.toml`:
   - `[github]`: `repo = "owner/name"`
   - `[source]`: name, subtitle, description, `website`, and `icon_url`
     pointing at the new app's committed icon
   - `[app]`: name, `bundle_identifier`, `developer_name`, subtitle,
     description, `icon_url`, `screenshots` (the
     `https://raw.githubusercontent.com/braless/soft_collections/main/apps/<AppName>/images/*.png`
     URLs), `tint_color`, `min_os_version`
   - `[versions]`: matching rules. ⚠️ **`asset_pattern` is a regex, not a
     glob** — to match any ipa use `".*\\.ipa$"`; `"*.ipa"` fails with
     `invalid regex`. Narrow it to a specific filename when each release
     ships exactly one ipa (e.g. `"EhPanda\\.ipa$"`). Use the latest
     `downloadURL` from step 2 to get the exact ipa filename.
   - `[news]`: copy the PiliPlus block, point `image_url` at the new app's
     `images/news.png`
   - `[output]`: `path = "apps.json"`
   - All `raw.githubusercontent.com` URLs use the `braless/soft_collections`
     repo path.

5. **Sample a tint color** (when the project has no official brand color in
   its AltStore source — otherwise reuse the source's `tintColor` directly):
   call the existing sampler in `templates/render_news.py` →
   `extract_icon_color()` instead of re-implementing the PIL sampling (see
   AGENTS.md → [Icon Color Sampling](#icon-color-sampling-pil)):
   ```bash
   PYTHONPATH=templates python3 -c "from render_news import extract_icon_color; from pathlib import Path; print(extract_icon_color(Path('apps/<AppName>/icon.png')))"
   ```
   ⚠️ **Eyeball the result — human confirmation required.** Multi-color or
   pale icons may not have an obvious single brand color.

6. **Write `news.toml`** (`name`, `tagline`, optional `[colors]`), then
   render the shared promo image (AGENTS.md → [Generating News Images]):
   ```bash
   ./.venv/bin/python templates/render_news.py --out apps/<AppName>
   ```
   Renders `apps/<AppName>/images/news.png` (1600x1200, 4:3) into the working
   tree (do not auto-commit). The image is drawn entirely with Pillow — no
   external rasterizer needed. ⚠️ **Use the venv interpreter** (same as
   `update_news.sh`): bare `python3` has no Pillow, so `render_news.py` fails
   with an import error.

7. **Generate `apps.json`** — **never hand-edit it**:
   ```bash
   cd apps/<AppName> && uvx altgen -c config.toml
   ```
   ⚠️ **After ANY `config.toml` change, regenerate** — never leave config and
   `apps.json` out of sync. If rate-limited or fetching from a private repo,
   use `GITHUB_TOKEN=$(gh auth token) uvx altgen -c config.toml`. This local
   run only **verifies** `config.toml` — the resulting `apps.json` is
   gitignored (it won't show in `git status`). The workflow
   (`.github/workflows/update.yml`) regenerates and commits the real
   `apps.json` — same as `all-apps.json` — after your change merges.

8. **Do NOT commit `all-apps.json`** — like `apps.json`, the repo-root JSON is
   generated and committed by the CI workflow
   (`.github/workflows/update.yml`) after your change merges; never commit
   either file locally. To verify the new app's source after its `config.toml`
   is written, the single-app form is fine: `./update.sh <AppName>` only
   regenerates this app's `apps.json` (no other app is touched). It still
   rewrites the tracked `all-apps.json`, so an unstaged `M` shows in
   `git status` — leave it for the workflow. Your change ships only
   `apps/<AppName>/` plus the README entry.

9. **Update README** — add the app to **Available Apps**, icon inline before
   the name:
   ```html
   ### <a href="https://github.com/owner/name"><img src="https://raw.githubusercontent.com/braless/soft_collections/main/apps/<AppName>/icon.png" alt="<AppName> icon" width="24" align="top"> <AppName></a>
   Short one-line description.
   ```
   ⚠️ Use `align="top"` on the icon — `align="center"` renders ~7px low on
   GitHub.

10. **Warn if no screenshots were found** — this is the LAST step. If step 3
    could not obtain any screenshots (empty `apps/<AppName>/images/`, no
    `screenshots` field in the source, no `images`/`assets` folder in the repo,
    broken URLs, …), output an explicit warning to the user before finishing.
    Example:

    ```
    ⚠️ Warning: no screenshots found for <AppName> — apps/<AppName>/images/ is
    empty. The app will show without screenshots in the gallery. When you have
    screenshots, drop them into apps/<AppName>/images/ and update the
    `[app] screenshots` list in config.toml (then regenerate apps.json).
    ```

    This warning is required — never end the add-app flow silently while
    screenshots are missing.

## Checklist
- [ ] fields extracted from the project's own AltStore source (when one exists); `tintColor` normalized to `#RRGGBB`
- [ ] `apps/<AppName>/{config.toml, news.toml, icon.png, images/*}` all present
- [ ] icon/screenshots hosted locally and referenced via `braless/soft_collections` raw URLs (never the source's remote URLs)
- [ ] `apps.json` regenerated after the last config change; never hand-edited; gitignored (not committed)
- [ ] `all-apps.json` NOT touched — CI workflow regenerates and commits it
- [ ] `images/news.png` rendered; not auto-committed
- [ ] README entry added, icon with `align="top"`
- [ ] if no screenshots could be found, the user was explicitly warned (never proceed silently)

<p align="center">
  <img src="https://raw.githubusercontent.com/braless/soft_collections/main/assets/icon.png" alt="soft_collections" width="120">
</p>

<h1 align="center">soft_collections</h1>

<p>Curated AltStore sources for IPA projects on GitHub. All sources are generated in this repo with <a href="https://pypi.org/project/altgen/">AltGen</a>. It can be used with <a href="https://github.com/altstoreio/Altstore">AltStore</a>, <a href="https://github.com/SideStore/SideStore">SideStore</a>, <a href="https://github.com/LiveContainer/LiveContainer">LiveContainer</a>, <a href="https://github.com/claration/Feather">Feather</a> or other compatible apps.</p>

<p align="center">
<a href="https://altdirect.app/?url=https://raw.githubusercontent.com/braless/soft_collections/refs/heads/main/all-apps.json" target="_blank">
<img src="https://raw.githubusercontent.com/braless/soft_collections/main/assets/add-alt-source.png" alt="Add AltSource" width="200">
</a>
</p>
<p align="center">(Click the above image to add the soft_collections source)</p>

## Request an App

Don't see an app you want? [Create an issue](https://github.com/braless/soft_collections/issues/new) and I'll add it to the gallery. Please include the app's name and a link to its GitHub repo (or an IPA / release URL) so I can verify and add it.

## Screenshots

<table align="center" style="border: none; margin-left: auto; margin-right: auto;">
  <tr>
    <td align="center" style="border: none; padding: 6px;">
      <img src="https://raw.githubusercontent.com/braless/soft_collections/main/assets/sidestore.jpg" alt="soft_collections in SideStore" width="200" style="border-radius: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
      <br><b>SideStore</b>
    </td>
    <td align="center" style="border: none; padding: 6px;">
      <img src="https://raw.githubusercontent.com/braless/soft_collections/main/assets/sidestore_news.jpg" alt="soft_collections news in SideStore" width="200" style="border-radius: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
      <br><b>SideStore News</b>
    </td>
    <td align="center" style="border: none; padding: 6px;">
      <img src="https://raw.githubusercontent.com/braless/soft_collections/main/assets/livecontainer.jpg" alt="soft_collections in LiveContainer" width="200" style="border-radius: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
      <br><b>LiveContainer</b>
    </td>
  </tr>
</table>

## Available Apps

### <a href="https://github.com/Mak5er/AirCard-iOS"><img src="https://raw.githubusercontent.com/braless/soft_collections/main/apps/AirCard-iOS/icon.png" alt="AirCard-iOS icon" width="24" align="top"> AirCard-iOS</a>
Apple Wallet card skins, lock screen passcode themes and PosterBoard wallpapers on device, without a jailbreak (iOS 27+).

### <a href="https://github.com/Lakr233/Asspp"><img src="https://raw.githubusercontent.com/braless/soft_collections/main/apps/Asspp/icon.png" alt="Asspp icon" width="24" align="top"> Asspp</a>
Manage multiple Apple IDs across App Store regions and download official signed IPAs — no more logging out of your device.

### <a href="https://github.com/TouchFriend/DoubanMApp"><img src="https://raw.githubusercontent.com/braless/soft_collections/main/apps/DoubanMApp/icon.png" alt="DoubanMApp icon" width="24" align="top"> 豆瓣</a>
无广告版豆瓣客户端（DoubanMApp）：移除绝大多数广告、精简界面，其余功能与官方客户端一致。

### <a href="https://github.com/Mac-XK/KMusic"><img src="https://raw.githubusercontent.com/braless/soft_collections/main/apps/KMusic/icon.png" alt="KMusic icon" width="24" align="top"> KMusic</a>
基于 SwiftUI 的多源音乐聚合播放器，支持 iOS/macOS，内置酷我、酷狗、QQ 音乐、网易云等多平台音源与 LRC 歌词同步。

### <a href="https://github.com/missuo/kumone"><img src="https://raw.githubusercontent.com/braless/soft_collections/main/apps/Kumone/icon.png" alt="Kumone icon" width="24" align="top"> Kumone</a>
原生 NetEase Cloud Music iOS 客户端（雲の音），直连网易云音乐真实 API，支持灰色歌曲解锁与歌词。

### <a href="https://github.com/ResistanceTo/MiniWatts"><img src="https://raw.githubusercontent.com/braless/soft_collections/main/apps/MiniWatts/icon.png" alt="MiniWatts icon" width="24" align="top"> MiniWatts</a>
An iPhone battery, charging and thermal instrument built on Apple's private iOS APIs — real charger watts, what reaches the cell, 30 temperature sensors and the USB-PD handshake.

### <a href="https://github.com/verback2308/Opaline"><img src="https://raw.githubusercontent.com/braless/soft_collections/main/apps/Opaline/icon.png" alt="Opaline icon" width="24" align="top"> Opaline</a>
A lightweight, native YouTube client for iOS 12+ — no ads, no tracking, no dependencies.

### <a href="https://github.com/bggRGjQaUbCoE/PiliPlus"><img src="https://raw.githubusercontent.com/braless/soft_collections/main/apps/PiliPlus/icon.png" alt="PiliPlus icon" width="24" align="top"> PiliPlus</a>
使用Flutter开发的BiliBili第三方客户端。

### <a href="https://github.com/leminlimez/Pocket-Poster"><img src="https://raw.githubusercontent.com/braless/soft_collections/main/apps/Pocket-Poster/icon.png" alt="Pocket Poster icon" width="24" align="top"> Pocket Poster</a>
Custom PosterBoard animated wallpapers for iOS 17+ — browse and download community wallpapers, or import your own videos and images.

IPAs committed under [`apps/Local/`](apps/Local) are part of the `all-apps.json` source as well — see [Local IPAs](#local-ipas).

## Project Layout

```
soft_collections/
├── assets/               # shared assets: app icon, "Add AltSource" button, README screenshots
│   ├── icon.svg / icon.png
│   ├── add-alt-source.svg / add-alt-source.png
│   └── *.jpg             # README screenshots (SideStore, SideStore News, LiveContainer)
├── templates/            # shared news-image template + renderer
│   ├── news_update.template.svg
│   └── render_news.py
├── scripts/              # offline helpers that do not talk to GitHub
│   └── local_source.py   # builds apps/Local/apps.json from committed IPAs
├── apps/                 # one folder per app
│   ├── <AppName>/
│       ├── config.toml   # altgen configuration
│       ├── news.toml     # news image config (name, tagline, optional colors)
│       ├── icon.png      # resource files live here
│       ├── images/       # screenshots + news.png promo image
│       └── apps.json     # generated AltStore source
│   └── Local/            # IPAs committed by hand instead of released on GitHub
│       ├── *.ipa         # drop a file here and commit it
│       ├── config.toml   # optional defaults (developer name, tint colour)
│       ├── icons/        # generated app icons (override by adding your own)
│       └── apps.json     # generated by scripts/local_source.py
└── ...
```

## Local IPAs

`apps/Local/` is for IPAs that have no GitHub release to pull from. Drop a
`.ipa` in, commit it, and `.github/workflows/local.yml` builds
`apps/Local/apps.json` and merges it into `all-apps.json`. Nothing else is
needed:

- the app name, bundle identifier, version, build number and minimum iOS
  version are read from the IPA's own `Info.plist`;
- the icon comes out of the IPA too (Apple's `CgBI` PNGs are re-encoded to
  standard PNGs). Put `apps/Local/icons/<bundle-id>.png` there yourself to use
  your own icon instead;
- every version is listed: two IPAs of the same app become two version entries,
  newest first;
- the download URL is the committed file itself, so an IPA stays installable
  from its raw URL;
- no screenshots and no news images are generated for these apps.

Run the generator on its own with `python3 scripts/local_source.py`. The
altgen-based `update.sh` skips this folder on purpose — these IPAs are never
looked up on GitHub — but it still merges `apps/Local/apps.json` into
`all-apps.json` like every other source.

Two limits worth knowing before you upload: GitHub refuses files over 100 MB,
and every IPA stays in the repository's history forever, so the repository
grows with each build you commit. An IPA whose bundle identifier already
exists in another folder (say PiliPlus) is rejected, because `all-apps.json`
cannot contain two apps with the same identifier.

## Updating Apps and News Images

Run both scripts from the repo root:

```bash
./update.sh       # regenerate every app's apps.json from config.toml and merge into all-apps.json
./update_news.sh  # re-render every app's images/news.png from its news.toml
```

Both scripts can be run from anywhere — paths resolve against the repo
directory.

`apps/<AppName>/apps.json` and `all-apps.json` are gitignored and are not
committed by contributors. The `Update all-apps.json` GitHub Actions workflow
regenerates and commits them on every push to `main`, every 6 hours, or on
manual "Run workflow". Re-rendered `images/news.png` files stay in the working
tree for you to review and commit.

`update.sh` runs `uvx altgen -c config.toml` in every `apps/<AppName>/` that has
a `config.toml`, then merges the resulting sources into the repo-root
`all-apps.json` via `uvx altgen merge -c assets/merge.toml`.

`update_news.sh` renders each app's `images/news.png` from its `news.toml` using
`templates/render_news.py`. It needs the Python venv (set up once):

```bash
uv venv && uv pip install -r requirements.txt
```

The image is drawn entirely with Pillow — no external rasterizer needed.

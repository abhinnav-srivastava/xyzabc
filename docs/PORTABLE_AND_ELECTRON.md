# Portable Windows & Electron Distribution

CodeCritique is intended to be distributed as a **portable Windows app** (e.g. Electron-based) with **no installation required** — no system Python, Java, or PATH dependencies. Everything the app needs must live **inside the app directory**.

---

## Principles

1. **No runtime dependencies on the machine:** No `pip install`, no system PATH, no "install Git/Java first."
2. **Bundle all tools as native Windows executables** where possible (`.exe`). Avoid JARs unless you also bundle a JRE.
3. **If the shipped app is Electron + Node only** (no embedded Python), then patch analysis must use only **bundled binaries** (Git, CLOC, diffstat) or be reimplemented in Node; Python-based metrics (Pygount, Radon) will not run.
4. **If the shipped app embeds Python** (e.g. PyInstaller backend + Electron frontend), you can bundle the Python env and optional libs (pygount, radon) inside the app.

---

## What to bundle for portable Windows

Ship these **inside the app** (e.g. under `resources/tools/` or `tools/` relative to the app root):

| Component | Purpose | What to ship | No-install note |
|-----------|---------|--------------|------------------|
| **Git** | Patch stats (`git apply --numstat`) | **PortableGit** (e.g. [Git for Windows](https://git-scm.com/download/win) → extract the portable archive) into `tools/git/`. Final path like `tools/git/cmd/git.exe`. | No system Git required. |
| **CLOC** | Lines of code by language | **cloc.exe** from [cloc releases](https://github.com/AlDanial/cloc/releases) (e.g. `cloc-2.08.exe`) into `tools/cloc/`. | Single exe, no Perl. |
| **diffstat** | Insertions/deletions summary | **diffstat.exe** (e.g. from [GnuWin32 diffstat](https://gnuwin32.sourceforge.net/packages/diffstat.htm)) into `tools/diffstat/`. | Prefer `.exe`; do **not** rely on a `.jar` (would require bundling a JRE). |

The app already **prefers native executables** over JARs (e.g. `diffstat.exe` is used before any `*.jar` in `tools/diffstat/`). For portable builds, **ship only the .exe** so no Java is needed.

---

## What not to rely on in portable build

- **System PATH** — Assume nothing is on PATH. Resolve all tools from the app’s `tools/` directory.
- **pip / Python packages** — Pygount and Radon only run if Python is embedded and those packages are bundled. For Electron-without-Python, do not depend on them.
- **Java** — Do not depend on `java -jar` for core features (e.g. use diffstat.exe, not DiffStats.jar) unless you bundle a portable JRE.

---

## Electron packaging

- **Backend:** If the backend is **Node only**, implement or call out to **only the bundled binaries** (Git, CLOC, diffstat) for patch metrics; path_utils-style resolution should point at `resources/tools/` (or your chosen path) inside the packaged app.
- **Backend with embedded Python:** If you ship a Python runtime (e.g. bundled via PyInstaller or similar), place the **same tools/** layout next to it and bundle optional Python deps (pygount, radon) in that environment so they work without user install.
- **Tool paths:** At build time, set the app’s base path (e.g. `process.resourcesPath` in Electron) and resolve `tools/git`, `tools/cloc`, `tools/diffstat` from there so the packaged app finds the executables.

---

## Checklist for portable Windows build

- [ ] **Git:** PortableGit extracted under `tools/git/` (e.g. `cmd/git.exe`).
- [ ] **CLOC:** `cloc.exe` (or `cloc-2.08.exe`) in `tools/cloc/`.
- [ ] **diffstat:** `diffstat.exe` in `tools/diffstat/` (GnuWin32 or equivalent); no dependency on Java/JAR.
- [ ] **No PATH:** All tool invocations use full paths to these executables.
- [ ] **Python (if used):** Either embed a Python runtime and bundle pygount/radon, or do not use Python-only metrics in the portable build.
- [ ] **Config:** `config/metrics_tools.json` and path_utils already support “bundled first”; ensure your packager copies `tools/` and `config/` into the app image.

---

## Distribution artifacts (no install required)

Run `npm run build:win` to produce:

| Artifact | Use |
|----------|-----|
| **CodeCritique 1.0.0.exe** (portable) | Single file — copy to target machine, double-click to run. No installation, no admin. |
| **CodeCritique-portable.zip** | Unzip anywhere on target machine, run `CodeCritique.exe`. No installation, no admin. |
| **win-unpacked/** | Unpacked folder — copy the whole folder to target, run `CodeCritique.exe`. No installation, no admin. |

All artifacts are in `dist-electron/`. No NSIS installer is produced; the build is **portable-only**.

**Target machine requirements:** None. No Python, Node, or system installs. Copy the exe/zip/folder and run. Works without admin rights.

---

## Summary

For **portable Windows / Electron**, ship **Git**, **CLOC**, and **diffstat** as **Windows executables** inside the app. Do not require Python or Java on the user’s machine for core patch metrics. The codebase is structured to prefer these bundled binaries; keep that layout when building the Electron (or other portable) package.

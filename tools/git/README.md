# Bundled Git (optional)

Place a **portable Git** here so Restore app name can use it for exact patch stats (GitLab-accurate) without requiring Git to be installed on the system.

## Layout

Use one of these layouts so the app can find `git`:

- **Windows (Git for Windows / Portable Git):**
  - `tools/git/cmd/git.exe`, or
  - `tools/git/bin/git.exe`
- **Unix / macOS:**
  - `tools/git/bin/git`

So after extracting, the executable should be at:

- **Windows:** `tools/git/cmd/git.exe` or `tools/git/bin/git.exe`
- **Unix:** `tools/git/bin/git`

## Where to get portable Git

- **Windows:** [Git for Windows](https://git-scm.com/download/win) — use the “Portable” build or install and copy the `cmd` and `bin` folders from the install directory into `tools/git/`.
- **macOS / Linux:** Git is usually installed system-wide; you can leave this folder empty and use system `git`. To bundle: copy your system `git` (and any needed DLLs/libs) into `tools/git/bin/`.

## If this folder is empty

Restore app name will use `git` from the system **PATH**. Install Git normally and ensure `git` is on PATH if you want exact patch stats.

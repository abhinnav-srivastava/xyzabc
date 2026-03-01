# Bundled diffstat (optional)

Place the **diffstat** native binary here. CodeReview uses only **native executables** (e.g. `diffstat.exe` on Windows) so that no extra window or Java process starts when the app runs.

## Layout

- **Windows:** `tools/diffstat/diffstat.exe`
- **Unix / macOS:** `tools/diffstat/diffstat` (executable)

**Note:** JARs (e.g. `DiffStats.jar`) in this folder are **not** used — they often open a GUI window. Use a native diffstat binary instead.

## Where to get diffstat

- **Windows:** [GnuWin32 diffstat](https://gnuwin32.sourceforge.net/packages/diffstat.htm) — download and extract `diffstat.exe` into this folder.
- **Linux:** `apt install diffstat` or `yum install diffstat` (use PATH).
- **macOS:** `brew install diffstat` (use PATH).

## If this folder is empty

CodeReview will still show diff stats: it uses a **pure-Python** fallback that parses the patch when the diffstat binary is not available. The binary is only needed if you want the exact `diffstat` output format.

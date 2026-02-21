# Bundled CLOC (optional)

Place **cloc** (Count Lines of Code) here so CodeCritique can show lines-of-code breakdown by language for the changed files in a patch, without requiring cloc to be installed system-wide.

## Layout

- **Windows:** `tools/cloc/cloc.exe` or `tools/cloc/cloc.pl`
- **Unix / macOS:** `tools/cloc/cloc` or `tools/cloc/cloc.pl`

So the executable should be at:

- **Windows:** `tools/cloc/cloc.exe` (or `cloc.pl` if using the Perl script)
- **Unix:** `tools/cloc/cloc` or `tools/cloc/cloc.pl`

## Where to get CLOC

- **Releases (Windows exe, Linux, macOS):** [cloc releases on GitHub](https://github.com/AlDanial/cloc/releases) — download the appropriate binary and put it in `tools/cloc/` as `cloc` or `cloc.exe`.
- **Perl script:** [cloc on GitHub](https://github.com/AlDanial/cloc) — copy `cloc` or `cloc.pl` into `tools/cloc/`. On Windows you need Perl installed to run it.

## If this folder is empty

CodeCritique will use `cloc` from the system **PATH**. Install cloc (e.g. `apt install cloc`, `brew install cloc`) if you want the “Lines of code (CLOC)” section in the patch summary.

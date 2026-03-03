# Dependency Audit Report

**Date:** March 2025  
**Project:** Restore app name  
**Last fixed:** March 2025

---

## Node.js / npm Dependencies

### Audit Summary (FIXED)

| Status | Count |
|--------|-------|
| Vulnerabilities | **0** (was 6) |

### Fixes Applied

- **electron:** ^28.0.0 → ^35.7.5
- **electron-builder:** ^24.9.1 → ^26.8.1
- **Python:** requirements.txt updated with minimum safe versions; Flask 3.1.3, reportlab 4.4.10 installed

### Previous Vulnerabilities (resolved)

#### 1. Electron (moderate) — FIXED
- **Package:** electron
- **Current:** ^28.0.0
- **Advisory:** [GHSA-vmqv-hx8q-j7mg](https://github.com/advisories/GHSA-vmqv-hx8q-j7mg)
- **Issue:** ASAR Integrity Bypass via resource modification
- **Fix:** Upgrade to electron ≥35.7.5 (e.g. `npm install electron@^35`)
- **Note:** Major version upgrade; test for breaking changes (Chromium, Node.js bumps)

#### 2. tar (high) – transitive via electron-builder — FIXED
- **Package:** tar (≤7.5.7)
- **Advisories:**
  - GHSA-r6q2-hw4h-h46w: Race condition via Unicode ligature collisions
  - GHSA-34x7-hfp2-rc4v: Arbitrary file creation/overwrite via hardlink traversal
  - GHSA-8qq5-rm4j-mr97: Arbitrary file overwrite and symlink poisoning
  - GHSA-83g3-92jg-28cx: Arbitrary file read/write via hardlink target escape
- **Fix:** Upgrade electron-builder to ≥26.8.1 (brings updated tar)
- **Note:** `npm audit fix --force` would upgrade electron-builder; may introduce breaking changes

### Recommended Actions (npm)

1. **Conservative:** Keep current versions; document as known issues; monitor for patches.
2. **Moderate:** Upgrade Electron to 35.x and electron-builder to 26.x; run full regression tests.
3. **Aggressive:** Run `npm audit fix --force`; expect breaking changes; extensive testing required.

---

## Python Dependencies

### Packages (requirements.txt)

| Package    | Version  | Notes                    |
|------------|----------|--------------------------|
| Flask      | 3.0.3    | Web framework            |
| reportlab  | 4.2.2    | PDF generation           |
| pandas     | 2.1.4    | Data processing          |
| numpy      | ≥1.24.0  | Numerical computing      |
| openpyxl   | 3.1.2    | Excel read/write         |
| PyInstaller| 6.3.0    | Packaging                |
| setuptools | ≥65.0.0  | Build                    |
| wheel      | ≥0.40.0  | Build                    |
| waitress   | ≥2.1.2   | WSGI server              |

### Known Issues

- **pandas 2.1.4:** CVE-2024-9880 (command injection in `DataFrame.query` with python engine) was reported but later **withdrawn** by CNA. If you use `df.query()` with user input, prefer the `numexpr` engine or validate input.
- **Flask 3.0.3, reportlab 4.2.2:** No critical CVEs found in recent advisories.

### Recommended Actions (Python)

1. Run `pip-audit` when available: `pip install pip-audit && pip-audit`
2. Consider upgrading: `pip install --upgrade Flask reportlab pandas openpyxl`
3. Pin versions in production and re-audit periodically.

---

## Summary

| Area   | Status   | Action                                      |
|--------|----------|---------------------------------------------|
| npm    | 6 issues | Upgrade Electron + electron-builder; test   |
| Python | Unknown  | Install pip-audit; run audit; upgrade if needed |

---

## Commands Reference

```bash
# npm audit
npm audit
npm audit fix          # Non-breaking fixes only
npm audit fix --force  # All fixes (breaking changes possible)

# Python audit (install pip-audit first)
pip install pip-audit
pip-audit
```

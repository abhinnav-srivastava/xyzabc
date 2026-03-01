# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for CodeReview backend.
Bundles Flask + Python + deps into a single CodeReview.exe for Electron.
Output: dist/CodeReview.exe
"""

import os

block_cipher = None

# Data files to bundle (relative to project root)
project_root = os.path.dirname(os.path.abspath(SPEC))

def collect_datas():
    """Bundle config, checklists, templates, static, utils, tools. Services are traced as Python."""
    datas = []
    for folder in ['config', 'checklists', 'templates', 'static', 'utils', 'tools']:
        src = os.path.join(project_root, folder)
        if os.path.exists(src):
            datas.append((src, folder))
    return datas

a = Analysis(
    ['app.py'],
    pathex=[project_root],
    binaries=[],
    datas=collect_datas(),
    hiddenimports=[
        'flask',
        'waitress',
        'jinja2',
        'werkzeug',
        'werkzeug.routing',
        'werkzeug.serving',
        'pandas',
        'numpy',
        'openpyxl',
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.lib.units',
        'reportlab.lib.colors',
        'reportlab.lib.styles',
        'reportlab.lib.enums',
        'reportlab.pdfgen',
        'reportlab.pdfgen.canvas',
        'reportlab.platypus',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CodeReview',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

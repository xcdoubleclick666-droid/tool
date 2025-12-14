# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
from PyInstaller.utils.hooks.qt import pyside6_plugins_binaries

# collect PySide6 data files and dynamic libs
datas = collect_data_files('PySide6')
binaries = collect_dynamic_libs('PySide6')

# include Qt platform plugins (e.g. qwindows.dll)
try:
    plugin_binaries = pyside6_plugins_binaries(('platforms',))
    binaries += plugin_binaries
except Exception:
    # best-effort: continue if hook not available
    pass

# include runtime JSONs and PySide6 datas
datas += [
    ('models.json', '.'),
    ('fields.json', '.'),
    ('ui_prefs.json', '.'),
]

a = Analysis([
    'qt_main.py',
],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='FitnessToolbox',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, name='FitnessToolbox')

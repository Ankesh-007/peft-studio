# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PEFT Studio Backend.

This spec file configures how the Python backend is bundled into a standalone executable.
It includes all dependencies, data files, and handles lazy-loaded modules.
"""

import sys
import os
from pathlib import Path

# Import our build hooks to get hidden imports
sys.path.insert(0, os.path.dirname(os.path.abspath(SPECPATH)))
from build_hooks import get_all_hidden_imports

# Get all hidden imports
hidden_imports = get_all_hidden_imports()

# Define data files to include
datas = [
    ('config.py', '.'),
    ('database.py', '.'),
    ('runtime_paths.py', '.'),
]

# Add services directory (for any non-Python resources)
services_dir = Path(SPECPATH) / 'services'
if services_dir.exists():
    # Include any JSON, YAML, or other config files in services
    for pattern in ['*.json', '*.yaml', '*.yml', '*.txt']:
        for file in services_dir.glob(pattern):
            datas.append((str(file), 'services'))

# Add connectors directory
connectors_dir = Path(SPECPATH) / 'connectors'
if connectors_dir.exists():
    for pattern in ['*.json', '*.yaml', '*.yml', '*.txt']:
        for file in connectors_dir.glob(pattern):
            datas.append((str(file), 'connectors'))

# Add plugins directory
plugins_dir = Path(SPECPATH) / 'plugins'
if plugins_dir.exists():
    for pattern in ['*.json', '*.yaml', '*.yml', '*.txt']:
        for file in plugins_dir.rglob(pattern):
            rel_path = file.relative_to(plugins_dir)
            datas.append((str(file), str(Path('plugins') / rel_path.parent)))

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[SPECPATH],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test modules
        'pytest',
        'hypothesis',
        'test',
        'tests',
        '_pytest',
        # Exclude development tools
        'IPython',
        'jupyter',
        'notebook',
        # Exclude unnecessary torch backends if needed
        # 'torch.distributions',  # Uncomment if not using distributions
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='peft_engine',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep True to see backend logs; Windows will hide console via Electron
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Can add icon path here if desired
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='peft_engine',
)

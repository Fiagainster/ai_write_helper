# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 要排除的文件和目录
# 排除所有__pycache__目录
# 排除可能包含API密钥的配置文件
# 排除测试目录和临时文件

a = Analysis(['main.py'],
             pathex=['d:/项目/AI划词补写小工具'],
             binaries=[],
             datas=[],
             hiddenimports=['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'pynput.keyboard', 'pynput.mouse', 'cryptography.hazmat.backends', 'cryptography.hazmat.primitives'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=['__pycache__', '*.pyc', '*.pyo', 'tests', '*.log', '*.db', 'config.json', 'settings.ini'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='AI划词补写小工具',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=True,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon=None)
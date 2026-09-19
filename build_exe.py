"""
اسکریپت ساخت فایل اجرایی مستقل ویندوز ۱۱ با PyInstaller.
اجرا: python build_exe.py
خروجی: dist/VoiceToText.exe
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def main():
    project_root = Path(__file__).parent.resolve()
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    assets_dir = project_root / "assets"
    spec_file = project_root / "VoiceToText.spec"

    print("=" * 60)
    print("  Voice-to-Text Windows 11 - EXE Builder v2.0")
    print("=" * 60)

    # اطمینان از نصب PyInstaller
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__} found.")
    except ImportError:
        print("[!] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0"])

    # ساخت فایل .spec
    fonts_path = assets_dir / "fonts"
    datas = []

    if fonts_path.exists():
        # اضافه کردن تمام فایل‌های فونت
        font_files = list(fonts_path.glob("Vazirmatn-Regular.ttf")) + \
                     list(fonts_path.glob("Vazirmatn-Medium.ttf")) + \
                     list(fonts_path.glob("Vazirmatn-Bold.ttf")) + \
                     list(fonts_path.glob("Vazirmatn-SemiBold.ttf")) + \
                     list(fonts_path.glob("Vazirmatn-Light.ttf"))

        for f in font_files:
            datas.append(f"(r'{f}', 'assets/fonts')")
        print(f"[OK] {len(font_files)} Vazirmatn font files added.")
    else:
        print("[WARNING] fonts directory not found — UI will fall back to Segoe UI.")

    datas_str = ",\n    ".join(datas)

    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
# VoiceToText Windows 11 — PyInstaller Spec File (Auto-generated)

block_cipher = None

a = Analysis(
    [r'{project_root / "main.py"}'],
    pathex=[r'{project_root}'],
    binaries=[],
    datas=[
    {datas_str}
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'speech_recognition',
        'pyaudio',
        'keyboard',
        'win32clipboard',
        'win32con',
        'win32api',
        'numpy',
        'numpy.core._methods',
        'numpy.lib.format',
        'winsound',
        'wave',
        'winreg',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['matplotlib', 'pandas', 'scipy', 'PIL', 'tk', 'tkinter', 'vosk'],
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
    name='VoiceToText',
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
    version_file=None,
    uac_admin=False,
)
"""

    spec_file.write_text(spec_content, encoding="utf-8")
    print(f"[OK] Spec file written: {spec_file}")

    # پاکسازی build قبلی
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
    if dist_dir.exists():
        shutil.rmtree(dist_dir, ignore_errors=True)

    # اجرای PyInstaller
    print("\n[..] Building EXE — this may take 1-3 minutes...")
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(spec_file)]
    result = subprocess.run(cmd, cwd=str(project_root))

    if result.returncode == 0:
        exe_path = dist_dir / "VoiceToText.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("")
            print("=" * 60)
            print("  [OK] Build Successful!")
            print(f"  Output: {exe_path}")
            print(f"  Size: {size_mb:.1f} MB")
            print("=" * 60)
        else:
            print("\n[ERROR] EXE not found in dist/ after build.")
    else:
        print(f"\n[ERROR] PyInstaller failed with code {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    main()

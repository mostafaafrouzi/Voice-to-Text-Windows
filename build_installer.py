"""
اسکریپت ساخت فایل نصاب ویندوز با Inno Setup (محلی).
اجرا: python build_installer.py
خروجی: dist/VoiceToText-Setup-v2.0.0.exe
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
from app.version import __version__


def find_iscc() -> str | None:
    # بررسی متغیر PATH
    iscc_path = shutil.which("ISCC") or shutil.which("iscc")
    if iscc_path:
        return iscc_path

    # بررسی مسیرهای متداول Inno Setup در ویندوز
    common_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"),
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p
    return None


def main():
    project_root = Path(__file__).parent.resolve()
    dist_dir = project_root / "dist"
    iss_file = project_root / "installer" / "setup.iss"
    exe_path = dist_dir / "VoiceToText.exe"

    print("=" * 60)
    print(f"  Voice-to-Text Windows - Installer Builder v{__version__}")
    print("=" * 60)

    # ۱. بررسی یا ساخت فایل EXE
    if not exe_path.exists():
        print("[!] dist/VoiceToText.exe not found. Building EXE first...")
        ret = subprocess.run([sys.executable, "build_exe.py"], cwd=str(project_root))
        if ret.returncode != 0 or not exe_path.exists():
            print("[ERROR] Failed to build VoiceToText.exe")
            sys.exit(1)
    else:
        print(f"[OK] Found executable: {exe_path} ({exe_path.stat().st_size / (1024*1024):.1f} MB)")

    # ۲. پیدا کردن کامپایلر Inno Setup
    iscc = find_iscc()
    if not iscc:
        print("\n[WARNING] Inno Setup compiler (ISCC.exe) was not found on this machine.")
        print("  - To build installer locally, please install Inno Setup 6: https://jrsoftware.org/isdl.php")
        print("  - Note: GitHub Actions automatically builds both EXE and Setup Installer in the cloud on tag release.")
        return

    print(f"[OK] Inno Setup compiler found: {iscc}")

    # ۳. کامپایل اسکریپت setup.iss
    print("\n[..] Compiling Windows Installer with Inno Setup...")
    cmd = [iscc, f"/DAppVersion={__version__}", str(iss_file)]
    ret = subprocess.run(cmd, cwd=str(project_root))

    if ret.returncode == 0:
        setup_file = dist_dir / f"VoiceToText-Setup-v{__version__}.exe"
        print("")
        print("=" * 60)
        print("  [OK] Installer Build Successful!")
        if setup_file.exists():
            size_mb = setup_file.stat().st_size / (1024 * 1024)
            print(f"  Installer: {setup_file}")
            print(f"  Size: {size_mb:.1f} MB")
        print("=" * 60)
    else:
        print(f"[ERROR] Inno Setup compilation failed with code {ret.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    main()

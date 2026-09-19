"""
ماژول بررسی بروزرسانی خودکار — استاندارد برنامه‌های جهانی.
در پس‌زمینه هنگام اجرا بررسی می‌کند، و امکان بررسی دستی از تنظیمات نیز دارد.
"""
import os
import sys
import json
import threading
import tempfile
import urllib.request
import subprocess
from packaging.version import Version
from app.version import __version__, __releases_api__, __github_url__, __app_name__


class UpdateResult:
    def __init__(self, has_update: bool, latest_version: str = "", download_url: str = "",
                 release_notes: str = "", error: str = ""):
        self.has_update = has_update
        self.latest_version = latest_version
        self.download_url = download_url
        self.release_notes = release_notes
        self.error = error


def check_for_updates(timeout: int = 8) -> UpdateResult:
    """
    بررسی آخرین نسخه از GitHub Releases API.
    """
    try:
        req = urllib.request.Request(
            __releases_api__,
            headers={
                "User-Agent": f"{__app_name__}/v{__version__}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        tag = data.get("tag_name", "").lstrip("v")
        if not tag:
            return UpdateResult(False, error="نسخه نامعتبر در پاسخ API")

        latest = Version(tag)
        current = Version(__version__)

        # پیدا کردن لینک دانلود فایل EXE از assets
        download_url = ""
        assets = data.get("assets", [])
        for asset in assets:
            name = asset.get("name", "").lower()
            if name.endswith(".exe") and "setup" in name:
                download_url = asset["browser_download_url"]
                break
        # اگر installer نبود، EXE اصلی را انتخاب کن
        if not download_url:
            for asset in assets:
                name = asset.get("name", "").lower()
                if name.endswith(".exe"):
                    download_url = asset["browser_download_url"]
                    break

        release_notes = data.get("body", "").strip()

        if latest > current:
            return UpdateResult(
                has_update=True,
                latest_version=f"v{tag}",
                download_url=download_url,
                release_notes=release_notes
            )
        else:
            return UpdateResult(has_update=False, latest_version=f"v{tag}")

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return UpdateResult(False, error="هنوز هیچ نسخه‌ای منتشر نشده است.")
        return UpdateResult(False, error=f"خطای HTTP: {e.code}")

    except urllib.error.URLError:
        return UpdateResult(False, error="عدم اتصال به اینترنت. بروزرسانی امکان‌پذیر نیست.")

    except Exception as e:
        return UpdateResult(False, error=f"خطای غیرمنتظره: {e}")


def download_and_install_update(download_url: str, on_progress=None, on_done=None, on_error=None):
    """
    دانلود و نصب نسخه جدید در یک ترد مجزا.
    فایل installer را دانلود کرده و سپس اجرا می‌کند.
    """
    def _worker():
        try:
            # دانلود به یک فایل موقت
            filename = os.path.basename(download_url.split("?")[0]) or "VoiceToTextSetup.exe"
            tmp_dir = tempfile.mkdtemp(prefix="vtt_update_")
            dest_path = os.path.join(tmp_dir, filename)

            req = urllib.request.Request(
                download_url,
                headers={"User-Agent": f"{__app_name__}/v{__version__}"}
            )

            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 65536  # 64KB
                with open(dest_path, "wb") as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if on_progress and total > 0:
                            pct = int(downloaded * 100 / total)
                            try:
                                on_progress(pct)
                            except Exception:
                                pass

            # اجرای فایل نصب/EXE
            if dest_path.lower().endswith("setup.exe") or "setup" in dest_path.lower():
                # Installer — اجرا و برنامه جاری را ببند
                subprocess.Popen([dest_path], shell=False)
            else:
                # EXE مستقیم — باز کن
                subprocess.Popen([dest_path], shell=False)

            if on_done:
                try:
                    on_done(dest_path)
                except Exception:
                    pass

        except Exception as e:
            if on_error:
                try:
                    on_error(str(e))
                except Exception:
                    pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


def check_updates_background(on_update_available=None, delay_seconds: float = 5.0):
    """
    بررسی بروزرسانی در پس‌زمینه چند ثانیه پس از راه‌اندازی برنامه.
    """
    def _delayed():
        import time
        time.sleep(delay_seconds)
        result = check_for_updates()
        if result.has_update and on_update_available:
            try:
                on_update_available(result)
            except Exception as e:
                print(f"[Updater] callback error: {e}")

    t = threading.Thread(target=_delayed, daemon=True)
    t.start()
    return t

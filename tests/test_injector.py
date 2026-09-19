import unittest
import time
from app.core.injector import _get_clipboard_text, _set_clipboard_text


class TestInjector(unittest.TestCase):
    def test_clipboard_backup_and_restore(self):
        original = "متن تستی قبلی کاربر"
        _set_clipboard_text(original)
        self.assertEqual(_get_clipboard_text(), original)

        # متن جدید
        new_text = "متن جدید تایپ صوتی"
        _set_clipboard_text(new_text)
        self.assertEqual(_get_clipboard_text(), new_text)

        # بازگردانی
        _set_clipboard_text(original)
        self.assertEqual(_get_clipboard_text(), original)


if __name__ == "__main__":
    unittest.main()

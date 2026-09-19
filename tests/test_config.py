import unittest
from app.config import ConfigManager, DEFAULT_CONFIG


class TestConfig(unittest.TestCase):
    def test_default_values(self):
        cfg = ConfigManager()
        self.assertEqual(cfg.get("language"), "fa-IR")
        self.assertEqual(cfg.get("hotkey"), "ctrl+alt+v")
        self.assertTrue(cfg.get("enable_persian_punctuation"))
        self.assertTrue(cfg.get("enable_half_space"))

    def test_set_and_get(self):
        cfg = ConfigManager()
        cfg.set("language", "en-US")
        self.assertEqual(cfg.get("language"), "en-US")
        # بازگردانی به حالت اولیه
        cfg.set("language", "fa-IR")


if __name__ == "__main__":
    unittest.main()

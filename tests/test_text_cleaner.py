import unittest
from app.core.text_cleaner import clean_text, ZWNJ


class TestTextCleaner(unittest.TestCase):
    def test_persian_punctuation(self):
        # نقطه
        res = clean_text("سلام نقطه حال شما چطوره علامت سوال", language="fa-IR")
        self.assertEqual(res, "سلام. حال شما چطوره؟")

        # ویرگول
        res = clean_text("سیب ویرگول پرتقال و موز", language="fa-IR")
        self.assertEqual(res, "سیب، پرتقال و موز")

        # علامت تعجب
        res = clean_text("چه روز قشنگی علامت تعجب", language="fa-IR")
        self.assertEqual(res, "چه روز قشنگی!")

        # برو خط بعد
        res = clean_text("خط اول برو خط بعد خط دوم", language="fa-IR")
        self.assertEqual(res, "خط اول\nخط دوم")

        # پرانتز
        res = clean_text("ایران پرانتز باز پایتخت تهران پرانتز بسته کشوری زیباست", language="fa-IR")
        self.assertEqual(res, "ایران (پایتخت تهران) کشوری زیباست")

    def test_persian_half_space(self):
        res = clean_text("من به خانه می روم و کتاب ها را می خوانم", language="fa-IR")
        expected = f"من به خانه می{ZWNJ}روم و کتاب{ZWNJ}ها را می{ZWNJ}خوانم"
        self.assertEqual(res, expected)

        res = clean_text("این کار راحت تر و سریع ترین راه است", language="fa-IR")
        expected = f"این کار راحت{ZWNJ}تر و سریع{ZWNJ}ترین راه است"
        self.assertEqual(res, expected)

    def test_english_punctuation_and_caps(self):
        res = clean_text("hello world period how are you question mark", language="en-US")
        self.assertEqual(res, "Hello world. How are you?")

        res = clean_text("item one comma item two and item three", language="en-US")
        self.assertEqual(res, "Item one, item two and item three")

        res = clean_text("first line new line second line", language="en-US")
        self.assertEqual(res, "First line\nSecond line")

    def test_complex_real_scenario(self):
        spoken = "سلام چطوری ویرگول فردا می بینمت نقطه برو خط بعد ساعت چهار منتظرم علامت تعجب"
        expected = f"سلام چطوری، فردا می{ZWNJ}بینمت.\nساعت چهار منتظرم!"
        self.assertEqual(clean_text(spoken, language="fa-IR"), expected)

    def test_persian_digits(self):
        res = clean_text("سال 1402 بود", language="fa-IR", persian_digits=True)
        self.assertEqual(res, "سال ۱۴۰۲ بود")


if __name__ == "__main__":
    unittest.main()

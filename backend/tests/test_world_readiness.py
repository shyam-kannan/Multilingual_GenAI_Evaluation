import pytest

from app.services.world_readiness import validate


# ── en-US ──────────────────────────────────────────────────────────────────

class TestEnUS:
    def test_good_english(self):
        text = "The total cost is $1,250.00 and the deadline is 12/31/2025."
        result = validate(text, "en-US")
        assert result["passed"] is True
        assert all(c["passed"] for c in result["checks"])

    def test_good_english_simple(self):
        text = "Hello, this is a response in American English."
        result = validate(text, "en-US")
        assert result["passed"] is True

    def test_fails_arabic_script_leak(self):
        text = "The answer is مرحبا and that's final."
        result = validate(text, "en-US")
        assert result["passed"] is False
        foreign_check = next(c for c in result["checks"] if c["check"] == "no_foreign_script")
        assert foreign_check["passed"] is False

    def test_fails_cjk_leak(self):
        text = "The weather is 天気 today in New York."
        result = validate(text, "en-US")
        assert result["passed"] is False
        foreign_check = next(c for c in result["checks"] if c["check"] == "no_foreign_script")
        assert foreign_check["passed"] is False

    def test_pure_numbers_passes(self):
        text = "Result: 42"
        result = validate(text, "en-US")
        assert result["passed"] is True


# ── es-MX ──────────────────────────────────────────────────────────────────

class TestEsMX:
    def test_good_spanish(self):
        text = "El costo total es de $1,250.00 y la fecha límite es el 31/12/2025. ¿Tiene alguna pregunta?"
        result = validate(text, "es-MX")
        assert result["passed"] is True
        assert all(c["passed"] for c in result["checks"])

    def test_good_spanish_diacritics(self):
        text = "La información está disponible en español para México."
        result = validate(text, "es-MX")
        assert result["passed"] is True

    def test_fails_no_diacritics_english(self):
        text = "This is a plain English response with no Spanish at all."
        result = validate(text, "es-MX")
        assert result["passed"] is False
        diac_check = next(c for c in result["checks"] if c["check"] == "spanish_diacritics")
        assert diac_check["passed"] is False

    def test_fails_arabic_leak(self):
        text = "El resultado es مرحبا según nuestros análisis."
        result = validate(text, "es-MX")
        assert result["passed"] is False
        foreign_check = next(c for c in result["checks"] if c["check"] == "no_foreign_script")
        assert foreign_check["passed"] is False

    def test_all_spanish_special_chars(self):
        text = "Año nuevo: ñ, ü, á, é, í, ó, ú, ¿por qué?, ¡sí!"
        result = validate(text, "es-MX")
        assert result["passed"] is True


# ── ar-SA ──────────────────────────────────────────────────────────────────

class TestArSA:
    def test_good_arabic(self):
        text = "مرحباً بكم في خدمة التقييم. التكلفة الإجمالية هي ١٢٥٠ ريال."
        result = validate(text, "ar-SA")
        assert result["passed"] is True
        assert all(c["passed"] for c in result["checks"])

    def test_good_arabic_simple(self):
        text = "هذا هو الرد باللغة العربية."
        result = validate(text, "ar-SA")
        assert result["passed"] is True

    def test_fails_no_arabic_script(self):
        text = "This is plain English with no Arabic whatsoever."
        result = validate(text, "ar-SA")
        assert result["passed"] is False
        arabic_check = next(c for c in result["checks"] if c["check"] == "arabic_script")
        assert arabic_check["passed"] is False

    def test_fails_too_much_latin(self):
        text = "This is mostly English but has a tiny bit of عربي somewhere."
        result = validate(text, "ar-SA")
        assert result["passed"] is False
        untrans = next(c for c in result["checks"] if c["check"] == "untranslated_strings")
        assert untrans["passed"] is False

    def test_arabic_with_numbers(self):
        text = "العدد الإجمالي هو ٥٠٠ وحدة والتاريخ ١٤٤٥/٠٦/١٥."
        result = validate(text, "ar-SA")
        assert result["passed"] is True

    def test_mixed_arabic_with_acceptable_latin(self):
        text = "يمكنك استخدام API للوصول إلى البيانات."
        result = validate(text, "ar-SA")
        assert result["passed"] is True


# ── ja-JP ──────────────────────────────────────────────────────────────────

class TestJaJP:
    def test_good_japanese(self):
        text = "合計金額は1,250円です。期限は2025年12月31日です。"
        result = validate(text, "ja-JP")
        assert result["passed"] is True
        assert all(c["passed"] for c in result["checks"])

    def test_good_japanese_hiragana_katakana(self):
        text = "これはテストの回答です。よろしくお願いします。"
        result = validate(text, "ja-JP")
        assert result["passed"] is True

    def test_fails_no_cjk(self):
        text = "This is plain English with no Japanese characters at all."
        result = validate(text, "ja-JP")
        assert result["passed"] is False
        cjk_check = next(c for c in result["checks"] if c["check"] == "cjk_script")
        assert cjk_check["passed"] is False

    def test_fails_too_much_latin(self):
        text = "This is almost all English except for one tiny 日 character buried in a long sentence."
        result = validate(text, "ja-JP")
        assert result["passed"] is False
        untrans = next(c for c in result["checks"] if c["check"] == "untranslated_strings")
        assert untrans["passed"] is False

    def test_japanese_with_dates(self):
        text = "本日は2025年6月25日です。天気は晴れです。"
        result = validate(text, "ja-JP")
        assert result["passed"] is True

    def test_katakana_heavy(self):
        text = "サーバーのレスポンスタイムはミリセカンドで計測されます。"
        result = validate(text, "ja-JP")
        assert result["passed"] is True


# ── Edge cases ─────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_unsupported_locale_passes(self):
        result = validate("Some text", "fr-FR")
        assert result["passed"] is True

    def test_empty_text_en_us(self):
        result = validate("", "en-US")
        assert result["passed"] is False

    def test_numbers_only(self):
        result = validate("12345", "en-US")
        assert result["passed"] is False

    def test_validate_returns_checks_list(self):
        result = validate("Hello world", "en-US")
        assert "checks" in result
        assert isinstance(result["checks"], list)
        assert all("check" in c and "passed" in c for c in result["checks"])

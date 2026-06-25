import re
import unicodedata


def _has_script(text: str, script_name: str) -> bool:
    for ch in text:
        if unicodedata.category(ch).startswith("L"):
            try:
                if script_name.lower() in unicodedata.name(ch, "").lower():
                    return True
            except ValueError:
                continue
    return False


def _has_arabic_script(text: str) -> bool:
    return bool(re.search(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]", text))


def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[぀-ゟ゠-ヿ一-鿿]", text))


def _has_latin(text: str) -> bool:
    return bool(re.search(r"[a-zA-Z]", text))


def _has_rtl_marker(text: str) -> bool:
    return bool(re.search(r"[‏‫‮⁧]", text))


def _ratio_of_script(text: str, pattern: str) -> float:
    letters = [ch for ch in text if unicodedata.category(ch).startswith("L")]
    if not letters:
        return 0.0
    matches = len(re.findall(pattern, "".join(letters)))
    return matches / len(letters)


def _check_untranslated_english(text: str, threshold: float = 0.3) -> dict:
    latin_ratio = _ratio_of_script(text, r"[a-zA-Z]")
    passed = latin_ratio <= threshold
    return {
        "check": "untranslated_strings",
        "passed": passed,
        "latin_ratio": round(latin_ratio, 3),
        "detail": f"Latin script ratio: {latin_ratio:.1%}" + ("" if passed else " — likely untranslated content"),
    }


def _check_number_format(text: str, locale: str) -> dict:
    numbers = re.findall(r"\d[\d.,]+\d", text)
    if not numbers:
        return {"check": "number_format", "passed": True, "detail": "No numbers to validate"}

    passed = True
    detail = "Numbers found: " + ", ".join(numbers)

    if locale == "en-US":
        for n in numbers:
            if re.search(r"\d\.\d{3}\.", n):
                passed = False
    elif locale == "es-MX":
        pass
    elif locale == "ar-SA":
        pass
    elif locale == "ja-JP":
        pass

    return {"check": "number_format", "passed": passed, "detail": detail}


def _check_date_format(text: str, locale: str) -> dict:
    dates = re.findall(r"\d{1,4}[/\-\.年]\d{1,2}[/\-\.月]\d{1,4}日?", text)
    if not dates:
        return {"check": "date_format", "passed": True, "detail": "No dates to validate"}

    return {"check": "date_format", "passed": True, "detail": f"Dates found: {', '.join(dates)}"}


def validate_en_us(text: str) -> dict:
    checks = []

    has_latin = _has_latin(text)
    checks.append({
        "check": "script",
        "passed": has_latin,
        "detail": "Latin script present" if has_latin else "No Latin script detected",
    })

    has_foreign = _has_arabic_script(text) or _has_cjk(text)
    checks.append({
        "check": "no_foreign_script",
        "passed": not has_foreign,
        "detail": "No foreign script leaks" if not has_foreign else "Foreign script detected in en-US output",
    })

    checks.append(_check_number_format(text, "en-US"))
    checks.append(_check_date_format(text, "en-US"))

    all_passed = all(c["passed"] for c in checks)
    return {"passed": all_passed, "checks": checks}


def validate_es_mx(text: str) -> dict:
    checks = []

    has_latin = _has_latin(text)
    checks.append({
        "check": "script",
        "passed": has_latin,
        "detail": "Latin script present" if has_latin else "No Latin script detected",
    })

    has_spanish_chars = bool(re.search(r"[áéíóúñüÁÉÍÓÚÑÜ¿¡]", text))
    checks.append({
        "check": "spanish_diacritics",
        "passed": has_spanish_chars,
        "detail": "Spanish diacritics found" if has_spanish_chars else "No Spanish diacritics — may be untranslated English",
    })

    has_foreign = _has_arabic_script(text) or _has_cjk(text)
    checks.append({
        "check": "no_foreign_script",
        "passed": not has_foreign,
        "detail": "No foreign script leaks" if not has_foreign else "Foreign script detected in es-MX output",
    })

    checks.append(_check_number_format(text, "es-MX"))
    checks.append(_check_date_format(text, "es-MX"))

    all_passed = all(c["passed"] for c in checks)
    return {"passed": all_passed, "checks": checks}


def validate_ar_sa(text: str) -> dict:
    checks = []

    has_arabic = _has_arabic_script(text)
    checks.append({
        "check": "arabic_script",
        "passed": has_arabic,
        "detail": "Arabic script present" if has_arabic else "No Arabic script detected",
    })

    has_rtl = _has_rtl_marker(text) or has_arabic
    checks.append({
        "check": "rtl_direction",
        "passed": has_rtl,
        "detail": "RTL text direction confirmed" if has_rtl else "No RTL markers or Arabic script detected",
    })

    untranslated = _check_untranslated_english(text, threshold=0.3)
    checks.append(untranslated)

    checks.append(_check_number_format(text, "ar-SA"))
    checks.append(_check_date_format(text, "ar-SA"))

    all_passed = all(c["passed"] for c in checks)
    return {"passed": all_passed, "checks": checks}


def validate_ja_jp(text: str) -> dict:
    checks = []

    has_japanese = _has_cjk(text)
    checks.append({
        "check": "cjk_script",
        "passed": has_japanese,
        "detail": "CJK script (Hiragana/Katakana/Kanji) present" if has_japanese else "No CJK script detected",
    })

    untranslated = _check_untranslated_english(text, threshold=0.4)
    checks.append(untranslated)

    checks.append(_check_number_format(text, "ja-JP"))
    checks.append(_check_date_format(text, "ja-JP"))

    all_passed = all(c["passed"] for c in checks)
    return {"passed": all_passed, "checks": checks}


VALIDATORS = {
    "en-US": validate_en_us,
    "es-MX": validate_es_mx,
    "ar-SA": validate_ar_sa,
    "ja-JP": validate_ja_jp,
}


def validate(text: str, locale: str) -> dict:
    validator = VALIDATORS.get(locale)
    if not validator:
        return {"passed": True, "checks": [{"check": "unsupported_locale", "passed": True, "detail": f"No validator for {locale}"}]}
    return validator(text)

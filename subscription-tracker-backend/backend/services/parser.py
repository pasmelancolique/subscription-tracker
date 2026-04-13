import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional


def extract_amount(text: str) -> Optional[Decimal]:
    """
    Extract transaction amount from Russian bank notification text.
    Handles formats: 1 234,56₽  |  1234.56 RUB  |  299р  |  1234р56к  |  -1 500,00 ₽
    """
    patterns = [
        # "1 234,56 ₽" or "1 234,56₽" or "1234,56 руб"
        r'[-−]?\s*(\d[\d\s]*\d),(\d{2})\s*(?:₽|руб|RUB|р\.)',
        # "1234.56 RUB" or "1234.56₽"
        r'[-−]?\s*(\d[\d\s]*\d)\.(\d{2})\s*(?:₽|руб|RUB|р\.)',
        # "299₽" or "299 руб" — no kopecks
        r'[-−]?\s*(\d[\d\s]*\d)\s*(?:₽|руб|RUB|р\.)',
        # "Покупка 299р" or "Сумма: 1500"
        r'(?:покупка|сумма|списание|оплата|платёж|платеж)[:\s]*[-−]?\s*(\d[\d\s]*[\d])[,.]?(\d{0,2})\s*(?:₽|руб|RUB|р\.?)?',
        # Fallback: any number followed by currency symbol
        r'(\d[\d\s]*\d)[,.](\d{2})\s*(?:₽|руб|RUB|р)',
        # Just a number with currency
        r'(\d{2,7})\s*(?:₽|руб|RUB|р\.)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            try:
                integer_part = groups[0].replace(" ", "").replace("\u00a0", "")
                decimal_part = groups[1] if len(groups) > 1 and groups[1] else "00"
                if not decimal_part:
                    decimal_part = "00"
                amount_str = f"{integer_part}.{decimal_part}"
                amount = Decimal(amount_str)
                if 0 < amount < 1_000_000:  # sanity check
                    return amount
            except (InvalidOperation, IndexError, ValueError):
                continue
    return None


def extract_date(text: str) -> Optional[str]:
    """
    Extract transaction date from text.
    Returns ISO format string or None.
    """
    patterns = [
        # "15.04.2025" or "15.04.25"
        (r'(\d{2})\.(\d{2})\.(\d{4})', "%d.%m.%Y"),
        (r'(\d{2})\.(\d{2})\.(\d{2})\b', "%d.%m.%y"),
        # "15 апр 2025" or "15 апреля 2025"
        (r'(\d{1,2})\s+(янв\w*|фев\w*|мар\w*|апр\w*|мая?|июн\w*|июл\w*|авг\w*|сен\w*|окт\w*|ноя\w*|дек\w*)\s*(\d{4})?', None),
        # "2025-04-15"
        (r'(\d{4})-(\d{2})-(\d{2})', "%Y-%m-%d"),
    ]

    month_map = {
        "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "мая": 5,
        "июн": 6, "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12,
    }

    for pattern, fmt in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                if fmt:
                    date_str = match.group(0)
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                else:
                    # Russian month name
                    day = int(match.group(1))
                    month_str = match.group(2).lower()[:3]
                    year = int(match.group(3)) if match.group(3) else datetime.now().year
                    month = month_map.get(month_str)
                    if month and 1 <= day <= 31:
                        return f"{year}-{month:02d}-{day:02d}"
            except (ValueError, KeyError):
                continue
    return None


def extract_merchant(text: str) -> Optional[str]:
    """
    Extract merchant name from Russian bank notification text.
    """
    patterns = [
        # "Покупка. YANDEX.PLUS" or "Оплата: Netflix"
        r'(?:покупка|оплата|списание|платёж|платеж|перевод)[.:\s]+([A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё0-9\s\.\-_]{2,40})',
        # "Мерчант: ..." or "Получатель: ..."
        r'(?:мерчант|получатель|магазин|компания)[:\s]+([A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё0-9\s\.\-_]{2,40})',
        # Common pattern: "YANDEX.PLUS" or "SPOTIFY" — all caps latin
        r'\b([A-Z][A-Z0-9\.\-_]{2,30})\b',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE if 'А-Я' in pattern else 0)
        if match:
            merchant = match.group(1).strip().rstrip(".")
            # Skip common non-merchant words
            skip_words = {"SMS", "PUSH", "MIR", "VISA", "MASTERCARD", "RUB", "RUR", "BANK", "КАРТА", "СЧЁТ", "БАЛАНС"}
            if merchant.upper() not in skip_words and len(merchant) > 2:
                return merchant
    return None


def extract_bank_name(text: str) -> Optional[str]:
    """
    Detect which bank the notification is from.
    """
    bank_patterns = {
        "Сбербанк": [r"сбер(?:банк)?", r"sber", r"900\b"],
        "Тинькофф": [r"тинькофф", r"tinkoff", r"t-bank"],
        "Альфа-Банк": [r"альфа[\s-]?банк", r"alfa[\s-]?bank"],
        "ВТБ": [r"\bвтб\b", r"\bvtb\b"],
        "Газпромбанк": [r"газпром", r"gazprom"],
        "Райффайзен": [r"райфф", r"raiffeisen"],
        "Россельхозбанк": [r"рсхб", r"россельхоз"],
        "Открытие": [r"открытие", r"otkritie"],
        "Совкомбанк": [r"совком", r"sovcom"],
        "Почта Банк": [r"почта\s*банк"],
    }

    text_lower = text.lower()
    for bank_name, patterns in bank_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return bank_name
    return None


def parse_ocr_text(text: str) -> dict:
    """
    Full parsing pipeline: extract all structured data from OCR text.
    """
    return {
        "amount": extract_amount(text),
        "merchant": extract_merchant(text),
        "transaction_date": extract_date(text),
        "bank_name": extract_bank_name(text),
    }

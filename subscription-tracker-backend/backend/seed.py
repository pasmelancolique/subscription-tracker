"""
Run once to seed the database with known services and banks.
Usage: python seed.py
"""
from database import engine, SessionLocal, Base
from models import Service, Bank


SERVICES = [
    {
        "name": "Яндекс Плюс",
        "category": "Развлечения",
        "website": "https://plus.yandex.ru",
        "price_plans": {"monthly": 399, "yearly": 1990, "aliases": ["YANDEX.PLUS", "YA.PLUS", "ЯНДЕКС ПЛЮС"]},
    },
    {
        "name": "YouTube Premium",
        "category": "Видео",
        "website": "https://youtube.com/premium",
        "price_plans": {"monthly": 299, "yearly": 2990, "aliases": ["YOUTUBE PREMIUM", "YOUTUBE", "GOOGLE*YOUTUBE"]},
    },
    {
        "name": "Netflix",
        "category": "Видео",
        "website": "https://netflix.com",
        "price_plans": {"monthly": 999, "aliases": ["NETFLIX", "NETFLIX.COM"]},
    },
    {
        "name": "Spotify",
        "category": "Музыка",
        "website": "https://spotify.com",
        "price_plans": {"monthly": 299, "aliases": ["SPOTIFY", "SPOTIFY AB"]},
    },
    {
        "name": "VK Музыка",
        "category": "Музыка",
        "website": "https://music.vk.com",
        "price_plans": {"monthly": 249, "aliases": ["VK MUSIC", "VK МУЗЫКА", "VKMUSIC"]},
    },
    {
        "name": "Кинопоиск",
        "category": "Видео",
        "website": "https://kinopoisk.ru",
        "price_plans": {"monthly": 299, "aliases": ["КИНОПОИСК", "KINOPOISK"]},
    },
    {
        "name": "Okko",
        "category": "Видео",
        "website": "https://okko.tv",
        "price_plans": {"monthly": 299, "aliases": ["OKKO", "ОККО"]},
    },
    {
        "name": "IVI",
        "category": "Видео",
        "website": "https://ivi.ru",
        "price_plans": {"monthly": 399, "yearly": 3588, "aliases": ["IVI", "ИВИ"]},
    },
    {
        "name": "Apple Music",
        "category": "Музыка",
        "website": "https://music.apple.com",
        "price_plans": {"monthly": 269, "aliases": ["APPLE MUSIC", "APPLE.COM/BILL"]},
    },
    {
        "name": "Telegram Premium",
        "category": "Мессенджеры",
        "website": "https://telegram.org",
        "price_plans": {"monthly": 299, "yearly": 2390, "aliases": ["TELEGRAM", "TELEGRAM PREMIUM"]},
    },
    {
        "name": "ChatGPT Plus",
        "category": "AI",
        "website": "https://chat.openai.com",
        "price_plans": {"monthly": 1890, "aliases": ["OPENAI", "CHATGPT"]},
    },
    {
        "name": "Claude Pro",
        "category": "AI",
        "website": "https://claude.ai",
        "price_plans": {"monthly": 1890, "aliases": ["ANTHROPIC", "CLAUDE"]},
    },
    {
        "name": "Литрес Подписка",
        "category": "Книги",
        "website": "https://litres.ru",
        "price_plans": {"monthly": 399, "aliases": ["ЛИТРЕС", "LITRES"]},
    },
    {
        "name": "Яндекс Музыка",
        "category": "Музыка",
        "website": "https://music.yandex.ru",
        "price_plans": {"monthly": 299, "aliases": ["YANDEX.MUSIC", "ЯНДЕКС МУЗЫКА"]},
    },
    {
        "name": "МТС Premium",
        "category": "Телеком",
        "website": "https://mts.ru",
        "price_plans": {"monthly": 299, "aliases": ["МТС PREMIUM", "MTS PREMIUM"]},
    },
    {
        "name": "СберПрайм",
        "category": "Финансы",
        "website": "https://sber.ru",
        "price_plans": {"monthly": 399, "yearly": 3990, "aliases": ["СБЕРПРАЙМ", "SBER PRIME"]},
    },
    {
        "name": "Wink",
        "category": "Видео",
        "website": "https://wink.ru",
        "price_plans": {"monthly": 299, "aliases": ["WINK", "ВИНК"]},
    },
    {
        "name": "START",
        "category": "Видео",
        "website": "https://start.ru",
        "price_plans": {"monthly": 299, "aliases": ["START", "СТАРТ"]},
    },
]

BANKS = [
    {
        "name": "Сбербанк",
        "bic": "044525225",
        "sms_regex": r"СБЕРБАНК|SBERBANK|900",
        "push_regex": r"Сбер|SberBank",
    },
    {
        "name": "Тинькофф",
        "bic": "044525974",
        "sms_regex": r"Тинькофф|Tinkoff|T-Bank",
        "push_regex": r"Тинькофф|Tinkoff",
    },
    {
        "name": "Альфа-Банк",
        "bic": "044525593",
        "sms_regex": r"Альфа|Alfa|ALFABANK",
        "push_regex": r"Альфа-Банк|Alfa-Bank",
    },
    {
        "name": "ВТБ",
        "bic": "044525187",
        "sms_regex": r"ВТБ|VTB",
        "push_regex": r"ВТБ|VTB",
    },
    {
        "name": "Газпромбанк",
        "bic": "044525823",
        "sms_regex": r"Газпром|GPB",
        "push_regex": r"Газпромбанк",
    },
    {
        "name": "Райффайзен",
        "bic": "044525700",
        "sms_regex": r"Raiffeisen|Райфф",
        "push_regex": r"Raiffeisen",
    },
    {
        "name": "Россельхозбанк",
        "bic": "044525111",
        "sms_regex": r"РСХБ|Россельхоз",
        "push_regex": r"Россельхозбанк",
    },
    {
        "name": "Открытие",
        "bic": "044525985",
        "sms_regex": r"Открытие|Otkritie",
        "push_regex": r"Открытие",
    },
    {
        "name": "Совкомбанк",
        "bic": "044525360",
        "sms_regex": r"Совком|Sovcom",
        "push_regex": r"Совкомбанк",
    },
    {
        "name": "Почта Банк",
        "bic": "044525214",
        "sms_regex": r"Почта Банк|Pochtabank",
        "push_regex": r"Почта Банк",
    },
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Seed services
        for svc_data in SERVICES:
            existing = db.query(Service).filter(Service.name == svc_data["name"]).first()
            if not existing:
                svc = Service(**svc_data)
                db.add(svc)
                print(f"  + Service: {svc_data['name']}")
            else:
                print(f"  = Service exists: {svc_data['name']}")

        # Seed banks
        for bank_data in BANKS:
            existing = db.query(Bank).filter(Bank.name == bank_data["name"]).first()
            if not existing:
                bank = Bank(**bank_data)
                db.add(bank)
                print(f"  + Bank: {bank_data['name']}")
            else:
                print(f"  = Bank exists: {bank_data['name']}")

        db.commit()
        print("\nSeed complete.")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

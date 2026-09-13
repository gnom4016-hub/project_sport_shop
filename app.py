import logging
import random
import time

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Разрешаем запросы с любого origin (в т.ч. с домена Tilda).
# Если хотите сузить — замените "*" на конкретный домен сайта, например
# CORS(app, resources={r"/*": {"origins": "https://verbally-glowing-pine.tilda.ws"}})
CORS(app)

# ВАЖНО: v1, v2 и обычный /cards/detail отключены Wildberries — сейчас
# рабочий только v4. Если WB снова сменит версию, чинить нужно здесь.
WB_CARD_ENDPOINTS = [
    "https://card.wb.ru/cards/v4/detail",
]

DEFAULT_PARAMS = {
    "appType": 1,
    "curr": "rub",
    "spp": 30,
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://www.wildberries.ru",
    "Referer": "https://www.wildberries.ru/",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# -1257786 — подтверждённый рабочий dest (Москва). Остальные "регионы",
# которые были здесь раньше, я не проверял, и один из них похоже вызывал
# HTTP 400 — убрал, чтобы не гадать вслепую.
DEST_CANDIDATES = [-1257786]


def _parse_price_from_product(product: dict):
    """
    Извлекает цену из объекта товара.
    WB хранит цену в копейках, в разных полях в зависимости от версии API.
    """
    try:
        sizes = product.get("sizes")
        if sizes:
            price_info = sizes[0].get("price") or {}
            price_kopecks = price_info.get("product") or price_info.get("total")
            if price_kopecks:
                return round(price_kopecks / 100)
    except (KeyError, IndexError, TypeError):
        pass

    for field in ("salePriceU", "priceU"):
        val = product.get(field)
        if val:
            return round(val / 100)

    return None


def get_competitor_price(article, timeout: int = 8, max_retries: int = 2):
    """
    Получает актуальную цену товара Wildberries по артикулу.
    Возвращает (price, last_error): price — int или None.
    """
    try:
        article = int(str(article).strip())
    except (ValueError, TypeError):
        logger.warning(f"Некорректный артикул: {article!r}")
        return None, "invalid_article"

    session = requests.Session()
    session.headers.update(HEADERS)

    last_error = None

    for attempt in range(max_retries + 1):
        for dest in DEST_CANDIDATES:
            for endpoint in WB_CARD_ENDPOINTS:
                params = {
                    **DEFAULT_PARAMS,
                    "dest": dest,
                    "nm": article,
                }
                try:
                    resp = session.get(endpoint, params=params, timeout=timeout)

                    if resp.status_code != 200:
                        last_error = f"HTTP {resp.status_code} на {endpoint} (dest={dest})"
                        logger.info(last_error)
                        continue

                    try:
                        data = resp.json()
                    except ValueError:
                        last_error = f"Невалидный JSON от {endpoint} (dest={dest})"
                        logger.info(last_error)
                        continue

                    products = (data.get("data") or {}).get("products") or []
                    if not products:
                        last_error = f"Пустой products от {endpoint} (dest={dest})"
                        logger.info(last_error)
                        continue

                    price = _parse_price_from_product(products[0])
                    if price is not None:
                        logger.info(
                            f"Цена для {article} получена: {price}₽ "
                            f"(endpoint={endpoint}, dest={dest})"
                        )
                        return price, None
                    else:
                        last_error = f"Не найдено поле цены в ответе (dest={dest})"
                        logger.info(last_error)

                except requests.exceptions.Timeout:
                    last_error = f"Timeout на {endpoint} (dest={dest})"
                    logger.warning(last_error)
                except requests.exceptions.RequestException as e:
                    last_error = f"RequestException: {e}"
                    logger.warning(last_error)

        if attempt < max_retries:
            time.sleep(1 + random.random())

    logger.error(f"Не удалось получить цену для артикула {article}. Последняя ошибка: {last_error}")
    return None, last_error


@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok", "service": "wb-price-monitor"})


@app.route("/price/<article>", methods=["GET"])
def price_route(article):
    """JSON-версия, удобна для отладки в браузере/Postman."""
    price, error = get_competitor_price(article)
    if price is None:
        return jsonify({
            "article": article,
            "price": None,
            "error": error or "not_found",
        }), 404

    return jsonify({
        "article": article,
        "price": price,
        "display": f"{price} \u20bd",
    })


@app.route("/update-prices", methods=["GET"])
def update_prices_route():
    """
    Роут, который реально дёргает widget.js:
    GET /update-prices?article=<артикул>
    Ответ — простой текст (widget.js делает response.text()), НЕ JSON.
    """
    article = request.args.get("article")
    if not article:
        return "Ошибка: не передан параметр article", 400

    price, error = get_competitor_price(article)
    if price is None:
        logger.warning(f"Артикул {article}: не удалось получить цену ({error})")
        return f"Ошибка WB (не удалось получить цену: {error})", 404

    return f"{price} \u20bd"


if __name__ == "__main__":
    app.run(debug=True)
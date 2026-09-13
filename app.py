import requests
import time
import random
import logging

logger = logging.getLogger(__name__)

# Основные точки входа WB API (актуальны на момент написания, могут меняться)
WB_CARD_ENDPOINTS = [
    "https://card.wb.ru/cards/v2/detail",
    "https://card.wb.ru/cards/v1/detail",
    "https://card.wb.ru/cards/detail",
]

# dest — код региона доставки. 123585668 = Москва (стандартный дефолт).
# Если для вашего кейса важен конкретный регион — подставьте свой.
DEFAULT_PARAMS = {
    "appType": 1,
    "curr": "rub",
    "dest": -1257786,       # общий/дефолтный dest, работает в большинстве случаев
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

# Набор dest-кодов для разных регионов — WB иногда отдаёт 404 для одного региона,
# но нормально отвечает для другого. Перебираем по очереди.
DEST_CANDIDATES = [-1257786, 123585668, -1216601, -5817441]


def _parse_price_from_product(product: dict):
    """
    Извлекает цену из объекта товара.
    WB хранит цену в копейках, в разных полях в зависимости от версии API:
    - sizes[0].price.product / total
    - salePriceU / priceU (устаревшие поля)
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

    # fallback на старые поля
    for field in ("salePriceU", "priceU"):
        val = product.get(field)
        if val:
            return round(val / 100)

    return None


def get_competitor_price(article, timeout: int = 8, max_retries: int = 2):
    """
    Получает актуальную цену товара Wildberries по артикулу.

    :param article: артикул товара (int или str)
    :param timeout: таймаут запроса в секундах
    :param max_retries: количество повторных попыток при неудаче
    :return: цена в рублях (int) или None, если не удалось получить
    """
    try:
        article = int(str(article).strip())
    except (ValueError, TypeError):
        logger.warning(f"Некорректный артикул: {article!r}")
        return None

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
                        continue

                    try:
                        data = resp.json()
                    except ValueError:
                        last_error = f"Невалидный JSON от {endpoint} (dest={dest})"
                        continue

                    products = (data.get("data") or {}).get("products") or []
                    if not products:
                        last_error = f"Пустой products от {endpoint} (dest={dest})"
                        continue

                    price = _parse_price_from_product(products[0])
                    if price is not None:
                        logger.info(
                            f"Цена для {article} получена: {price}₽ "
                            f"(endpoint={endpoint}, dest={dest})"
                        )
                        return price
                    else:
                        last_error = f"Не найдено поле цены в ответе (dest={dest})"

                except requests.exceptions.Timeout:
                    last_error = f"Timeout на {endpoint} (dest={dest})"
                except requests.exceptions.RequestException as e:
                    last_error = f"RequestException: {e}"

        # небольшая пауза перед повтором, чтобы не словить rate-limit
        if attempt < max_retries:
            time.sleep(1 + random.random())

    logger.error(f"Не удалось получить цену для артикула {article}. Последняя ошибка: {last_error}")
    return None


# Пример использования во Flask-роуте:
#
# @app.route("/price/<article>")
# def price_route(article):
#     price = get_competitor_price(article)
#     if price is None:
#         return jsonify({"error": "price not found"}), 404
#     return jsonify({"article": article, "price": price, "display": f"{price} ₽"})
import os
import requests
from flask import Flask, send_from_directory, request

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/static/widget.js')
def serve_widget():
    return send_from_directory('static', 'widget.js')

def get_competitor_price(article):
    # Прямой API-запрос к карточке товара Wildberries
    url = f"https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={article}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        products = data.get('data', {}).get('products', [])
        if products:
            # Цена в копейках, делим на 100
            price_raw = products[0].get('sizes', [{}])[0].get('price', {}).get('product', 0)
            if price_raw:
                return f"{price_raw // 100} ₽"
        return "Товар не найден"
    except Exception as e:
        return f"Ошибка запроса: {e}"

@app.route('/update-prices')
def update_prices():
    article = request.args.get('article', '')
    if not article:
        return "Артикул не указан"
    return get_competitor_price(article)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
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
    # Актуальный публичный API v2 Wildberries
    url = f"https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={article}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.9'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return f"Ошибка WB ({response.status_code})"
            
        data = response.json()
        products = data.get('data', {}).get('products', [])
        
        if products:
            product = products[0]
            # В v2 цена берется из списка размеров (sizes)
            sizes = product.get('sizes', [])
            if sizes:
                price_info = sizes[0].get('price', {})
                # Берем цену с учетом СПП (product) или базовую (total)
                price_raw = price_info.get('product') or price_info.get('total')
                if price_raw:
                    return f"{price_raw // 100} ₽"
                    
            # Резервный поиск по ключу цены в корне
            price_raw = product.get('salePriceU') or product.get('priceU')
            if price_raw:
                return f"{price_raw // 100} ₽"
                
        return "Товар не найден"
    except Exception as e:
        return f"Ошибка: {e}"

@app.route('/update-prices')
def update_prices():
    article = request.args.get('article', '')
    if not article:
        return "Артикул не указан"
    return get_competitor_price(article)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
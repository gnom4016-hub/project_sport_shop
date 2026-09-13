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
    try:
        art = int(article)
        vol = art // 100000
        part = art // 1000
        
        # Динамический адрес хранения карточки WB
        url = f"https://basket-10.wbbasket.ru/vol{vol}/part{part}/{art}/info/price-history.json"
        
        # Если статический JSON не отдается, берем через общий API поиска карточки:
        api_url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&nm={article}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        res = requests.get(api_url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            products = data.get('data', {}).get('products', [])
            if products:
                price_raw = products[0].get('salePriceU') or products[0].get('priceU')
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
    
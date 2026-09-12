import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, send_from_directory

app = Flask(__name__)

# Роут для отдачи JS-файла виджета в Tilda
@app.route('/static/widget.js')
def serve_widget():
    return send_from_directory('static', 'widget.js')

# Улучшенный парсер цен Wildberries
def get_competitor_price(article):
    url = f"https://www.wildberries.ru/catalog/{article}/detail.aspx"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Поиск элемента цены
        price_element = soup.find('span', class_='price-block__final-price')
        if price_element:
            return price_element.text.strip()
        return "Цена не найдена"
    except Exception as e:
        return f"Ошибка запроса: {e}"

# Роут для запуска обновления цен
@app.route('/update-prices')
def update_prices():
    # Пример вызова парсинга для артикула
    # В реальном проекте здесь будет логика работы с БД (SQLAlchemy)
    sample_article = "12345678"
    price = get_competitor_price(sample_article)
    return f"Статус: Обновлено. Результат тестового парсинга: {price}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
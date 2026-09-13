(function () {
  console.log("Виджет мониторинга цен успешно подключен :)");

  // Функция для запроса обновленных данных с бэкенда
  async function fetchCompetitorPrice(article) {
    try {
      // Запрос к твоему серверу на Render
      const response = await fetch(`https://project-sport-shop.onrender.com/update-prices?article=${article}`);
      const data = await response.text();
      return data;
    } catch (error) {
      console.error("Ошибка при получении цены:", error);
      return null;
    }
  }

  // Пример интеграции в DOM страницы Tilda
  async function initWidget() {
    // В зависимости от того, как устроена верстка в Тильде, находим нужный блок
    const priceContainer = document.querySelector('.t-store__card__price'); 
    
    if (priceContainer) {
      // Пример артикула (в реальности его можно читать из дата-атрибута товара)
      const testArticle = "12345678"; 
      
      const result = await fetchCompetitorPrice(testArticle);
      
      if (result) {
        // Создаем плашку с ценой конкурента
        const badge = document.createElement('div');
        badge.style.cssText = 'margin-top: 5px; font-size: 12px; color: #ff5500; font-weight: bold;';
        badge.innerText = `Конкуренты (WB): ${result}`;
        
        priceContainer.appendChild(badge);
      }
    }
  }

  // Запускаем скрипт после полной загрузки страницы
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWidget);
  } else {
    initWidget();
  }
})();
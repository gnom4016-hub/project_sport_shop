(function () {
  console.log("Виджет мониторинга цен успешно подключен :)");

  async function fetchCompetitorPrice(article) {
    try {
      const response = await fetch(`https://project-sport-shop.onrender.com/update-prices?article=${article}`);
      const data = await response.text();
      return data;
    } catch (error) {
      console.error("Ошибка при получении цены:", error);
      return null;
    }
  }

  async function initWidget() {
    // Внимание: укажи здесь реальный артикул Wildberries для теста (например: 211605633)
    const testArticle = "211605633"; 
    const price = await fetchCompetitorPrice(testArticle);

    // Ищем контейнер цены в Тильде или выводим плашку вверху страницы для теста
    const targetElement = document.querySelector('.t-store__card__price') || document.body;

    if (targetElement && price) {
      const badge = document.createElement('div');
      badge.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #000;
        color: #fff;
        padding: 12px 20px;
        border-radius: 8px;
        font-family: sans-serif;
        font-weight: bold;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        z-index: 999999;
      `;
      badge.innerText = `WB (арт. ${testArticle}): ${price}`;
      document.body.appendChild(badge);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWidget);
  } else {
    initWidget();
  }
})();
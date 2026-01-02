import os  # noqa: F401
import sys  # noqa: F401


import django  # noqa: F401

from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


from load_django import *  # noqa: F403,F401


from parser_app.models import Product


def pars():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)  # создвем браузер
        context = browser.new_context()  # в одном контекстте хранятся куки,как профиль
        page = context.new_page()  # создаем новую страницу
        try:
            page.goto("https://brain.com.ua/", timeout=60000, wait_until="domcontentloaded")
        except PlaywrightTimeoutError:
            print("Сторiнка не загрузилась за 60 секунд")
        try:
            search_input = page.locator("(//input[contains(@class,'quick-search-input')])[2]")
            search_input.wait_for(state="visible")
            search_input.click()
            search_input.type("Apple iPhone 15 128GB Black", delay=50)
            search_input.click()
        except PlaywrightTimeoutError:
            print("Поле пошуку не знайдено ")
        try:

            search_form = page.locator("(//form[contains(@class,'qsr-form')])")
            search_form.wait_for(state="visible")
            search_button = search_form.locator("//input[contains(@class,'qsr-submit')]")
            search_button.click()
        except PlaywrightTimeoutError:
            print("Форма пошуку або кнопка Знайти не знайденi")

        # ждём, пока появятся карточки
        try:
            page.wait_for_selector("//div[contains(@class,'br-pcg-product-wrapper')]")
        except PlaywrightTimeoutError:
            print("Карточки товарiв не загрузились")

        # находим первую карточку
        try:
            first_block = page.locator("(//div[contains(@class,'br-pcg-product-wrapper')])[1]")

            # находим ссылку внутри карточки
            first_link = first_block.locator("//a").first

            # кликаем
            first_link.click()
        except PlaywrightTimeoutError:
            print("Не вдалося знайти першу карточку или ссилку")

        # текущий URL страницы
        try:
            URL = page.url
            print("URL:", URL)
        except AttributeError:
            print("Не удалось получить URL — страница не инициализирована")
            URL = None

        # Берем данные с карточки для записи в базу данных
        product = {}
        # название товара
        try:
            title_el = page.locator("//h1[contains(@class,'desktop-only-title')]")
            title_el.wait_for(state="visible", timeout=5000)  # 5 секунд

            product["title"] = title_el.inner_text().strip()

        except PlaywrightTimeoutError:
            product["title"] = None

        print("title:", product["title"])

        # старая цена, если есть скидки
        try:
            o_price = page.locator("//div[contains(@class, 'br-pr-op')]//span")
            o_price.wait_for(state="visible", timeout=5000)
            product["old_price"] = o_price.inner_text().strip()
        except PlaywrightTimeoutError:
            product["old_price"] = None

        # новая цена - всегда есть
        try:
            price_block = page.query_selector("//div[contains(@class,'br-pr-np')]")

            red_prices = price_block.query_selector_all("//span[contains(@class,'red-price')]")
            # (выдаст пустой список есл елемента нет, а не исключение. тут проверяем - elements)
            if red_prices:
                product["new_price"] = red_prices[0].inner_text().strip()
                product["is_discount"] = True
            else:
                product["new_price"] = (
                    price_block.query_selector("//div[contains(@class,'price-wrapper')]/span").inner_text().strip()
                )
                # тут утверджаем - element
                product["is_discount"] = False
        except AttributeError:
            product["new_price"] = None
            product["is_discount"] = False

        print("old_price", product["old_price"])
        print("new_price", product["new_price"])
        print("is_discount", product["is_discount"])

        try:
            product_code = page.query_selector("//span[contains(@class, 'br-pr-code-val')]")
            product["product_code"] = product_code.inner_text().strip()
        except AttributeError:
            product["product_code"] = None  # код товара

        try:
            reviews_count = page.query_selector("//a[contains(@class, 'forbid-click')]//span")
            product["reviews_count"] = reviews_count.inner_text().strip()
        except AttributeError:
            product["reviews_count"] = None  # количество отзывов

        print("product_code", product["product_code"])
        print("reviews_count", product["reviews_count"])

        # базовый url для относительных ссылок
        base_url = "https://brain.com.ua"

        # ищем все картинки с классом br-main-img
        images = page.query_selector_all("//img[contains(@class, 'br-main-img')]")

        photo_urls = []

        for img in images:
            src = img.get_attribute("src")  # значение атрибута src
            if not src:
                continue

            if src.startswith("http"):
                photo_urls.append(src)
            else:
                photo_urls.append(base_url + src)

        # если картинок нет, photo_urls будет пустым списком
        product["images"] = photo_urls
        print("images:", product["images"])

        # найдем все характеристики и соберем их как слварь
        try:
            specifications_dict = {}

            sections = page.query_selector_all("//div[contains(@class, 'br-pr-chr-item')]")

            for section in sections:
                # название секции (Основні характеристики, Дисплей, и т.д.)
                section_name_element = section.query_selector("xpath=.//h3")
                if not section_name_element:
                    continue
                section_name = section_name_element.inner_text().strip()

                specifications_dict[section_name] = {}

                # строки характеристик — div, внутри которых есть ДВА span
                rows = section.query_selector_all("//div[span and count(span)=2]")

                for row in rows:
                    spans = row.query_selector_all("//span")
                    if len(spans) != 2:
                        continue

                    name = spans[0].inner_text().strip()
                    value = spans[1].inner_text().strip().replace("\xa0", "")

                    specifications_dict[section_name][name] = value

        except PlaywrightTimeoutError:
            specifications_dict = None

        product["specifications"] = specifications_dict
        print("specifications:", product["specifications"])

        try:
            product["color"] = specifications_dict.get("Фізичні характеристики", {}).get("Колір")
        except AttributeError:
            product["color"] = None

        try:
            product["memory"] = specifications_dict.get("Функції пам'яті", {}).get("Вбудована пам'ять")
        except AttributeError:
            product["memory"] = None

        try:
            product["manufacturer"] = specifications_dict.get("Інші", {}).get("Виробник")  # Производитель
        except AttributeError:
            product["manufacturer"] = None

        try:
            product["screen_size"] = specifications_dict.get("Дисплей", {}).get("Діагональ екрану")  # Диагональ экрана
        except AttributeError:
            product["screen_size"] = None

        try:
            product["resolution"] = specifications_dict.get("Дисплей", {}).get(
                "Роздільна здатність екрану"
            )  # роздiльна здатнiсть дiсплея
        except AttributeError:
            product["resolution"] = None

        for key, value in product.items():
            print("=" * 50)
            print(f"{key}: {value}")

        return URL, product


URL, product = pars()


#
#
def save_product(url: str, data: dict):
    """Сохраняет продукт в базу данных (update or create)."""

    product, created = Product.objects.get_or_create(url=url)

    product.title = data.get("title")
    product.color = data.get("color")
    product.memory = data.get("memory")
    product.manufacturer = data.get("manufacturer")

    product.old_price = data.get("old_price")
    product.new_price = data.get("new_price")
    product.is_discount = data.get("is_discount")

    product.images = data.get("images")
    product.code = data.get("product_code")
    product.reviews_count = data.get("reviews_count")
    product.screen_size = data.get("screen_size")
    product.resolution = data.get("resolution")
    product.specifications = data.get("specifications")

    product.save()


save_product(url=URL, data=product)

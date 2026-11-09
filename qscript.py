import json;
import logging;
import shutil;
import random;
import time;
from pathlib import Path;

from playwright.sync_api import sync_playwright;
from werkzeug.utils import secure_filename;


logger = logging.getLogger(__name__)


# Папка для сохранения видео
PATH_TO_VIDEO_FOLDER = "./video";


def CaptureVideo_Magento(
    url,
    company_name,
    language,
    country,
    postcode,
    city,
    street,
    house_no,
):
    """Запускает браузер и записывает выполнение сценария."""

    video_folder = Path(PATH_TO_VIDEO_FOLDER)
    video_folder.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as playwright:

            # Запускаем Chromium
            browser = playwright.chromium.launch(
                headless=False
            )

            try:
                # Создаём запись видео
                context = browser.new_context(
                    record_video_dir=str(video_folder),
                    record_video_size={
                        "width": 1280,
                        "height": 720
                    }
                )

                try:
                    page = None

                    # Внедряем собственный курсор и стили
                    context.add_init_script(
                        script=load_cursor_script()
                    )

                    # Создаём страницу
                    page = context.new_page()

                    # Открываем сайт
                    logger.info("Открываем: %s", url)

                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=30000
                    )

                    # Находим поисковое поле по селектору
                    search_field, target_x, target_y = find_element(
                        page,
                        'textarea[name="q"], input[name="q"]' # input[name="q"] - на всякий случай
                    )

                    # Перемещаем мышь на поисковое поле
                    smooth_move(
                        page,
                        end_x=target_x, 
                        end_y=target_y,
                        click_at_end=True 
                    )

                    page.wait_for_timeout(1000);

                    # Вводим поисковый запрос
                    type_like_human(
                        search_field,
                        f"Magento developer in {city}"
                    )

                    # Ожидаем обновления интерфейса
                    page.wait_for_timeout(2000)

                    # Ищем кнопку поиска в выпадающем меню
                    search_button, x, y = find_element(
                        page,
                        'form button[type="submit"]:visible'
                    )
                    
                    # Перемещаем мышь и нажимаем
                    smooth_move(
                        page,
                        end_x=x,
                        end_y=y,
                        click_at_end=True
                    )


                    page.wait_for_timeout(1000)


                    # Находим первую ссылку из поиска
                    first_result, x, y = find_element(
                        page,
                        'a[data-testid="result-title-a"]'
                    )

                    # Нажимаем первую ссылку
                    with page.expect_navigation(
                        wait_until="domcontentloaded",
                        timeout=30000
                    ):
                        smooth_move(
                            page,
                            start_x=0,
                            start_y=0,
                            end_x=x,
                            end_y=y,
                            click_at_end=True
                        )

                    # Временная пауза 
                    page.wait_for_timeout(4000)

                finally:
                    # Завершаем запись внутри Playwright
                    context.close()

                    # Получаем путь к видео
                    if page is not None:
                        recorded_video = page.video.path()

            finally:
                # Закрываем браузер до остановки Playwright
                browser.close()

        # Формируем итоговое имя видео
        safe_name = secure_filename(company_name) or "company"
        output_path = video_folder / f"{safe_name}.webm"

        # Перемещаем и переименовываем видео
        shutil.move(
            str(recorded_video),
            str(output_path)
        )

        return str(output_path.resolve())

    except Exception:
        logger.exception("Ошибка при обработке %s", company_name)
        return None





def smooth_move(
    page,
    end_x,
    end_y,
    start_x=None,
    start_y=None,
    click_at_end=False,
    steps=100,
    duration=2
):
    """
    Плавно перемещает мыши.

    Если start_x/start_y переданы — движение начнётся от них.
    Если не переданы — используются последние сохранённые координаты.
    При первом вызове стартовая точка будет (0, 0).
    """

    # Хранилище последних позиций для каждой страницы
    if not hasattr(smooth_move, "positions"):
        smooth_move.positions = {}

    page_id = id(page)

    # Если стартовые координаты не переданы —
    # берём их из сохранённого состояния
    if start_x is None or start_y is None:
        start_x, start_y = smooth_move.positions.get(page_id, (0, 0))

    for step in range(1, steps + 1):
        t = step / steps

        # Плавное ускорение и замедление
        # page.mouse.move(x, y, steps=50) - делает слишком резко и нельзя замедлить, поэтому делаем вручную
        progress = 3 * t**2 - 2 * t**3

        current_x = start_x + (end_x - start_x) * progress
        current_y = start_y + (end_y - start_y) * progress

        page.mouse.move(current_x, current_y)

        time.sleep(duration / steps)

    # Сохраняем последнюю позицию
    smooth_move.positions[page_id] = (end_x, end_y)

    # Клик в конечной точке
    if click_at_end:
        page.mouse.click(end_x, end_y)

    return end_x, end_y



def find_element(page, selector, timeout=10000):
    """
    Находит элемент и возвращаем его центральные координаты.
    """

    search_field = page.locator(selector).first

    # Ждём появления поля
    search_field.wait_for(
        state="visible",
        timeout=timeout
    )

    # Прокручиваем страницу к элементу,
    # если он находится за пределами видимой области
    search_field.scroll_into_view_if_needed()

    # Получаем расположение и размеры элемента
    box = search_field.bounding_box()

    if box is None:
        raise RuntimeError("Не удалось получить координаты поискового поля")

    # Вычисляем центр поля
    center_x = box["x"] + box["width"] / 2
    center_y = box["y"] + box["height"] / 2

    return search_field, center_x, center_y






def type_like_human(field, text, min_delay=0.06, max_delay=0.14):
    """
    Посимвольно вводит текст с небольшими случайными задержками.
    Имитируя ввод человека.


    field: Playwright Locator текстового поля.
    text: Текст для ввода.
    min_delay: Минимальная задержка между символами (сек).
    max_delay: Максимальная задержка между символами (сек).
    """

    # Проверяем доступность поля
    field.wait_for(state="visible", timeout=10000)

    if not field.is_editable():
        raise RuntimeError("Поле недоступно для ввода текста")

    for index, char in enumerate(text):

        # Вводим один символ
        field.press_sequentially(char)

        # Случайная задержка перед следующим символом
        if index < len(text) - 1:
            time.sleep(random.uniform(min_delay, max_delay))




# Встаривает js и css в нашу страницу
def load_cursor_script():
    assets_dir = Path(__file__).resolve().parent / "assets"

    css = (assets_dir / "cursor.css").read_text(encoding="utf-8")
    js = (assets_dir / "cursor.js").read_text(encoding="utf-8")

    # Передаём CSS в JavaScript
    script = f"window.__CURSOR_CSS__ = {json.dumps(css)};\n{js}"

    return script
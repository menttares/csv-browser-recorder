import argparse
import csv
import logging
import time
from pathlib import Path
from typing import Optional

import qscript


CSV_FILE = Path(__file__).resolve().parent / "input.csv"

REQUIRED_COLUMNS = (
    "URL",
    "Company Name",
    "Language",
    "Country",
    "Postcode",
    "City",
    "Street",
    "HouseNo",
)

logger = logging.getLogger(__name__)



def read_csv_file(file_path: Path) -> list[dict]:
    #читает CSV-файл и возвращает список строк

    with file_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(
            file,
            delimiter=";",
            quotechar='"'
        )

        if reader.fieldnames is None:
            return []

        missing_columns = [
            column for column in REQUIRED_COLUMNS
            if column not in reader.fieldnames
        ]
        if missing_columns:
            raise ValueError(
                f"{file_path}: отсутствуют столбцы CSV: "
                f"{', '.join(missing_columns)}"
            )

        return list(reader)



def preview_video(video_url: str, view_seconds: int) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)

        try:
            page = browser.new_page()

            response = page.goto(
                video_url,
                wait_until="load",
                timeout=30000
            )

            if response is None or not response.ok:
                raise RuntimeError(
                    f"Failed to open video: {video_url}"
                )

            if view_seconds == 0:
                input("Нажмите Enter, чтобы закрыть предпросмотр...")
            else:
                time.sleep(view_seconds)

        finally:
            browser.close()



def run_capture(
    server_url: Optional[str] = None,
    view_seconds: int = 5
    ) -> None:

    #Запускает обработку всех записей CSV

    rows = read_csv_file(CSV_FILE)

    if not rows:
        logger.info("CSV-файл не содержит данных.")
        return

    for index, row in enumerate(rows, start=1 ):

        company_name = (row.get("Company Name") or "").strip()
        missing_values = [
            column
            for column in ("Company Name", "URL", "City")
            if not (row.get(column) or "").strip()
        ]
        if missing_values:
            logger.error(
                "Пропуск строки %s: пустые обязательные поля: %s",
                index + 1,
                ", ".join(missing_values)
            )
            continue

        logger.info(
            "Обработка %s/%s: %s",
            index,
            len(rows),
            company_name
        )
        try:
            video_path = qscript.capture_video_magento(
                url=row["URL"],
                company_name=company_name,
                language=row["Language"],
                country=row["Country"],
                postcode=row["Postcode"],
                city=row["City"],
                street=row["Street"],
                house_no=row["HouseNo"]
            )
        except Exception:
            logger.exception(
                "Ошибка записи видео для %s",
                company_name
            )
            continue

        if not video_path:
            logger.error(
                "Не удалось записать видео для %s",
                company_name
            )
            continue

        logger.info("Видео сохранено: %s", video_path)

        # Без --server сохраняем прежнее поведение.
        if server_url is None:
            continue

        try:
            # Отложенный импорт: requests не нужен без --server.
            from video_client import upload_video

            video_url = upload_video(
                server_url=server_url,
                video_path=video_path,
                company_name=company_name
            )

            logger.info("Видео загружено: %s", video_url)

        except Exception:
            logger.exception(
                "Ошибка загрузки видео для %s",
                company_name
            )
            continue

        try:
            preview_video(video_url, view_seconds)

        except Exception:
            logger.exception(
                "Ошибка предпросмотра видео для %s",
                company_name
            )
            continue


def main():
    parser = argparse.ArgumentParser(
        description="CSV-driven browser video recorder"
    )

    parser.add_argument(
        "--server",
        type=str,
        default=None,
        help="URL сервера для загрузки видео"
    )

    parser.add_argument(
        "--view-seconds",
        type=int,
        default=5,
        help="Время предпросмотра; 0 — ждать Enter (по умолчанию 5)"
    )

    args = parser.parse_args()

    if args.view_seconds < 0:
        parser.error("--view-seconds не может быть отрицательным")

    run_capture(
        server_url=args.server,
        view_seconds=args.view_seconds
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    main()

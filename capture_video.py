from pathlib import Path;
import qscript;
import csv;



CSV_FILE = Path(__file__).parent / "input.csv";


def read_csv_file(file_path: Path) -> list[dict]:
    #читает CSV-файл и возвращает список строк

    with open(file_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(
            file,
            delimiter=";",
            quotechar='"'
        )

        return list(reader);


def run_capture():
    #Запускает обработку всех записей CSV

    rows = read_csv_file(CSV_FILE);

    if not rows:
        print("CSV-файл не содержит данных.");
        return;

    for index, row in enumerate(rows, start=1 ):
        print(f"\nОбработка записи {index}/{len(rows)}");

        video_path = qscript.CaptureVideo_Magento(
            url=row["URL"],
            company_name=row["Company Name"],
            language=row["Language"],
            country=row["Country"],
            postcode=row["Postcode"],
            city=row["City"],
            street=row["Street"],
            house_no=row["HouseNo"]
        )

        if video_path:
            print(f"Видео сохранено: {video_path}");
        else:
            print("Не удалось записать видео.");



if __name__ == "__main__":
    run_capture();

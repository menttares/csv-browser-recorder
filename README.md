# CSV Browser Recorder

Python browser automation using Playwright. The project records browser sessions
from `input.csv`, optionally uploads the resulting WebM files to the Flask
service, and stores the latest video URL for each company in SQLite.


[This_is_a_great_company_A.webm](https://github.com/user-attachments/assets/1620ae73-c295-4a57-a5f5-20e9f21c7167)

## Setup

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Run

Start the upload service in one terminal:

```bash
python -m web_service.web_service
```

Run the CSV recorder in another terminal:

```bash
python capture_video.py --server http://127.0.0.1:8000
```

Use `python capture_video.py` to record videos without uploading them. The
browser is visible, so a graphical desktop session is required.


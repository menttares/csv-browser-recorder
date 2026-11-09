
import logging
import sqlite3
from pathlib import Path

from flask import g
from urllib.parse import urlsplit, unquote


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "videos.db"

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    pass


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH, timeout=10)
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(error=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DATABASE_PATH) as db:
        db.execute("PRAGMA journal_mode=WAL")

        db.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL UNIQUE,
                file_path TEXT NOT NULL,
                video_url TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        removed = cleanup_invalid_videos(db)

        logger.info(
            "Database initialized. Invalid records removed: %s",
            removed
        )


def save_video(company_name: str, file_path: str, video_url: str):
    db = None

    try:
        db = get_db()
        db.execute("BEGIN IMMEDIATE")

        previous = db.execute(
            "SELECT file_path FROM videos WHERE company_name = ?",
            (company_name,)
        ).fetchone()

        db.execute("""
            INSERT INTO videos (company_name, file_path, video_url)
            VALUES (?, ?, ?)
            ON CONFLICT(company_name) DO UPDATE SET
                file_path = excluded.file_path,
                video_url = excluded.video_url,
                updated_at = datetime('now')
        """, (company_name, file_path, video_url))

        db.commit()

        return previous["file_path"] if previous else None

    except sqlite3.Error as error:
        if db is not None:
            db.rollback()

        raise DatabaseError("Failed to save video metadata") from error




def get_video_by_company(company_name: str):
    try:
        db = get_db()

        record = db.execute(
            """
            SELECT company_name, video_url
            FROM videos
            WHERE company_name = ?
            """,
            (company_name,)
        ).fetchone()

        return dict(record) if record else None

    except sqlite3.Error as error:
        raise DatabaseError(
            "Failed to get video metadata"
        ) from error





def cleanup_invalid_videos(db: sqlite3.Connection) -> int:
    records = db.execute(
        "SELECT id, file_path, video_url FROM videos"
    ).fetchall()

    invalid_ids = []
    upload_folder = (BASE_DIR / "uploads").resolve()

    for record_id, file_path, video_url in records:
        path = Path(file_path)
        url = urlsplit(video_url)

        file_valid = (
            path.is_absolute()
            and path.is_file()
            and path.resolve().parent == upload_folder
        )

        url_valid = (
            url.scheme in ("http", "https")
            and bool(url.netloc)
            and unquote(url.path) == f"/media/{path.name}"
        )

        if not file_valid or not url_valid:
            invalid_ids.append((record_id,))

    if invalid_ids:
        db.executemany(
            "DELETE FROM videos WHERE id = ?",
            invalid_ids
        )

    return len(invalid_ids)

from pathlib import Path

import requests


def UploadVideo(server_url: str, video_path: str, company_name: str) -> str:
    """Upload a video file and return its URL."""

    endpoint = f"{server_url.rstrip('/')}/upload"
    path = Path(video_path)

    with path.open("rb") as file:
        response = requests.post(
            endpoint,
            files={
                "file": (path.name, file, "video/webm")
            },
            data={
                "company_name": company_name
            },
            timeout=(5, 120),
        )

    response.raise_for_status()
    return response.json()["video_url"]


def GetVideoURL(server_url: str, company_name: str) -> str:
    """Get the video URL for the specified company."""

    endpoint = f"{server_url.rstrip('/')}/get_video_url"

    response = requests.get(
        endpoint,
        params={
            "company_name": company_name
        },
        timeout=10,
    )

    response.raise_for_status()
    return response.json()["video_url"]

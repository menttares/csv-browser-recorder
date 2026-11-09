
from pathlib import Path
from typing import Any

import requests


def _response_json(response: requests.Response) -> dict[str, Any]:
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Server returned an invalid JSON response")
    return payload


def upload_video(server_url: str, video_path: str, company_name: str) -> str:
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

    payload = _response_json(response)
    return str(payload["video_url"])


def get_video_url(server_url: str, company_name: str) -> str:
    """Get the video URL for the specified company."""

    endpoint = f"{server_url.rstrip('/')}/get_video_url"

    response = requests.get(
        endpoint,
        params={
            "company_name": company_name
        },
        timeout=10,
    )

    payload = _response_json(response)
    return str(payload["video_url"])


# Compatibility aliases for existing callers.
UploadVideo = upload_video
GetVideoURL = get_video_url

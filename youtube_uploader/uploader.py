"""Загрузка видео, обложек и работа с плейлистами."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

PRIVACY_STATUSES = ("private", "unlisted", "public")
RETRIABLE_STATUS_CODES = {500, 502, 503, 504}
MAX_RETRIES = 10
CHUNK_SIZE = 8 * 1024 * 1024  # 8 МБ, должно быть кратно 256 КБ


@dataclass
class VideoMetadata:
    title: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    category_id: str = "22"  # 22 = People & Blogs
    privacy_status: str = "private"
    made_for_kids: bool = False
    publish_at: str | None = None  # ISO 8601, напр. 2026-12-01T10:00:00Z (только для private)
    default_language: str | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Название видео не может быть пустым")
        if len(self.title) > 100:
            raise ValueError("Название длиннее 100 символов")
        if len(self.description.encode("utf-8")) > 5000:
            raise ValueError("Описание длиннее 5000 байт")
        if self.privacy_status not in PRIVACY_STATUSES:
            raise ValueError(f"privacy_status должен быть одним из {PRIVACY_STATUSES}")
        if self.publish_at and self.privacy_status != "private":
            raise ValueError("Отложенная публикация (publish_at) требует privacy_status=private")

    def to_body(self) -> dict:
        snippet: dict = {
            "title": self.title,
            "description": self.description,
            "categoryId": self.category_id,
        }
        if self.tags:
            snippet["tags"] = self.tags
        if self.default_language:
            snippet["defaultLanguage"] = self.default_language
        status: dict = {
            "privacyStatus": self.privacy_status,
            "selfDeclaredMadeForKids": self.made_for_kids,
        }
        if self.publish_at:
            status["publishAt"] = self.publish_at
        return {"snippet": snippet, "status": status}


ProgressCallback = Callable[[float], None]


class YouTubeUploader:
    def __init__(self, credentials=None, *, service=None, sleep: Callable[[float], None] = time.sleep):
        if service is None:
            service = build("youtube", "v3", credentials=credentials, cache_discovery=False)
        self.youtube = service
        self._sleep = sleep

    # --- загрузка -----------------------------------------------------------

    def upload_video(
        self,
        file_path: str | Path,
        metadata: VideoMetadata,
        *,
        on_progress: ProgressCallback | None = None,
        notify_subscribers: bool = True,
    ) -> dict:
        """Загружает видео возобновляемой загрузкой. Возвращает ресурс видео (с полем id)."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(path)

        media = MediaFileUpload(str(path), chunksize=CHUNK_SIZE, resumable=True)
        request = self.youtube.videos().insert(
            part="snippet,status",
            body=metadata.to_body(),
            media_body=media,
            notifySubscribers=notify_subscribers,
        )
        return self._run_resumable(request, on_progress)

    def _run_resumable(self, request, on_progress: ProgressCallback | None) -> dict:
        response = None
        retries = 0
        while response is None:
            try:
                status, response = request.next_chunk()
                retries = 0
                if status and on_progress:
                    on_progress(status.progress())
            except HttpError as e:
                if e.resp.status not in RETRIABLE_STATUS_CODES:
                    raise
                retries = self._backoff(retries, e)
            except (ConnectionError, TimeoutError, OSError) as e:
                retries = self._backoff(retries, e)
        if on_progress:
            on_progress(1.0)
        if "id" not in response:
            raise RuntimeError(f"Неожиданный ответ YouTube: {response}")
        return response

    def _backoff(self, retries: int, error: Exception) -> int:
        retries += 1
        if retries > MAX_RETRIES:
            raise RuntimeError(f"Загрузка не удалась после {MAX_RETRIES} попыток") from error
        self._sleep(random.random() * (2 ** retries))
        return retries

    # --- прочие операции ----------------------------------------------------

    def set_thumbnail(self, video_id: str, image_path: str | Path) -> dict:
        """Ставит обложку (JPG/PNG до 2 МБ). Канал должен быть подтверждён."""
        media = MediaFileUpload(str(image_path))
        return self.youtube.thumbnails().set(videoId=video_id, media_body=media).execute()

    def add_to_playlist(self, video_id: str, playlist_id: str) -> dict:
        body = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        }
        return self.youtube.playlistItems().insert(part="snippet", body=body).execute()

    def update_video(self, video_id: str, metadata: VideoMetadata) -> dict:
        body = metadata.to_body()
        body["id"] = video_id
        return self.youtube.videos().update(part="snippet,status", body=body).execute()

    def delete_video(self, video_id: str) -> None:
        self.youtube.videos().delete(id=video_id).execute()

    def my_channel(self) -> dict:
        resp = self.youtube.channels().list(part="snippet,statistics,contentDetails", mine=True).execute()
        items = resp.get("items", [])
        if not items:
            raise RuntimeError("У аккаунта нет YouTube-канала")
        return items[0]

    def list_my_videos(self, limit: int = 25) -> list[dict]:
        """Последние загрузки канала (из плейлиста uploads)."""
        uploads = self.my_channel()["contentDetails"]["relatedPlaylists"]["uploads"]
        videos: list[dict] = []
        page_token = None
        while len(videos) < limit:
            resp = self.youtube.playlistItems().list(
                part="snippet,status",
                playlistId=uploads,
                maxResults=min(50, limit - len(videos)),
                pageToken=page_token,
            ).execute()
            videos.extend(resp.get("items", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return videos[:limit]

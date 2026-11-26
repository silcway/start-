"""Загрузка и управление видео на YouTube-канале через YouTube Data API v3."""

from .auth import get_credentials
from .uploader import YouTubeUploader, VideoMetadata

__all__ = ["get_credentials", "YouTubeUploader", "VideoMetadata"]

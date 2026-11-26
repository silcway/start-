"""OAuth 2.0 авторизация для YouTube Data API v3."""

from __future__ import annotations

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# youtube.upload — загрузка видео; youtube — чтение и изменение данных канала
# (метаданные видео, плейлисты, обложки).
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

DEFAULT_CLIENT_SECRET = Path(os.environ.get("YOUTUBE_CLIENT_SECRET", "client_secret.json"))
DEFAULT_TOKEN = Path(os.environ.get("YOUTUBE_TOKEN", "token.json"))


def get_credentials(
    client_secret: Path = DEFAULT_CLIENT_SECRET,
    token_path: Path = DEFAULT_TOKEN,
    *,
    open_browser: bool = True,
) -> Credentials:
    """Возвращает действующие учётные данные.

    Сохранённый токен берётся из token_path и при необходимости обновляется.
    Если токена нет, запускается вход через браузер (нужен один раз).
    """
    creds: Credentials | None = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not client_secret.exists():
            raise FileNotFoundError(
                f"Не найден {client_secret}. Скачайте OAuth client ID (тип Desktop app) "
                "из Google Cloud Console — инструкция в README."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
        creds = flow.run_local_server(port=0, open_browser=open_browser)

    token_path.write_text(creds.to_json())
    try:
        token_path.chmod(0o600)
    except OSError:
        pass
    return creds

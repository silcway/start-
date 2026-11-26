"""Командная строка: python -m youtube_uploader <команда> ..."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from googleapiclient.errors import HttpError

from .auth import DEFAULT_CLIENT_SECRET, DEFAULT_TOKEN, get_credentials
from .uploader import PRIVACY_STATUSES, VideoMetadata, YouTubeUploader


def _metadata(args) -> VideoMetadata:
    description = args.description or ""
    if args.description_file:
        description = Path(args.description_file).read_text(encoding="utf-8")
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    return VideoMetadata(
        title=args.title,
        description=description,
        tags=tags,
        category_id=args.category,
        privacy_status=args.privacy,
        made_for_kids=args.made_for_kids,
        publish_at=args.publish_at,
        default_language=args.language,
    )


def _add_metadata_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--title", required=True, help="Название (до 100 символов)")
    p.add_argument("--description", help="Описание")
    p.add_argument("--description-file", help="Взять описание из файла")
    p.add_argument("--tags", help="Теги через запятую")
    p.add_argument("--category", default="22", help="ID категории (по умолчанию 22)")
    p.add_argument("--privacy", choices=PRIVACY_STATUSES, default="private")
    p.add_argument("--publish-at", help="Отложенная публикация, ISO 8601 (напр. 2026-12-01T10:00:00Z)")
    p.add_argument("--made-for-kids", action="store_true", help="Видео для детей")
    p.add_argument("--language", help="Язык видео, напр. ru")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="youtube_uploader", description="Загрузка видео на YouTube")
    parser.add_argument("--client-secret", type=Path, default=DEFAULT_CLIENT_SECRET)
    parser.add_argument("--token", type=Path, default=DEFAULT_TOKEN)
    parser.add_argument("--no-browser", action="store_true", help="Не открывать браузер автоматически")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("auth", help="Войти в Google-аккаунт и сохранить токен")
    sub.add_parser("channel", help="Показать подключённый канал")

    up = sub.add_parser("upload", help="Загрузить видео")
    up.add_argument("file", help="Путь к видеофайлу")
    _add_metadata_args(up)
    up.add_argument("--thumbnail", help="Обложка JPG/PNG")
    up.add_argument("--playlist", help="ID плейлиста, куда добавить видео")
    up.add_argument("--no-notify", action="store_true", help="Не уведомлять подписчиков")

    ls = sub.add_parser("list", help="Последние видео канала")
    ls.add_argument("--limit", type=int, default=10)

    upd = sub.add_parser("update", help="Изменить метаданные видео")
    upd.add_argument("video_id")
    _add_metadata_args(upd)

    rm = sub.add_parser("delete", help="Удалить видео")
    rm.add_argument("video_id")
    rm.add_argument("--yes", action="store_true", help="Без подтверждения")
    return parser


def _progress(fraction: float) -> None:
    sys.stdout.write(f"\rЗагрузка: {fraction * 100:5.1f}%")
    sys.stdout.flush()
    if fraction >= 1.0:
        sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    creds = get_credentials(args.client_secret, args.token, open_browser=not args.no_browser)
    if args.command == "auth":
        print(f"Готово, токен сохранён в {args.token}")
        return 0

    yt = YouTubeUploader(creds)
    try:
        if args.command == "channel":
            ch = yt.my_channel()
            s = ch.get("statistics", {})
            print(f"{ch['snippet']['title']}  (id: {ch['id']})")
            print(f"Подписчиков: {s.get('subscriberCount', '—')}, видео: {s.get('videoCount', '—')}")

        elif args.command == "upload":
            video = yt.upload_video(
                args.file, _metadata(args), on_progress=_progress, notify_subscribers=not args.no_notify
            )
            vid = video["id"]
            print(f"Видео загружено: https://youtu.be/{vid}  (статус: {video['status']['privacyStatus']})")
            if args.thumbnail:
                yt.set_thumbnail(vid, args.thumbnail)
                print("Обложка установлена")
            if args.playlist:
                yt.add_to_playlist(vid, args.playlist)
                print(f"Добавлено в плейлист {args.playlist}")

        elif args.command == "list":
            for item in yt.list_my_videos(args.limit):
                vid = item["snippet"]["resourceId"]["videoId"]
                privacy = item.get("status", {}).get("privacyStatus", "?")
                print(f"{vid}  [{privacy:8}]  {item['snippet']['title']}")

        elif args.command == "update":
            yt.update_video(args.video_id, _metadata(args))
            print(f"Видео {args.video_id} обновлено")

        elif args.command == "delete":
            if not args.yes and input(f"Удалить {args.video_id} безвозвратно? [y/N] ").lower() != "y":
                print("Отменено")
                return 1
            yt.delete_video(args.video_id)
            print(f"Видео {args.video_id} удалено")
    except HttpError as e:
        print(f"Ошибка YouTube API ({e.resp.status}): {e._get_reason()}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

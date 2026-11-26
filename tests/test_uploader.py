from unittest.mock import MagicMock

import httplib2
import pytest
from googleapiclient.errors import HttpError

from youtube_uploader import VideoMetadata, YouTubeUploader
from youtube_uploader.cli import build_parser, _metadata


def http_error(status):
    resp = httplib2.Response({"status": status})
    return HttpError(resp, b'{"error": {"message": "x"}}')


def make_uploader(next_chunk_effects):
    service = MagicMock()
    request = MagicMock()
    request.next_chunk.side_effect = next_chunk_effects
    service.videos.return_value.insert.return_value = request
    sleeps = []
    return YouTubeUploader(service=service, sleep=sleeps.append), service, sleeps


@pytest.fixture
def video_file(tmp_path):
    f = tmp_path / "clip.mp4"
    f.write_bytes(b"\x00" * 1024)
    return f


def test_metadata_body():
    body = VideoMetadata(title="Привет", tags=["a", "b"], privacy_status="unlisted").to_body()
    assert body["snippet"]["title"] == "Привет"
    assert body["snippet"]["tags"] == ["a", "b"]
    assert body["status"] == {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"title": " "},
        {"title": "x" * 101},
        {"title": "ok", "privacy_status": "secret"},
        {"title": "ok", "privacy_status": "public", "publish_at": "2026-12-01T10:00:00Z"},
        {"title": "ok", "description": "я" * 2501},  # 5002 байта
    ],
)
def test_metadata_validation(kwargs):
    with pytest.raises(ValueError):
        VideoMetadata(**kwargs)


def test_upload_success_reports_progress(video_file):
    status = MagicMock()
    status.progress.return_value = 0.5
    up, service, _ = make_uploader([(status, None), (None, {"id": "abc", "status": {}})])
    progress = []
    result = up.upload_video(video_file, VideoMetadata(title="t"), on_progress=progress.append)
    assert result["id"] == "abc"
    assert progress == [0.5, 1.0]
    kwargs = service.videos.return_value.insert.call_args.kwargs
    assert kwargs["part"] == "snippet,status"
    assert kwargs["notifySubscribers"] is True


def test_upload_retries_on_5xx(video_file):
    up, _, sleeps = make_uploader([http_error(503), ConnectionError(), (None, {"id": "abc"})])
    assert up.upload_video(video_file, VideoMetadata(title="t"))["id"] == "abc"
    assert len(sleeps) == 2


def test_upload_does_not_retry_on_4xx(video_file):
    up, _, sleeps = make_uploader([http_error(403)])
    with pytest.raises(HttpError):
        up.upload_video(video_file, VideoMetadata(title="t"))
    assert sleeps == []


def test_upload_gives_up_after_max_retries(video_file):
    up, _, _ = make_uploader([http_error(500)] * 20)
    with pytest.raises(RuntimeError, match="попыток"):
        up.upload_video(video_file, VideoMetadata(title="t"))


def test_upload_missing_file(tmp_path):
    up, _, _ = make_uploader([])
    with pytest.raises(FileNotFoundError):
        up.upload_video(tmp_path / "nope.mp4", VideoMetadata(title="t"))


def test_list_my_videos_paginates():
    service = MagicMock()
    service.channels.return_value.list.return_value.execute.return_value = {
        "items": [{"contentDetails": {"relatedPlaylists": {"uploads": "UU1"}}}]
    }
    service.playlistItems.return_value.list.return_value.execute.side_effect = [
        {"items": [{"n": 1}, {"n": 2}], "nextPageToken": "p2"},
        {"items": [{"n": 3}]},
    ]
    up = YouTubeUploader(service=service)
    assert [v["n"] for v in up.list_my_videos(limit=5)] == [1, 2, 3]


def test_cli_parses_upload():
    args = build_parser().parse_args(
        ["upload", "v.mp4", "--title", "T", "--tags", "a, b,,c", "--privacy", "public"]
    )
    meta = _metadata(args)
    assert meta.tags == ["a", "b", "c"]
    assert meta.privacy_status == "public"

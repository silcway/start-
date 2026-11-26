# start-

## YouTube: загрузка видео на канал

CLI и Python-модуль для загрузки и управления видео через YouTube Data API v3 (OAuth 2.0).

### 1. Настройка Google Cloud (один раз)

1. Откройте <https://console.cloud.google.com/> и создайте проект.
2. **APIs & Services → Library** → найдите **YouTube Data API v3** → **Enable**.
3. **APIs & Services → OAuth consent screen**: тип **External**, заполните название и почту.
   В разделе **Test users** добавьте Google-аккаунт, к которому привязан канал.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**,
   тип приложения **Desktop app**. Скачайте JSON и сохраните его в корне проекта как `client_secret.json`.

> `client_secret.json` и `token.json` — секреты, они уже в `.gitignore`. Не коммитьте их.

### 2. Установка и вход

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m youtube_uploader auth      # откроется браузер, войдите и разрешите доступ
python -m youtube_uploader channel   # проверка: покажет ваш канал
```

Вход запускайте на своём компьютере, потому что нужен браузер. После него появится `token.json`,
и дальше токен обновляется сам. Если браузер не открылся, запустите с `--no-browser` и откройте ссылку из терминала вручную.

### 3. Использование

```bash
# Загрузка (по умолчанию private)
python -m youtube_uploader upload video.mp4 \
  --title "Моё видео" --description-file desc.txt --tags "влог,путешествия" \
  --privacy public --thumbnail cover.jpg --playlist PLxxxxxxxx --language ru

# Отложенная публикация (только вместе с --privacy private)
python -m youtube_uploader upload video.mp4 --title "Премьера" --publish-at 2026-12-01T10:00:00Z

python -m youtube_uploader list --limit 20
python -m youtube_uploader update VIDEO_ID --title "Новое название" --privacy unlisted
python -m youtube_uploader delete VIDEO_ID
```

`update` перезаписывает snippet целиком: описание и теги, которые вы не передали, будут очищены.

Из Python:

```python
from youtube_uploader import get_credentials, YouTubeUploader, VideoMetadata

yt = YouTubeUploader(get_credentials())
video = yt.upload_video("video.mp4", VideoMetadata(title="Привет", privacy_status="unlisted"))
print("https://youtu.be/" + video["id"])
```

### Ограничения YouTube, о которых стоит знать

- **Квота:** по умолчанию 10 000 единиц в сутки. Одна загрузка стоит около 1 600 единиц, то есть примерно 6 видео в день.
  Увеличить квоту можно через форму аудита в Google Cloud.
- **Непроверенное приложение:** пока проект не прошёл аудит Google, все видео, загруженные через API,
  становятся **private** независимо от `--privacy`. Чтобы публиковать публично, подайте заявку на
  [API audit](https://support.google.com/youtube/contact/yt_api_form).
- **Режим Testing** у consent screen: refresh-токен живёт 7 дней, потом нужно снова выполнить `auth`.
  Чтобы токен не истекал, переведите приложение в **In production**.
- **Обложки** доступны только каналам, подтверждённым по телефону.

### Тесты

```bash
pip install pytest && python -m pytest
```

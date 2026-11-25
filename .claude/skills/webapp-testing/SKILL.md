---
name: webapp-testing
description: Test web apps end-to-end in a real browser with Playwright. Use when the user asks: протестируй сайт, e2e тест, проверь веб-приложение, playwright, screenshot the app. Отдел: 01 Разработка.
---

# Webapp Testing

_Отдел: 01 Разработка_

## Процесс

1. Найди команду запуска приложения (package.json scripts, Makefile, README) и подними dev-сервер в фоне.
2. Дождись готовности порта перед тестами.
3. Используй Playwright (require('playwright'), chromium.launch()); не переустанавливай браузеры.
4. Сначала разведка: открой страницу, сделай скриншот, собери селекторы (роль/текст/data-testid).
5. Пиши сценарии пользователя: навигация, формы, ошибки валидации, мобильная ширина (390px).
6. Собирай console errors и упавшие network-запросы.
7. Запускай с --trace off, трассу включай только для отладки падения.

## Результат

Скрипт/тесты Playwright, скриншоты, список найденных проблем.

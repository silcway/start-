---
name: web-artifacts
description: Build self-contained interactive HTML artifacts (single file). Use when the user asks: сделай артефакт, интерактивная страница, HTML-демо, калькулятор, web artifact. Отдел: 02 Дизайн.
---

# Web Artifacts

_Отдел: 02 Дизайн_

## Процесс

1. Один HTML-файл: инлайн CSS/JS; внешние библиотеки только с CDN с точной версией.
2. Цвета как CSS-переменные на :root + тёмная тема через prefers-color-scheme.
3. Без горизонтального скролла на 360px, отступы 16px.
4. localStorage только в try/catch и только для удобств.
5. Проверь в браузере (Playwright-скриншот) перед сдачей.

## Результат

Готовый .html файл.

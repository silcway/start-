---
name: gif-motion
description: Create animated GIFs and simple motion graphics. Use when the user asks: сделай гифку, анимация, GIF, motion, анимированный стикер. Отдел: 02 Дизайн.
---

# GIF Motion

_Отдел: 02 Дизайн_

## Процесс

1. Определи длительность (1–4 c), размер (≤ 480px для мессенджеров), fps 12–20.
2. Генерируй кадры через Python (Pillow) или HTML+Playwright-скриншоты.
3. Easing (ease-in-out), бесшовная петля: последний кадр → первый.
4. Сохраняй с optimize=True и ограниченной палитрой; проверь размер файла.

## Результат

.gif файл и скрипт генерации.

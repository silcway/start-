---
name: mcp-tools
description: Design and build MCP (Model Context Protocol) servers and tools. Use when the user asks: сделай MCP сервер, подключи API к Claude, MCP tool, build an MCP server. Отдел: 01 Разработка.
---

# MCP Tools

_Отдел: 01 Разработка_

## Процесс

1. Определи, какие действия/данные нужны модели; сгруппируй в 3–10 инструментов с понятными именами (verb_noun).
2. Выбери SDK: TypeScript (@modelcontextprotocol/sdk) или Python (mcp / FastMCP); транспорт stdio для локального, Streamable HTTP для удалённого.
3. Для каждого инструмента: чёткое описание (когда вызывать), строгая JSON-схема входа, компактный выход, понятные ошибки.
4. Добавь пагинацию и лимиты для больших ответов; секреты только из переменных окружения.
5. Протестируй через MCP Inspector (npx @modelcontextprotocol/inspector).
6. Покажи, как подключить: `claude mcp add <name> -- <command>` или .mcp.json.

## Результат

Код сервера, README с подключением, пример вызова каждого инструмента.

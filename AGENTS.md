# Правила проекта CreditPulse

## Общие правила

- Проект русскоязычный: пользовательские тексты, README и документация пишутся на русском.
- Реальные секреты хранятся только в `.env`; `.env.example` содержит безопасный пример.
- Основной production-запуск: `docker compose up -d --build`.
- Development-запуск: backend и frontend отдельными процессами.
- Версия приложения единая для backend и frontend. Источник правды для UI — `/api/health`.
- SQLite-БД проекта хранится в `data/creditpulse.sqlite3` и намеренно не игнорируется Git: это общий демо-набор клиентов и историй чатов для команды.
- Docker Compose монтирует БД через bind mount `./data:/app/data`; `docker compose down -v` не удаляет этот файл. Для сброса БД нужно явно удалить `data/creditpulse.sqlite3`.
- Перед коммитом изменений данных проверять, что вместе с кодом добавлен актуальный `data/creditpulse.sqlite3`, если менялись клиенты или история чатов.

## Backend

- Backend написан на FastAPI.
- API-схемы описываются через Pydantic в `app/schemas.py`.
- Доступ к SQLite сосредоточен в `app/database.py`; не добавлять альтернативные локальные хранилища клиентов/чатов на frontend.
- LLM-интеграции подключаются через интерфейс `app/llm/base.py` и фабрику `app/llm/factory.py`.
- Скоринг пока находится в `app/scoring.py`; при замене модели нужно сохранить контракт ответа для frontend.
- Перед сдачей backend-изменений запускать:

```bash
python -m compileall app
```

## Frontend

- Frontend написан на Vue 3 + TypeScript + Vite.
- Основной UI kit: Element Plus.
- Используется Vue Router; `App.vue` должен оставаться легким и содержать только `router-view`.
- Общие компоненты размещаются в `frontend/src/components`.
- Страницы размещаются в `frontend/src/pages`.
- Компоненты, уникальные для страницы, размещаются рядом со страницей в `frontend/src/pages/<page>/components`.
- API-клиент генерируется Orval в `frontend/src/api/generated/creditpulse.ts`.
- `frontend/src/styles.scss` содержит только глобальные правила, базовые CSS-переменные и общие утилиты.
- Стили конкретных страниц и компонентов пишутся внутри Vue-файлов через `<style scoped lang="scss">`.
- Стили пишутся в SCSS-синтаксисе.
- В стилях преимущественно используются переменные Element Plus: `var(--el-color-*)`, `var(--el-bg-color*)`, `var(--el-text-color*)`, `var(--el-border-color*)`.
- Обычные HEX/RGB цвета допускаются только при необходимости и точечно.
- Темная тема поддерживается через класс `dark` на `document.documentElement` и Element Plus dark css vars.
- Приложение ведет себя как SPA: глобальный скролл страницы выключен, скролл включается только внутри областей с переполнением, например чат, список клиентов или список карточек.
- Перед сдачей frontend-изменений запускать:

```bash
cd frontend
npm run typecheck
npm run lint
```

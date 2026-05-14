# CreditPulse

CreditPulse — прототип интеллектуальной системы поддержки принятия решений для оценки кредитоспособности заемщика.

Текущая версия приложения: `0.4.0`.

Проект состоит из двух контейнеров:

- `backend`: FastAPI API, базовый скоринг, интеграция с LLM-провайдером.
- `frontend`: Vue 3 + TypeScript приложение, собранное Vite и раздаваемое через nginx.

Основные разделы интерфейса:

- `Ассистент` — чат с LLM по выбранной карточке заемщика.
- `Клиентская база` — локальный справочник клиентов с добавлением, редактированием и удалением.
- `Настройки` — версия приложения, LLM-провайдер, интеграции и переключатель светлой/темной темы.

## Демо

![Интерфейс CreditPulse](demo.png)

## Продакшен-запуск

Перед первым запуском создайте `.env` на основе `.env.example`:

```powershell
Copy-Item .env.example .env
```

`.env.example` — это только пример. Реальные ключи, например `YANDEX_API_KEY`, нужно хранить в `.env`.

Запуск:

```bash
docker compose up -d --build
```

Открыть приложение:

```text
http://127.0.0.1:8000
```

Полезные адреса:

```text
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/openapi.json
```

## Переменные окружения

Пример `.env` для реального Yandex-провайдера:

```text
CREDITPULSE_LLM_PROVIDER=yandex
YANDEX_API_KEY=<real_key>
YANDEX_BASE_URL=https://ai.api.cloud.yandex.net/v1
YANDEX_PROJECT=b1gea2upudrrrnph3fj4
YANDEX_PROMPT_ID=fvtf6nig20k1irru1ffs
```

Для локального режима без внешнего API:

```text
CREDITPULSE_LLM_PROVIDER=mock
```

Docker Compose сначала читает `.env.example`, затем опциональный `.env`, поэтому значения из `.env` переопределяют шаблон.

## Режим разработки

В разработке удобнее запускать backend и frontend отдельными процессами.

### Backend

Создать виртуальное окружение:

```bash
python -m venv .venv
```

Активировать окружение в PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Установить Python-зависимости:

```bash
pip install -r requirements.txt
```

Создать `.env`, если он еще не создан:

```powershell
Copy-Item .env.example .env
```

Заполнить `.env` реальными значениями или включить локальный мок:

```text
CREDITPULSE_LLM_PROVIDER=mock
```

Запустить backend:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

Установить npm-зависимости:

```bash
cd frontend
npm install
```

Запустить Vite dev server:

```bash
npm run dev
```

Открыть frontend:

```text
http://127.0.0.1:5173
```

Vite проксирует `/api`, `/docs` и `/openapi.json` на `http://127.0.0.1:8000`.

## Генерация API-клиента

Orval генерирует TypeScript-клиент из OpenAPI-схемы FastAPI:

```text
http://127.0.0.1:8000/openapi.json
```

Перед генерацией должен быть запущен backend.

```bash
cd frontend
npm run generate
```

Сгенерированный клиент лежит в одном файле:

```text
frontend/src/api/generated/creditpulse.ts
```

## Проверки

Frontend:

```bash
cd frontend
npm run typecheck
npm run lint
npm run build:docker
```

Backend:

```bash
python -m compileall app
```

Проверка Docker Compose:

```bash
docker compose config --services
```

## API

`GET /api/health` — статус backend, активный LLM-провайдер и версия приложения.

`GET /api/borrowers` — список карточек заемщиков.

`GET /api/borrowers/{borrower_id}` — карточка одного заемщика.

`POST /api/analyze` — расчет скоринга и генерация объяснения через LLM.

Пример запроса:

```json
{
  "borrowerId": "anna",
  "question": "Оцени заявку и объясни рекомендацию."
}
```

Backend также принимает старый формат с полной карточкой `borrower` для обратной совместимости.

## Архитектура

- `app/main.py` — FastAPI-приложение и HTTP endpoints.
- `app/schemas.py` — Pydantic-схемы API.
- `app/data.py` — демонстрационные заемщики и display-поля.
- `app/scoring.py` — базовый модуль скоринга.
- `app/llm/base.py` — общий интерфейс LLM-провайдера.
- `app/llm/mock_provider.py` — локальный мок без внешнего API.
- `app/llm/yandex_provider.py` — интеграция с Yandex Cloud AI через OpenAI-compatible API.
- `frontend/src/App.vue` — легкая точка входа с `router-view`.
- `frontend/src/router` — маршруты приложения.
- `frontend/src/components` — общие компоненты.
- `frontend/src/pages` — страницы и уникальные для них компоненты.
- `frontend/src/styles.scss` — только глобальные стили и общие переменные.
- `frontend/nginx.conf` — nginx-прокси для frontend и backend API.

## Ограничения прототипа

- История чатов хранится только в памяти frontend и сбрасывается при перезагрузке страницы.
- Скоринг пока является детерминированной демонстрационной эвристикой.
- Демо-заемщики пока хранятся в коде.
- Изменения на странице `Клиентская база` пока локальные и не сохраняются на backend.
- LLM-модуль заменяемый: новый провайдер можно подключить через `app/llm/base.py` и `app/llm/factory.py`.

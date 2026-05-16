# CreditPulse

CreditPulse — прототип интеллектуальной системы поддержки принятия решений для оценки кредитоспособности заемщика.

Текущая версия приложения: `0.4.0`.

Проект состоит из двух контейнеров:

- `backend`: FastAPI API, базовый скоринг, classic ML-модель и интеграция с LLM-провайдером.
- `frontend`: Vue 3 + TypeScript приложение, собранное Vite и раздаваемое через nginx.

Основные разделы интерфейса:

- `Ассистент` — чат по выбранной карточке заемщика со сравнением classic ML и LLM-оценки.
- `Клиентская база` — справочник клиентов с добавлением, редактированием и удалением через backend и SQLite.
- `Настройки` — версия приложения, LLM-провайдер, интеграции и переключатель светлой/темной темы.

ML-часть использует ансамбль `RandomForestClassifier` и `GradientBoostingClassifier`.
Модель обучается на синтетической выборке заемщиков и возвращает вероятность дефолта,
класс заемщика, рекомендацию и ключевые факторы. LLM используется как второе мнение:
она формирует независимую оценку риска и короткое объяснение расхождения или совпадения
с classic ML.

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

## Хранение данных

Клиенты и истории чатов хранятся в SQLite-файле:

```text
data/creditpulse.sqlite3
```

Этот файл намеренно находится в рабочем каталоге и не игнорируется Git. Если вы добавили, отредактировали или удалили клиентов через приложение, изменения попадают в `data/creditpulse.sqlite3`; после `git add` и коммита другие участники получат эти данные через `git pull`.

Docker Compose использует bind mount:

```yaml
./data:/app/data
```

Поэтому `docker compose down -v` не удаляет БД. Для полного сброса локальных данных удалите файл вручную:

```powershell
Remove-Item .\data\creditpulse.sqlite3
```

При следующем запуске backend создаст БД заново и заполнит ее начальными демо-клиентами, если файла еще нет.

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

`POST /api/analyze` — расчет базового скоринга, classic ML-прогноза, LLM-оценки и сравнения результатов.

Пример запроса:

```json
{
  "borrowerId": "anna",
  "question": "Оцени заявку и объясни рекомендацию."
}
```

Backend также принимает старый формат с полной карточкой `borrower` для обратной совместимости.

В ответе сохраняется старое поле `result`, а также добавляются:

- `mlResult` — прогноз classic ML-модели.
- `aiAssessment` — независимая LLM-оценка риска.
- `comparison` — совпадение или расхождение рекомендаций.

## Архитектура

- `app/main.py` — FastAPI-приложение и HTTP endpoints.
- `app/schemas.py` — Pydantic-схемы API.
- `app/database.py` — SQLite-хранилище клиентов и историй чатов.
- `app/data.py` — демонстрационные заемщики и display-поля.
- `app/scoring.py` — базовый модуль скоринга.
- `app/ml/classic_model.py` — classic ML-ансамбль Random Forest + Gradient Boosting.
- `app/comparison.py` — сравнение прогноза ML и LLM-оценки.
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

- `result` остается детерминированной демонстрационной эвристикой для обратной совместимости.
- Classic ML обучается на синтетических данных и не заменяет промышленную кредитную модель.
- SQLite-БД является общим демо-файлом проекта; при параллельном редактировании данных возможны Git-конфликты бинарного файла.
- LLM-модуль заменяемый: новый провайдер можно подключить через `app/llm/base.py` и `app/llm/factory.py`.

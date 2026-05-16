import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv(".env")
load_dotenv(".env.example", override=False)


@dataclass(frozen=True)
class Settings:
    llm_provider: str = os.getenv("CREDITPULSE_LLM_PROVIDER", "yandex")
    database_path: str = os.getenv("CREDITPULSE_DATABASE_PATH", "data/creditpulse.sqlite3")
    yandex_api_key: str = os.getenv("YANDEX_API_KEY", "")
    yandex_base_url: str = os.getenv(
        "YANDEX_BASE_URL", "https://ai.api.cloud.yandex.net/v1"
    )
    yandex_project: str = os.getenv("YANDEX_PROJECT", "b1gea2upudrrrnph3fj4")
    yandex_prompt_id: str = os.getenv("YANDEX_PROMPT_ID", "fvtf6nig20k1irru1ffs")


settings = Settings()

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from app.config import settings
from app.schemas import Borrower, BorrowerCreate, ChatMessage


def _connect() -> sqlite3.Connection:
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database(seed_borrowers: Iterable[Borrower]) -> None:
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS borrowers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                income REAL NOT NULL,
                employment_years REAL NOT NULL,
                employment_type TEXT NOT NULL,
                housing_type TEXT NOT NULL,
                loan_amount REAL NOT NULL,
                loan_term_months INTEGER NOT NULL,
                interest_rate REAL NOT NULL,
                loan_purpose TEXT NOT NULL,
                credit_history TEXT NOT NULL,
                past_defaults INTEGER NOT NULL,
                debt_load REAL NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                borrower_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'agent')),
                text TEXT NOT NULL,
                result_json TEXT,
                ml_result_json TEXT,
                ai_assessment_json TEXT,
                comparison_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (borrower_id) REFERENCES borrowers(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_chat_messages_borrower_created
                ON chat_messages (borrower_id, created_at);

            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        existing_count = connection.execute("SELECT COUNT(*) FROM borrowers").fetchone()[0]
        seed_done = connection.execute(
            "SELECT value FROM app_meta WHERE key = 'borrowers_seeded'"
        ).fetchone()
        if existing_count == 0 and seed_done is None:
            now = _now()
            connection.executemany(
                """
                INSERT INTO borrowers (
                    id, name, age, income, employment_years, employment_type, housing_type,
                    loan_amount, loan_term_months, interest_rate, loan_purpose, credit_history,
                    past_defaults, debt_load, created_at, updated_at
                )
                VALUES (
                    :id, :name, :age, :income, :employment_years, :employment_type, :housing_type,
                    :loan_amount, :loan_term_months, :interest_rate, :loan_purpose, :credit_history,
                    :past_defaults, :debt_load, :created_at, :updated_at
                )
                """,
                [_borrower_params(borrower, now) for borrower in seed_borrowers],
            )
        if seed_done is None:
            connection.execute(
                "INSERT INTO app_meta (key, value) VALUES ('borrowers_seeded', '1')"
            )


def list_borrowers() -> list[Borrower]:
    with _connect() as connection:
        rows = connection.execute("SELECT * FROM borrowers ORDER BY created_at DESC, name").fetchall()
    return [_row_to_borrower(row) for row in rows]


def get_borrower(borrower_id: str) -> Borrower | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM borrowers WHERE id = ?",
            (borrower_id,),
        ).fetchone()
    return _row_to_borrower(row) if row else None


def create_borrower(payload: BorrowerCreate) -> Borrower:
    borrower = _payload_to_borrower(payload)
    now = _now()
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO borrowers (
                id, name, age, income, employment_years, employment_type, housing_type,
                loan_amount, loan_term_months, interest_rate, loan_purpose, credit_history,
                past_defaults, debt_load, created_at, updated_at
            )
            VALUES (
                :id, :name, :age, :income, :employment_years, :employment_type, :housing_type,
                :loan_amount, :loan_term_months, :interest_rate, :loan_purpose, :credit_history,
                :past_defaults, :debt_load, :created_at, :updated_at
            )
            """,
            _borrower_params(borrower, now),
        )
    return borrower


def update_borrower(borrower_id: str, payload: BorrowerCreate) -> Borrower | None:
    borrower = _payload_to_borrower(payload, borrower_id)
    with _connect() as connection:
        cursor = connection.execute(
            """
            UPDATE borrowers
            SET name = :name,
                age = :age,
                income = :income,
                employment_years = :employment_years,
                employment_type = :employment_type,
                housing_type = :housing_type,
                loan_amount = :loan_amount,
                loan_term_months = :loan_term_months,
                interest_rate = :interest_rate,
                loan_purpose = :loan_purpose,
                credit_history = :credit_history,
                past_defaults = :past_defaults,
                debt_load = :debt_load,
                updated_at = :updated_at
            WHERE id = :id
            """,
            _borrower_params(borrower, _now()),
        )
    return borrower if cursor.rowcount else None


def delete_borrower(borrower_id: str) -> bool:
    with _connect() as connection:
        cursor = connection.execute("DELETE FROM borrowers WHERE id = ?", (borrower_id,))
    return cursor.rowcount > 0


def list_chat_messages(borrower_id: str) -> list[ChatMessage]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT * FROM chat_messages
            WHERE borrower_id = ?
            ORDER BY created_at, rowid
            """,
            (borrower_id,),
        ).fetchall()
    return [_row_to_chat_message(row) for row in rows]


def add_chat_message(
    borrower_id: str,
    role: str,
    text: str,
    *,
    result: Any | None = None,
    ml_result: Any | None = None,
    ai_assessment: Any | None = None,
    comparison: Any | None = None,
) -> ChatMessage:
    message_id = str(uuid.uuid4())
    created_at = _now()
    params = {
        "id": message_id,
        "borrower_id": borrower_id,
        "role": role,
        "text": text,
        "result_json": _dump_json(result),
        "ml_result_json": _dump_json(ml_result),
        "ai_assessment_json": _dump_json(ai_assessment),
        "comparison_json": _dump_json(comparison),
        "created_at": created_at,
    }
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO chat_messages (
                id, borrower_id, role, text, result_json, ml_result_json,
                ai_assessment_json, comparison_json, created_at
            )
            VALUES (
                :id, :borrower_id, :role, :text, :result_json, :ml_result_json,
                :ai_assessment_json, :comparison_json, :created_at
            )
            """,
            params,
        )
    return ChatMessage(
        id=message_id,
        borrowerId=borrower_id,
        role=role,
        text=text,
        result=result,
        mlResult=ml_result,
        aiAssessment=ai_assessment,
        comparison=comparison,
        createdAt=created_at,
    )


def clear_chat_messages(borrower_id: str) -> None:
    with _connect() as connection:
        connection.execute("DELETE FROM chat_messages WHERE borrower_id = ?", (borrower_id,))


def _payload_to_borrower(payload: BorrowerCreate, borrower_id: str | None = None) -> Borrower:
    return Borrower(
        **{
            **payload.model_dump(by_alias=True),
            "id": borrower_id or payload.id or str(uuid.uuid4()),
        }
    )


def _borrower_params(borrower: Borrower, timestamp: str) -> dict[str, Any]:
    return {
        "id": borrower.id,
        "name": borrower.name,
        "age": borrower.age,
        "income": borrower.income,
        "employment_years": borrower.employment_years,
        "employment_type": borrower.employment_type,
        "housing_type": borrower.housing_type,
        "loan_amount": borrower.loan_amount,
        "loan_term_months": borrower.loan_term_months,
        "interest_rate": borrower.interest_rate,
        "loan_purpose": borrower.loan_purpose,
        "credit_history": borrower.credit_history,
        "past_defaults": int(borrower.past_defaults),
        "debt_load": borrower.debt_load,
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def _row_to_borrower(row: sqlite3.Row) -> Borrower:
    return Borrower(
        id=row["id"],
        name=row["name"],
        age=row["age"],
        income=row["income"],
        employmentYears=row["employment_years"],
        employmentType=row["employment_type"],
        housingType=row["housing_type"],
        loanAmount=row["loan_amount"],
        loanTermMonths=row["loan_term_months"],
        interestRate=row["interest_rate"],
        loanPurpose=row["loan_purpose"],
        creditHistory=row["credit_history"],
        pastDefaults=bool(row["past_defaults"]),
        debtLoad=row["debt_load"],
    )


def _row_to_chat_message(row: sqlite3.Row) -> ChatMessage:
    return ChatMessage(
        id=row["id"],
        borrowerId=row["borrower_id"],
        role=row["role"],
        text=row["text"],
        result=_load_json(row["result_json"]),
        mlResult=_load_json(row["ml_result_json"]),
        aiAssessment=_load_json(row["ai_assessment_json"]),
        comparison=_load_json(row["comparison_json"]),
        createdAt=row["created_at"],
    )


def _dump_json(value: Any | None) -> str | None:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        value = value.model_dump(by_alias=True)
    return json.dumps(value, ensure_ascii=False)


def _load_json(value: str | None) -> Any | None:
    return json.loads(value) if value else None


def _now() -> str:
    return datetime.now(UTC).isoformat()

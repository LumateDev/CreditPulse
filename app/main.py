from __future__ import annotations

from contextlib import asynccontextmanager
from sqlite3 import IntegrityError
from typing import Any

from fastapi import FastAPI, HTTPException, Response

from app.config import settings
from app.comparison import compare_predictions
from app.data import DEMO_BORROWERS, to_card
from app.database import (
    add_chat_message,
    clear_chat_messages,
    create_borrower,
    delete_borrower,
    get_borrower,
    init_database,
    list_borrowers,
    list_chat_messages,
    update_borrower,
)
from app.llm import build_llm_provider
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    BorrowerCard,
    BorrowerCreate,
    ChatMessage,
    HealthResponse,
)
from app.ml import score_with_classic_ml
from app.scoring import score_borrower
from app.version import APP_VERSION


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database(DEMO_BORROWERS)
    yield


app = FastAPI(
    title="CreditPulse API",
    description="Prototype DSS for borrower scoring and LLM explanations.",
    version=APP_VERSION,
    lifespan=lifespan,
)


@app.get(
    "/api/health",
    response_model=HealthResponse,
    response_model_by_alias=True,
    operation_id="getHealth",
)
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "llmProvider": settings.llm_provider,
        "version": APP_VERSION,
    }


@app.get(
    "/api/borrowers",
    response_model=list[BorrowerCard],
    response_model_by_alias=True,
    operation_id="listBorrowers",
)
def borrowers() -> list[BorrowerCard]:
    return [to_card(borrower) for borrower in list_borrowers()]


@app.post(
    "/api/borrowers",
    response_model=BorrowerCard,
    response_model_by_alias=True,
    operation_id="createBorrower",
    status_code=201,
)
def borrower_create(payload: BorrowerCreate) -> BorrowerCard:
    try:
        borrower = create_borrower(payload)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Borrower already exists") from exc
    return to_card(borrower)


@app.get(
    "/api/borrowers/{borrower_id}",
    response_model=BorrowerCard,
    response_model_by_alias=True,
    operation_id="getBorrower",
)
def borrower_details(borrower_id: str) -> BorrowerCard:
    borrower = get_borrower(borrower_id)
    if borrower is None:
        raise HTTPException(status_code=404, detail="Borrower not found")
    return to_card(borrower)


@app.put(
    "/api/borrowers/{borrower_id}",
    response_model=BorrowerCard,
    response_model_by_alias=True,
    operation_id="updateBorrower",
)
def borrower_update(borrower_id: str, payload: BorrowerCreate) -> BorrowerCard:
    borrower = update_borrower(borrower_id, payload)
    if borrower is None:
        raise HTTPException(status_code=404, detail="Borrower not found")
    return to_card(borrower)


@app.delete(
    "/api/borrowers/{borrower_id}",
    status_code=204,
    operation_id="deleteBorrower",
)
def borrower_delete(borrower_id: str) -> Response:
    if not delete_borrower(borrower_id):
        raise HTTPException(status_code=404, detail="Borrower not found")
    return Response(status_code=204)


@app.get(
    "/api/borrowers/{borrower_id}/chat",
    response_model=list[ChatMessage],
    response_model_by_alias=True,
    operation_id="listChatMessages",
)
def chat_messages(borrower_id: str) -> list[ChatMessage]:
    if get_borrower(borrower_id) is None:
        raise HTTPException(status_code=404, detail="Borrower not found")
    return list_chat_messages(borrower_id)


@app.delete(
    "/api/borrowers/{borrower_id}/chat",
    status_code=204,
    operation_id="clearChatMessages",
)
def chat_clear(borrower_id: str) -> Response:
    if get_borrower(borrower_id) is None:
        raise HTTPException(status_code=404, detail="Borrower not found")
    clear_chat_messages(borrower_id)
    return Response(status_code=204)


@app.post(
    "/api/analyze",
    response_model=AnalyzeResponse,
    response_model_by_alias=True,
    operation_id="analyzeBorrower",
)
def analyze(payload: AnalyzeRequest) -> dict[str, Any]:
    borrower = get_borrower(payload.borrower_id) if payload.borrower_id else payload.borrower
    if borrower is None:
        raise HTTPException(status_code=404, detail="Borrower not found")

    result = score_borrower(borrower)
    borrower_payload = borrower.model_dump(by_alias=True)
    try:
        ml_result = score_with_classic_ml(borrower)
        provider = build_llm_provider()
        llm_payload = {
            "borrower": borrower_payload,
            "result": result,
            "mlResult": ml_result,
            "question": payload.question,
        }
        ai_assessment = provider.assess(llm_payload)
        comparison = compare_predictions(ml_result, ai_assessment)
        explanation = provider.explain(
            {
                **llm_payload,
                "aiAssessment": ai_assessment,
                "comparison": comparison,
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Analysis provider error: {exc}",
        ) from exc

    if payload.borrower_id:
        add_chat_message(payload.borrower_id, "user", payload.question)
        add_chat_message(
            payload.borrower_id,
            "agent",
            explanation,
            result=result,
            ml_result=ml_result,
            ai_assessment=ai_assessment,
            comparison=comparison,
        )

    return {
        "borrower": to_card(borrower),
        "result": result,
        "mlResult": ml_result,
        "aiAssessment": ai_assessment,
        "comparison": comparison,
        "explanation": explanation,
    }

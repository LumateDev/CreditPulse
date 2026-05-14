from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from app.config import settings
from app.comparison import compare_predictions
from app.data import get_borrower, list_borrower_cards, to_card
from app.llm import build_llm_provider
from app.schemas import AnalyzeRequest, AnalyzeResponse, BorrowerCard, HealthResponse
from app.ml import score_with_classic_ml
from app.scoring import score_borrower

APP_VERSION = "0.4.0"

app = FastAPI(
    title="CreditPulse API",
    description="Prototype DSS for borrower scoring and LLM explanations.",
    version=APP_VERSION,
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
    return list_borrower_cards()


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

    return {
        "borrower": to_card(borrower),
        "result": result,
        "mlResult": ml_result,
        "aiAssessment": ai_assessment,
        "comparison": comparison,
        "explanation": explanation,
    }

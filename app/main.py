from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from app.config import settings
from app.data import get_borrower, list_borrower_cards, to_card
from app.llm import build_llm_provider
from app.schemas import AnalyzeRequest, AnalyzeResponse, BorrowerCard
from app.scoring import score_borrower

app = FastAPI(
    title="CreditPulse API",
    description="Prototype DSS for borrower scoring and LLM explanations.",
    version="0.3.0",
)


@app.get("/api/health", operation_id="getHealth")
def health() -> dict[str, str]:
    return {"status": "ok", "llmProvider": settings.llm_provider}


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
        explanation = build_llm_provider().explain(
            {
                "borrower": borrower_payload,
                "result": result,
                "question": payload.question,
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM provider error: {exc}",
        ) from exc

    return {"borrower": to_card(borrower), "result": result, "explanation": explanation}

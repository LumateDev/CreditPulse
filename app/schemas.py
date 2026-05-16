from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Borrower(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    age: int
    income: float
    employment_years: float = Field(alias="employmentYears")
    employment_type: str = Field(alias="employmentType")
    housing_type: str = Field(alias="housingType")
    loan_amount: float = Field(alias="loanAmount")
    loan_term_months: int = Field(alias="loanTermMonths")
    interest_rate: float = Field(alias="interestRate")
    loan_purpose: str = Field(alias="loanPurpose")
    credit_history: str = Field(alias="creditHistory")
    past_defaults: bool = Field(alias="pastDefaults")
    debt_load: float = Field(alias="debtLoad")


class BorrowerDisplay(BaseModel):
    employment_type: str = Field(alias="employmentType")
    housing_type: str = Field(alias="housingType")
    credit_history: str = Field(alias="creditHistory")
    income: str
    loan_amount: str = Field(alias="loanAmount")
    debt_load: str = Field(alias="debtLoad")
    loan_term: str = Field(alias="loanTerm")


class BorrowerCard(Borrower):
    display: BorrowerDisplay


class BorrowerCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    name: str
    age: int
    income: float
    employment_years: float = Field(alias="employmentYears")
    employment_type: str = Field(alias="employmentType")
    housing_type: str = Field(alias="housingType")
    loan_amount: float = Field(alias="loanAmount")
    loan_term_months: int = Field(alias="loanTermMonths")
    interest_rate: float = Field(alias="interestRate")
    loan_purpose: str = Field(alias="loanPurpose")
    credit_history: str = Field(alias="creditHistory")
    past_defaults: bool = Field(alias="pastDefaults")
    debt_load: float = Field(alias="debtLoad")


class Factor(BaseModel):
    name: str
    sign: Literal["+", "-"]
    impact: float


class LoanMetrics(BaseModel):
    monthly_payment: float = Field(alias="monthlyPayment")
    payment_to_income: float = Field(alias="paymentToIncome")
    term_assessment: str = Field(alias="termAssessment")


class ScoringResult(BaseModel):
    default_probability: float = Field(alias="defaultProbability")
    borrower_class: Literal["good", "bad"] = Field(alias="borrowerClass")
    recommendation: str
    factors: list[Factor]
    loan_metrics: LoanMetrics = Field(alias="loanMetrics")


class AiAssessment(BaseModel):
    default_probability: float = Field(alias="defaultProbability")
    borrower_class: Literal["good", "bad"] = Field(alias="borrowerClass")
    recommendation: str
    risk_level: Literal["low", "medium", "high"] = Field(alias="riskLevel")
    confidence: float
    reasoning_summary: str = Field(alias="reasoningSummary")


class PredictionComparison(BaseModel):
    agreement: bool
    probability_gap: float = Field(alias="probabilityGap")
    summary: str


class ChatMessage(BaseModel):
    id: str
    borrower_id: str = Field(alias="borrowerId")
    role: Literal["user", "agent"]
    text: str
    result: ScoringResult | None = None
    ml_result: ScoringResult | None = Field(default=None, alias="mlResult")
    ai_assessment: AiAssessment | None = Field(default=None, alias="aiAssessment")
    comparison: PredictionComparison | None = None
    created_at: str = Field(alias="createdAt")


class AnalyzeRequest(BaseModel):
    borrower_id: str | None = Field(default=None, alias="borrowerId")
    borrower: Borrower | None = None
    question: str = "Оцени заявку и объясни рекомендацию."


class AnalyzeResponse(BaseModel):
    borrower: BorrowerCard
    result: ScoringResult
    ml_result: ScoringResult = Field(alias="mlResult")
    ai_assessment: AiAssessment = Field(alias="aiAssessment")
    comparison: PredictionComparison
    explanation: str


class HealthResponse(BaseModel):
    status: str
    llm_provider: str = Field(alias="llmProvider")
    version: str

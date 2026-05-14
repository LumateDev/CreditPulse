from __future__ import annotations

from app.schemas import Borrower, BorrowerCard, BorrowerDisplay


EMPLOYMENT_LABELS = {
    "full_time": "постоянная",
    "self_employed": "самозанятость",
    "temporary": "временная",
    "unemployed": "без работы",
}

HOUSING_LABELS = {
    "own": "собственное",
    "rent": "аренда",
    "mortgage": "ипотека",
}

CREDIT_HISTORY_LABELS = {
    "excellent": "отличная",
    "good": "хорошая",
    "late_payments": "просрочки",
    "poor": "слабая",
}

DEMO_BORROWERS = [
    Borrower(
        id="anna",
        name="Анна Смирнова",
        age=32,
        income=95000,
        employmentYears=6,
        employmentType="full_time",
        housingType="own",
        loanAmount=620000,
        loanTermMonths=24,
        interestRate=13.5,
        loanPurpose="ремонт",
        creditHistory="good",
        pastDefaults=False,
        debtLoad=0.24,
    ),
    Borrower(
        id="maksim",
        name="Максим Орлов",
        age=28,
        income=35000,
        employmentYears=1,
        employmentType="self_employed",
        housingType="rent",
        loanAmount=520000,
        loanTermMonths=36,
        interestRate=18.0,
        loanPurpose="потребительский кредит",
        creditHistory="late_payments",
        pastDefaults=False,
        debtLoad=0.51,
    ),
    Borrower(
        id="elena",
        name="Елена Кузнецова",
        age=45,
        income=140000,
        employmentYears=11,
        employmentType="full_time",
        housingType="mortgage",
        loanAmount=1800000,
        loanTermMonths=60,
        interestRate=12.2,
        loanPurpose="автомобиль",
        creditHistory="excellent",
        pastDefaults=False,
        debtLoad=0.32,
    ),
    Borrower(
        id="timur",
        name="Тимур Ахметов",
        age=23,
        income=48000,
        employmentYears=0.5,
        employmentType="temporary",
        housingType="rent",
        loanAmount=780000,
        loanTermMonths=48,
        interestRate=21.0,
        loanPurpose="техника",
        creditHistory="poor",
        pastDefaults=True,
        debtLoad=0.64,
    ),
]


def format_money(value: float) -> str:
    return f"{value:,.0f} ₽".replace(",", " ")


def format_percent(value: float) -> str:
    return f"{round(value * 100)}%"


def get_borrower(borrower_id: str) -> Borrower | None:
    return next((borrower for borrower in DEMO_BORROWERS if borrower.id == borrower_id), None)


def to_card(borrower: Borrower) -> BorrowerCard:
    return BorrowerCard(
        **borrower.model_dump(by_alias=True),
        display=BorrowerDisplay(
            employmentType=EMPLOYMENT_LABELS.get(borrower.employment_type, borrower.employment_type),
            housingType=HOUSING_LABELS.get(borrower.housing_type, borrower.housing_type),
            creditHistory=CREDIT_HISTORY_LABELS.get(
                borrower.credit_history, borrower.credit_history
            ),
            income=format_money(borrower.income),
            loanAmount=format_money(borrower.loan_amount),
            debtLoad=format_percent(borrower.debt_load),
            loanTerm=f"{borrower.loan_term_months} мес.",
        ),
    )


def list_borrower_cards() -> list[BorrowerCard]:
    return [to_card(borrower) for borrower in DEMO_BORROWERS]

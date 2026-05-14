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

FINAL_CHECK_BORROWERS = [
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

FIRST_NAMES = [
    "Алексей",
    "Мария",
    "Иван",
    "Ольга",
    "Дмитрий",
    "Наталья",
    "Сергей",
    "Юлия",
    "Павел",
    "Ирина",
    "Виктор",
    "Алина",
    "Роман",
    "Екатерина",
    "Георгий",
    "Ксения",
]

LAST_NAMES = [
    "Иванов",
    "Петрова",
    "Соколов",
    "Морозова",
    "Волков",
    "Новикова",
    "Федоров",
    "Орлова",
    "Михайлов",
    "Зайцева",
    "Павлов",
    "Беляева",
    "Козлов",
    "Семенова",
    "Громов",
    "Лебедева",
]

EMPLOYMENT_TYPES = ["full_time", "self_employed", "temporary", "unemployed"]
HOUSING_TYPES = ["own", "rent", "mortgage"]
CREDIT_HISTORIES = ["excellent", "good", "late_payments", "poor"]
LOAN_PURPOSES = [
    "ремонт",
    "автомобиль",
    "потребительский кредит",
    "образование",
    "техника",
    "медицина",
    "путешествие",
    "рефинансирование",
]
TERMS = [12, 18, 24, 36, 48, 60, 72]


def _synthetic_borrower(index: int) -> Borrower:
    employment_type = EMPLOYMENT_TYPES[(index * 7 + index // 5) % len(EMPLOYMENT_TYPES)]
    housing_type = HOUSING_TYPES[(index * 5 + index // 11) % len(HOUSING_TYPES)]
    credit_history = CREDIT_HISTORIES[(index * 3 + index // 13) % len(CREDIT_HISTORIES)]
    loan_term = TERMS[(index * 5 + index // 9) % len(TERMS)]

    age = 21 + ((index * 17 + index // 3) % 43)
    income = 32000 + ((index * 11700 + (index % 9) * 4300) % 178000)
    employment_years = round(((index * 9) % 180) / 12, 1)
    if employment_type == "unemployed":
        employment_years = round(((index * 2) % 10) / 12, 1)
    elif employment_type == "full_time":
        employment_years = max(1.2, employment_years)

    debt_load = round(0.12 + ((index * 37 + index // 4) % 66) / 100, 2)
    if credit_history in {"late_payments", "poor"}:
        debt_load = min(0.82, round(debt_load + 0.06, 2))
    if credit_history == "excellent":
        debt_load = max(0.08, round(debt_load - 0.05, 2))

    loan_multiplier = 4.5 + ((index * 19 + index // 7) % 125) / 10
    loan_amount = round(income * loan_multiplier / 10000) * 10000
    interest_rate = round(9.5 + ((index * 23 + index // 6) % 145) / 10, 1)
    if credit_history == "excellent":
        interest_rate = max(8.5, round(interest_rate - 2.0, 1))
    elif credit_history == "poor":
        interest_rate = min(27.5, round(interest_rate + 2.8, 1))

    past_defaults = credit_history == "poor" and index % 3 == 0
    if credit_history == "late_payments" and index % 17 == 0:
        past_defaults = True

    return Borrower(
        id=f"synthetic-{index:03d}",
        name=f"{FIRST_NAMES[index % len(FIRST_NAMES)]} {LAST_NAMES[(index * 5) % len(LAST_NAMES)]}",
        age=age,
        income=float(income),
        employmentYears=employment_years,
        employmentType=employment_type,
        housingType=housing_type,
        loanAmount=float(max(90000, loan_amount)),
        loanTermMonths=loan_term,
        interestRate=interest_rate,
        loanPurpose=LOAN_PURPOSES[(index * 11) % len(LOAN_PURPOSES)],
        creditHistory=credit_history,
        pastDefaults=past_defaults,
        debtLoad=debt_load,
    )


TRAINING_BORROWERS = [_synthetic_borrower(index) for index in range(1, 241)]
DEMO_BORROWERS = FINAL_CHECK_BORROWERS + TRAINING_BORROWERS


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

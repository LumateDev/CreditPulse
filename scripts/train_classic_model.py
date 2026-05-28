from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from joblib import dump
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

from app.database import list_borrowers
from app.ml.classic_model import (
    MODEL_PATH,
    _borrower_features,
    _fit_model,
    _synthetic_label,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train CreditPulse classic ML model.")
    parser.add_argument(
        "--output",
        default=str(MODEL_PATH),
        help="Path to save the trained joblib model.",
    )
    parser.add_argument(
        "--test-size",
        default=0.2,
        type=float,
        help="Validation split share.",
    )
    args = parser.parse_args()

    borrowers = list_borrowers()
    if not borrowers:
        raise SystemExit("No borrowers found in the database.")

    labels = [_synthetic_label(borrower) for borrower in borrowers]
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        raise SystemExit("Training labels must contain both classes.")

    train_borrowers, test_borrowers, _, y_test = train_test_split(
        borrowers,
        labels,
        test_size=args.test_size,
        random_state=42,
        stratify=labels,
    )

    model = _fit_model(train_borrowers)
    x_test = [_borrower_features(borrower) for borrower in test_borrowers]
    y_proba = model.predict_proba(x_test)[:, 1]
    y_pred = (y_proba >= 0.55).astype(int)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dump(model, output_path)

    print(f"borrowers={len(borrowers)} train={len(train_borrowers)} test={len(test_borrowers)}")
    print(f"labels_good={negatives} labels_bad={positives}")
    print(f"roc_auc={roc_auc_score(y_test, y_proba):.4f}")
    print(classification_report(y_test, y_pred, target_names=["good", "bad"]))
    print(f"saved={output_path}")


if __name__ == "__main__":
    main()

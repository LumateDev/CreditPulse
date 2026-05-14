# Обучение classic ML модели для CreditPulse

Этот документ описывает демонстрационный сценарий обучения classic ML модели:
ансамбль `RandomForestClassifier` + `GradientBoostingClassifier` через soft voting.

## Разделение данных

В `app/data.py` оставлены 4 исходные карточки:

- `anna`
- `maksim`
- `elena`
- `timur`

Они вынесены в `FINAL_CHECK_BORROWERS` и не используются для обучения runtime-модели.
На них удобно делать финальную ручную проверку поведения. Для обучения используется
`TRAINING_BORROWERS`: 240 синтетических заемщиков с разными профилями дохода,
долговой нагрузки, занятости, кредитной истории, срока и суммы кредита.

## Почему модель не должна быстро переобучиться

- 240 примеров не повторяют одну и ту же форму заемщика: признаки варьируются независимо.
- В выборке есть хорошие, пограничные и рискованные профили.
- Random Forest ограничен `max_depth=6` и `min_samples_leaf=6`.
- Gradient Boosting использует небольшую глубину деревьев `max_depth=2`, низкий
  `learning_rate=0.045` и `subsample=0.85`.
- Финальные 4 примера оставлены вне обучения как holdout-check.

Это не заменяет настоящую банковскую выборку, но для прототипа показывает корректную
архитектуру: табличная ML-модель дает вероятность, LLM дает второе мнение и объяснение.

## Пример offline-обучения и сохранения модели

```python
from joblib import dump
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

from app.data import TRAINING_BORROWERS
from app.ml.classic_model import _borrower_features, _synthetic_label

model = VotingClassifier(
    estimators=[
        (
            "random_forest",
            RandomForestClassifier(
                n_estimators=160,
                max_depth=6,
                min_samples_leaf=6,
                class_weight="balanced",
                random_state=42,
            ),
        ),
        (
            "gradient_boosting",
            GradientBoostingClassifier(
                n_estimators=90,
                learning_rate=0.045,
                max_depth=2,
                subsample=0.85,
                random_state=42,
            ),
        ),
    ],
    voting="soft",
    weights=[0.55, 0.45],
)

pipeline = Pipeline(
    steps=[
        ("features", DictVectorizer(sparse=False)),
        ("model", model),
    ]
)

x_train = [_borrower_features(borrower) for borrower in TRAINING_BORROWERS]
y_train = [_synthetic_label(borrower) for borrower in TRAINING_BORROWERS]

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
roc_auc = cross_val_score(pipeline, x_train, y_train, cv=cv, scoring="roc_auc")
print(f"ROC-AUC: {roc_auc.mean():.3f} +/- {roc_auc.std():.3f}")

pipeline.fit(x_train, y_train)
dump(pipeline, "models/creditpulse_ensemble.joblib")
```

## Runtime-интеграция

В текущей версии runtime-модель обучается лениво в памяти при первом вызове
`POST /api/analyze`. Это сделано, чтобы прототип работал без отдельного файла модели.
Позже можно заменить `_build_model()` на загрузку `joblib`-файла из `models/`.

Ответ `/api/analyze` сохраняет старое поле `result`, а рядом добавляет:

- `mlResult` — classic ML prediction
- `aiAssessment` — LLM second opinion
- `comparison` — совпадение или расхождение двух подходов

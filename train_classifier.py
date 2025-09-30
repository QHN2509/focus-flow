import os
import json
import sqlite3
import joblib
import datetime
import numpy as np
import pandas as pd
import matplotlib
# Use a non-interactive backend for environments without a display
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay

DB_NAME = "productivity_agent.db"
ROOT_MODEL_NAME = "classifier_model.joblib"  # legacy location (overwritten with latest)
ARTIFACT_DIR = "artifacts"


def ensure_artifacts_dir():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)


def evaluate_and_save(model, X_val, y_val, labels, out_dir=ARTIFACT_DIR):
    """Save classification report (txt + json) and confusion matrix PNG."""
    ensure_artifacts_dir()
    y_pred = model.predict(X_val)

    # Classification report (text + json)
    report_dict = classification_report(y_val, y_pred, labels=labels, output_dict=True, zero_division=0)
    txt_path = os.path.join(out_dir, "classification_report.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(classification_report(y_val, y_pred, labels=labels, zero_division=0))
    json_path = os.path.join(out_dir, "classification_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)

    # Confusion matrix
    cm = confusion_matrix(y_val, y_pred, labels=labels)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    fig, ax = plt.subplots(figsize=(6, 6))
    disp.plot(ax=ax, cmap="Blues", values_format='d')
    plt.title("Confusion Matrix")
    plt.tight_layout()
    cm_path = os.path.join(out_dir, "confusion_matrix.png")
    fig.savefig(cm_path)
    plt.close(fig)

    return txt_path, json_path, cm_path


def cross_validate_and_train(pipeline, X_train, y_train, scoring=None, cv_splits=5, out_dir=ARTIFACT_DIR):
    """Run stratified CV on training set, save summary, then fit pipeline on training set."""
    ensure_artifacts_dir()
    if scoring is None:
        scoring = ["accuracy", "precision_macro", "recall_macro", "f1_macro"]

    skf = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=42)
    cv_results = cross_validate(pipeline, X_train, y_train, cv=skf, scoring=scoring, return_train_score=False)

    # Save CV summary (mean/std for each test score)
    summary = {}
    for k, v in cv_results.items():
        if k.startswith("test_"):
            summary[k] = {
                "mean": float(np.mean(v)),
                "std": float(np.std(v))
            }

    summary_path = os.path.join(out_dir, "cv_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Fit on the training set and return the trained pipeline
    pipeline.fit(X_train, y_train)
    return pipeline, summary_path


def train_model():
    """Loads labeled data, evaluates with CV, saves artifacts and model versions."""
    print("--- Training Classification Model ---")
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM labeled_activities", conn)
    finally:
        conn.close()

    if len(df) < 20:
        print(f"Not enough labeled data to train. You have {len(df)} labels. Please label at least 20 activities using manual_labeler.py.")
        return

    X = df['activity_text']
    y = df['category']

    # Split data for evaluation: hold out 20%
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', max_df=0.9, min_df=2)),
        ('clf', LogisticRegression(random_state=42, multi_class='auto', solver='lbfgs', max_iter=1000))
    ])

    print("Running cross-validated evaluation on training set...")
    pipeline_trained, cv_summary_path = cross_validate_and_train(pipeline, X_train, y_train, cv_splits=5)

    # Evaluate on the held-out test set and save artifacts
    labels = sorted(list(pd.Series(y).unique()))
    print("Evaluating on holdout test set...")
    report_txt, report_json, cm_png = evaluate_and_save(pipeline_trained, X_test, y_test, labels)

    # Fit final model on full dataset and save with timestamped name and a legacy filename
    print("Fitting final model on full dataset and saving artifacts...")
    pipeline.fit(X, y)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    model_filename = f"classifier_model_{ts}.joblib"
    model_path = os.path.join(ARTIFACT_DIR, model_filename)
    joblib.dump(pipeline, model_path)

    # Also write/overwrite legacy model path for backwards compatibility
    joblib.dump(pipeline, ROOT_MODEL_NAME)

    # Write a small metadata file
    # Convert class distribution counts to plain Python ints for JSON serializability
    raw_counts = df['category'].value_counts()
    class_dist = {str(k): int(v) for k, v in raw_counts.items()}

    metadata = {
        "trained_at": ts,
        "n_samples": int(len(df)),
        "class_distribution": class_dist,
        "model_path": model_path,
        "legacy_model": ROOT_MODEL_NAME,
        "cv_summary": cv_summary_path,
        "classification_report": report_txt,
        "confusion_matrix": cm_png
    }
    meta_path = os.path.join(ARTIFACT_DIR, f"metadata_{ts}.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Model saved to: {model_path}")
    print(f"Also saved legacy model to: {ROOT_MODEL_NAME}")
    print(f"Artifacts written to: {ARTIFACT_DIR}")


if __name__ == "__main__":
    train_model()

import joblib
import pandas as pd
import sqlite3
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
from pathlib import Path

DB_NAME = "productivity_agent.db"
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

def retrain():
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM labeled_activities", conn)
    finally:
        conn.close()

    if df.empty:
        print("No labeled data found. Aborting retrain.")
        return

    X = df['activity_text']
    y = df['category']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', max_df=0.9, min_df=1)),
        ('clf', LogisticRegression(random_state=42, max_iter=1000))
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)

    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    model_file = MODEL_DIR / f'classifier_model_{ts}.joblib'
    joblib.dump(pipeline, model_file)

    manifest = {
        'model_file': str(model_file),
        'trained_at': ts,
        'num_labels': len(df),
        'report': report
    }

    manifest_file = MODEL_DIR / f'manifest_{ts}.joblib'
    joblib.dump(manifest, manifest_file)

    # Also save a copy to the default model filename for compatibility
    joblib.dump(pipeline, 'classifier_model.joblib')

    print(f"Retrained and saved model to {model_file}")
    print(f"Saved manifest to {manifest_file}")

if __name__ == '__main__':
    retrain()

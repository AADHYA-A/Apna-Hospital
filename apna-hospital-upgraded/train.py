"""Train the disease classifier and save it with metrics.

Run:  python train.py
Creates models/model.joblib and models/metrics.json
"""
import json, os
import joblib, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

BASE = os.path.dirname(os.path.abspath(__file__))


def train(save=True):
    df = pd.read_csv(os.path.join(BASE, "datasets", "Training.csv"))
    df.columns = [c.strip() for c in df.columns]
    X, y = df.drop(columns="prognosis"), df["prognosis"].str.strip()
    # Honest evaluation: drop exact duplicate rows so CV isn't inflated by repeats
    dd = df.drop_duplicates()
    Xd, yd = dd.drop(columns="prognosis"), dd["prognosis"].str.strip()
    clf = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    acc = float(cross_val_score(clf, Xd, yd, cv=cv).mean())
    clf.fit(X.values, y.values)
    bundle = {"model": clf, "features": list(X.columns), "classes": list(clf.classes_)}
    metrics = {"cv_accuracy": round(acc, 4), "rows": int(len(df)), "unique_rows": int(len(dd)),
               "diseases": int(y.nunique()), "symptoms": int(X.shape[1])}
    if save:
        os.makedirs(os.path.join(BASE, "models"), exist_ok=True)
        joblib.dump(bundle, os.path.join(BASE, "models", "model.joblib"), compress=3)
        json.dump(metrics, open(os.path.join(BASE, "models", "metrics.json"), "w"), indent=2)
    return bundle, metrics


if __name__ == "__main__":
    _, m = train()
    print(m)

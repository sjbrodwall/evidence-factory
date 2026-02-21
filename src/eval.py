import argparse, hashlib, json, os
from datetime import datetime, timezone

import numpy as np
import joblib
from sklearn.metrics import accuracy_score, roc_auc_score


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-dir", default="build")
    ap.add_argument("--out", default="build/eval.json")
    args = ap.parse_args()

    build_dir = args.build_dir
    model_path = os.path.join(build_dir, "model.joblib")
    model = joblib.load(model_path)
    test = np.load(os.path.join(build_dir, "test_set.npz"))
    X, y = test["X"], test["y"]

    proba = model.predict_proba(X)[:, 1]
    pred = (proba >= 0.5).astype(int)

    # Content-addressable link to the model artifact (paths as in evidence pack)
    model_artifact = "model/model.joblib"
    train_meta_artifact = "model/train_meta.json"
    with open(model_path, "rb") as f:
        model_sha256 = hashlib.sha256(f.read()).hexdigest()

    report = {
        "schema_version": "1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "model_artifact": model_artifact,
        "train_meta_artifact": train_meta_artifact,
        "model_sha256": model_sha256,
        "metrics": {
            "accuracy": float(accuracy_score(y, pred)),
            "roc_auc": float(roc_auc_score(y, proba)),
        },
        "n_test": int(len(y)),
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
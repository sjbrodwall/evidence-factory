import argparse, json, os, platform, subprocess, sys
from datetime import datetime, timezone

import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="build")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    rng = np.random.default_rng(args.seed)

    X, y = make_classification(
        n_samples=2000,
        n_features=20,
        n_informative=6,
        n_redundant=2,
        n_classes=2,
        random_state=args.seed,
    )

    # deterministic split
    idx = np.arange(X.shape[0])
    rng.shuffle(idx)
    split = int(0.8 * len(idx))
    tr, te = idx[:split], idx[split:]
    X_train, y_train = X[tr], y[tr]
    X_test, y_test = X[te], y[te]

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=args.seed)),
        ]
    )
    model.fit(X_train, y_train)

    model_path = os.path.join(args.out_dir, "model.joblib")
    joblib.dump(model, model_path)

    # Capture dependency versions for reproducibility (best-effort)
    dep_versions = None
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode == 0 and r.stdout:
            dep_versions = r.stdout.strip().split("\n")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    meta = {
        "schema_version": "1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "dataset": {
            "type": "synthetic_make_classification",
            "n_samples": int(X.shape[0]),
            "n_features": int(X.shape[1]),
        },
        "env": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "dependency_versions": dep_versions,
        "artifacts": {
            "model_path": "model.joblib",
        },
        # store test set deterministically for eval to consume
        "test_set": {
            "path": "test_set.npz",
            "n_samples": int(X_test.shape[0]),
        },
    }

    np.savez_compressed(os.path.join(args.out_dir, "test_set.npz"), X=X_test, y=y_test)

    with open(os.path.join(args.out_dir, "train_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, sort_keys=True)

    print(f"Wrote {model_path}")


if __name__ == "__main__":
    main()
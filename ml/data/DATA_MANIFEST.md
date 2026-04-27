# ML Data Manifest

SHA-256 checksums and row counts for all generated data files.
These files are committed to the repository; this manifest lets you verify integrity
and trace each file back to the script that produced it.

Generated: 2026-04-27

## Parquet files (`ml/data/processed/`)

| File | Rows | SHA-256 | Regenerate with |
|------|------|---------|-----------------|
| `historical.parquet` | 87,720 | `bd6d17339b1c3a4e2a4fc8730f851da71742bd1590e3ac9fe65c491229559836` | `python -m ml.data.collect` |
| `train.parquet` | 61,403 | `4679788a652f022404c2fba10b0504f80ded6dc9bd99724cc42f3c12baaa8a31` | `python -m ml.splits` |
| `val.parquet` | 13,159 | `30eb4b4a044cbb33c64f08d75eef35ca0b6f425db537fc96bbc7531929d64717` | `python -m ml.splits` |
| `test.parquet` | 13,158 | `63287929e1ecf80263c071ed180b734e0a97dbfb03103851236dd8bbeff2fafc` | `python -m ml.splits` |

Split ratios: 70 % train / 15 % val / 15 % test, chronological (no data leakage).
Date range: 2024-04-25 → 2026-04-25. Five spots, 17,544 rows each.

## Model files (`ml/models/`)

| File | Size | SHA-256 |
|------|------|---------|
| `surf_condition_model.joblib` | 1,807 KB | `e4fa43bda68170836b1db485afce1547d63beab63a10f78d1966e40a7fe73b2a` |
| `imputer.joblib` | 1 KB | `eb1f971385797e65aed80e95bfdc84a26a528b664b1c09f3b198d488e5f064d1` |

Model trained with `scikit-learn==1.8.0` (see `requirements.txt`).
Training metadata (hyperparameters, CV scores, feature list): `ml/models/model_metadata.json`.

## Verification

```python
import hashlib
from pathlib import Path

expected = {
    "ml/data/processed/historical.parquet": "bd6d17339b1c3a4e2a4fc8730f851da71742bd1590e3ac9fe65c491229559836",
    "ml/data/processed/train.parquet":      "4679788a652f022404c2fba10b0504f80ded6dc9bd99724cc42f3c12baaa8a31",
    "ml/data/processed/val.parquet":        "30eb4b4a044cbb33c64f08d75eef35ca0b6f425db537fc96bbc7531929d64717",
    "ml/data/processed/test.parquet":       "63287929e1ecf80263c071ed180b734e0a97dbfb03103851236dd8bbeff2fafc",
    "ml/models/surf_condition_model.joblib":"e4fa43bda68170836b1db485afce1547d63beab63a10f78d1966e40a7fe73b2a",
    "ml/models/imputer.joblib":             "eb1f971385797e65aed80e95bfdc84a26a528b664b1c09f3b198d488e5f064d1",
}

for path, sha in expected.items():
    actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    status = "OK" if actual == sha else "MISMATCH"
    print(f"{status}  {path}")
```

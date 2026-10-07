"""Reject invalid or insufficient positive-class F1 before deployment."""
import json
import math
import sys

F1_THRESHOLD = 0.65


def check_quality(f1: float) -> None:
    if not math.isfinite(f1) or not F1_THRESHOLD <= f1 <= 1.0:
        raise ValueError(f"FAILED: f1_score={f1}; required {F1_THRESHOLD} <= F1 <= 1.0")


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        f1 = float(json.load(f)["f1_score"])
    check_quality(f1)
    print(f"PASSED: f1_score={f1:.4f}")

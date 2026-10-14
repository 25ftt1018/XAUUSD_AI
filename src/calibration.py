"""Honest confidence: walk-forward measured hit-rate per model-confidence bucket.

6-fold purged walk-forward (865 H4 trades): model probabilities are uncalibrated,
e.g. claims 65-70% but hits 49.7%. Display hist alongside model so the card
never overstates. Refit when model retrains on new regimes.
"""
# (bucket_lo, bucket_hi, measured_hit_pct)
BUCKETS = [
    (0.60, 0.65, 51.6),
    (0.65, 0.70, 49.7),
    (0.70, 1.01, 53.1),
]


def hist_conf(p: float) -> float:
    for lo, hi, hit in BUCKETS:
        if lo <= p < hi or (hi > 1.0 and p >= lo):
            return hit
    return 50.0

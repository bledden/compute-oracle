def adjust_confidence(
    base_confidence: float,
    horizon: str,
    factors_agree: bool,
) -> float:
    """Adjust confidence score based on horizon and factor agreement."""
    multiplier = 1.0

    # Longer horizons = less confident
    horizon_multipliers = {
        "1h": 1.0,
        "4h": 0.85,
        "24h": 0.65,
    }
    multiplier *= horizon_multipliers.get(horizon, 0.7)

    # Factors agreeing = more confident
    if factors_agree:
        multiplier *= 1.1

    return max(0.1, min(0.95, base_confidence * multiplier))

def mae(errors: list[float]) -> float:
    """Mean Absolute Error."""
    if not errors:
        return 0.0
    return sum(abs(e) for e in errors) / len(errors)


def directional_accuracy(correct: list[bool]) -> float:
    """Percentage of correct direction predictions."""
    if not correct:
        return 0.0
    return sum(1 for c in correct if c) / len(correct)


def rolling_metric(values: list[float], window: int = 20) -> list[float]:
    """Compute rolling average over a window."""
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        window_vals = values[start:i + 1]
        result.append(sum(window_vals) / len(window_vals))
    return result

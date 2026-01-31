def exponential_weight_update(
    old_weight: float, correct: bool, alpha: float = 0.1
) -> float:
    """Update edge weight using exponential moving approach.

    If correct: weight moves toward 1.0
    If incorrect: weight moves toward 0.0
    Alpha controls learning rate.
    """
    if correct:
        new_weight = old_weight + alpha * (1.0 - old_weight)
    else:
        new_weight = old_weight * (1.0 - alpha)
    return max(0.0, min(1.0, new_weight))


def adaptive_alpha(cycle: int) -> float:
    """Learning rate that decays over time.

    High early (0.2) to learn fast from initial predictions.
    Decays to 0.05 to stabilize after many cycles.
    """
    if cycle < 10:
        return 0.20
    elif cycle < 30:
        return 0.15
    elif cycle < 60:
        return 0.10
    else:
        return 0.05

def pass_rate(passed: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return passed / total


def safety_violation_rate(violations: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return violations / total

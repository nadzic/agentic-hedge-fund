from __future__ import annotations

from app.agents.services.insider.types import InsiderDecision, InsiderSnapshot


def score_insider(snapshot: InsiderSnapshot) -> InsiderDecision:
    total_value = snapshot.buy_value_used + snapshot.sell_value_used
    if total_value <= 0:
        return InsiderDecision(
            score=0.0,
            confidence=0.0,
            reasoning="No meaningful insider value flow.",
        )

    score = (snapshot.buy_value_used - snapshot.sell_value_used) / total_value
    # Confidence scales with total traded value, then gets clamped.
    confidence = max(0.50, min(0.90, 0.55 + min(0.35, total_value / 10_000_000)))
    reasoning = (
        f"Insider net flow score={score:.2f}, "
        f"buy_value={snapshot.buy_value_used:.0f}, sell_value={snapshot.sell_value_used:.0f}, "
        f"buy_count={snapshot.buy_count}, sell_count={snapshot.sell_count}."
    )

    return InsiderDecision(
        score=score,
        confidence=confidence,
        reasoning=reasoning,
    )
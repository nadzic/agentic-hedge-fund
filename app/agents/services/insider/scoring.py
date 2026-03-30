from app.agents.services.insider.types import InsiderSnapshot, InsiderDecision

def score_insider(snapshot: InsiderSnapshot) -> InsiderDecision:
  total_value = snapshot.buy_value_used + snapshot.sell_value_used
  if total_value <= 0:
    return InsiderDecision(
      score=0.0,
      confidence=0.0,
      reasoning="No meaningful insider value flow.",
    )

  score = (snapshot.buy_value_used - snapshot.sell_value_used) / total_value
  # The confidence value is calculated as follows:
  # - The "total_value" (sum of buy and sell value) determines how meaningful the insider trades are.
  # - For each $10 million in total insider trade value, we increase confidence by 0.01, up to a maximum add-on of 0.35.
  # - The formula starts at a base of 0.55: "0.55 + min(0.35, total_value / 10_000_000)".
  #   So with $3M total trades, only 0.55 + 0.3 = 0.58 (rounded), for $10M total, it's 0.55 + 0.1 = 0.56, etc.
  # - The result is then clamped between 0.50 and 0.90 to avoid overconfidence or underconfidence.
  # - The $10 million threshold is chosen as an approximate level where insider trading values become materially significant.
  #   This value is somewhat arbitrary, based on typical scales of insider transactions; trades above this represent sizeable, more likely meaningful actions.
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
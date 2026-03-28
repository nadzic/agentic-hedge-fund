from __future__ import annotations

from app.agents.graph.schemas import Signal
from app.agents.services.technicals.types import TechnicalDecision, TechnicalSnapshot


def score_snapshot(snapshot: TechnicalSnapshot) -> TechnicalDecision:
    bullish_votes = 0
    bearish_votes = 0
    reasons: list[str] = []

    if snapshot.rsi14 < 30:
        bullish_votes += 1
        reasons.append("RSI<30 bullish")
    elif snapshot.rsi14 > 70:
        bearish_votes += 1
        reasons.append("RSI>70 bearish")
    else:
        reasons.append("RSI neutral")

    if snapshot.macd > snapshot.macd_signal and snapshot.macd_hist > 0:
        bullish_votes += 1
        reasons.append("MACD bullish crossover")
    elif snapshot.macd < snapshot.macd_signal and snapshot.macd_hist < 0:
        bearish_votes += 1
        reasons.append("MACD bearish crossover")
    else:
        reasons.append("MACD neutral")

    if snapshot.close > snapshot.ema200:
        bullish_votes += 1
        reasons.append("Price above EMA200")
    else:
        bearish_votes += 1
        reasons.append("Price below EMA200")

    if snapshot.close < snapshot.bb_lower:
        bullish_votes += 1
        reasons.append("Below lower Bollinger (mean-reversion bullish)")
    elif snapshot.close > snapshot.bb_upper:
        bearish_votes += 1
        reasons.append("Above upper Bollinger (mean-reversion bearish)")
    else:
        reasons.append("Bollinger neutral")

    score = (bullish_votes - bearish_votes) / 4.0
    if score >= 0.35:
        signal = Signal.BUY
    elif score <= -0.35:
        signal = Signal.SELL
    else:
        signal = Signal.HOLD

    confidence = max(0.50, min(0.90, 0.50 + abs(score) * 0.40))
    reasoning = "; ".join(reasons) + f" | score={score:.2f}"

    return TechnicalDecision(
        signal=signal,
        confidence=confidence,
        score=score,
        votes_bullish=bullish_votes,
        votes_bearish=bearish_votes,
        reasoning=reasoning,
    )

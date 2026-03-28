from __future__ import annotations

from app.agents.services.technicals.data_client import download_ohlcv
from app.agents.services.technicals.indicators import compute_indicators
from app.agents.services.technicals.scoring import TechnicalDecision, score_snapshot


def run_technicals_analysis(
    symbol: str,
    horizon: str,
) -> tuple[TechnicalDecision, dict[str, float | int | str]]:
    frame = download_ohlcv(symbol=symbol, horizon=horizon)
    snapshot = compute_indicators(frame)
    decision = score_snapshot(snapshot)

    metrics: dict[str, float | int | str] = {
        "close": snapshot.close,
        "rsi14": snapshot.rsi14,
        "macd": snapshot.macd,
        "macd_signal": snapshot.macd_signal,
        "macd_hist": snapshot.macd_hist,
        "ema200": snapshot.ema200,
        "bb_upper": snapshot.bb_upper,
        "bb_mid": snapshot.bb_mid,
        "bb_lower": snapshot.bb_lower,
        "technical_score": decision.score,
        "votes_bullish": decision.votes_bullish,
        "votes_bearish": decision.votes_bearish,
    }
    return decision, metrics
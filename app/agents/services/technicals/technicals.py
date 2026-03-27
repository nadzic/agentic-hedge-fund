from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import pandas as pd
import yfinance as yf

from app.agents.graph.schemas import Signal


@dataclass(frozen=True)
class TechnicalSnapshot:
    close: float
    rsi14: float
    macd: float
    macd_signal: float
    macd_hist: float
    ema200: float
    bb_upper: float
    bb_mid: float
    bb_lower: float


@dataclass(frozen=True)
class TechnicalDecision:
    signal: Signal
    confidence: float
    score: float
    votes_bullish: int
    votes_bearish: int
    reasoning: str


def _timeframe_from_horizon(horizon: str) -> tuple[str, str]:
    if horizon == "intraday":
        return "60d", "1h"
    if horizon == "position":
        return "2y", "1d"
    return "1y", "1d"


def _download_ohlcv(symbol: str, horizon: str) -> pd.DataFrame:
    period, interval = _timeframe_from_horizon(horizon)
    raw_frame = yf.download(
        tickers=symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
    )
    if raw_frame is None or raw_frame.empty:
        raise ValueError(f"No market data returned for symbol={symbol}.")
    frame = raw_frame

    # yfinance can return MultiIndex columns for some symbols/options.
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [str(col[0]) for col in frame.columns]

    required = {"Open", "High", "Low", "Close", "Volume"}
    missing = required - set(str(column) for column in frame.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")

    frame = frame.dropna(subset=["Close"]).copy()
    if len(frame) < 220:
        raise ValueError(f"Not enough data points ({len(frame)}) for EMA200/indicators.")
    return frame


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = cast(pd.Series, close.diff())
    gain = cast(pd.Series, delta.clip(lower=0.0))
    loss = cast(pd.Series, -delta.clip(upper=0.0))
    avg_gain = cast(pd.Series, gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean())
    avg_loss = cast(pd.Series, loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean())
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = cast(pd.Series, 100 - (100 / (1 + rs)))
    return cast(pd.Series, rsi.fillna(50.0))


def _compute_indicators(frame: pd.DataFrame) -> TechnicalSnapshot:
    close = cast(pd.Series, frame["Close"]).astype(float)
    ema12 = cast(pd.Series, close.ewm(span=12, adjust=False).mean())
    ema26 = cast(pd.Series, close.ewm(span=26, adjust=False).mean())
    macd = cast(pd.Series, ema12 - ema26)
    macd_signal = cast(pd.Series, macd.ewm(span=9, adjust=False).mean())
    macd_hist = cast(pd.Series, macd - macd_signal)
    ema200 = cast(pd.Series, close.ewm(span=200, adjust=False).mean())
    bb_mid = cast(pd.Series, close.rolling(window=20, min_periods=20).mean())
    bb_std = cast(pd.Series, close.rolling(window=20, min_periods=20).std(ddof=0))
    bb_upper = cast(pd.Series, bb_mid + 2 * bb_std)
    bb_lower = cast(pd.Series, bb_mid - 2 * bb_std)
    rsi14 = _compute_rsi(close, period=14)

    return TechnicalSnapshot(
        close=float(close.iloc[-1]),
        rsi14=float(rsi14.iloc[-1]),
        macd=float(macd.iloc[-1]),
        macd_signal=float(macd_signal.iloc[-1]),
        macd_hist=float(macd_hist.iloc[-1]),
        ema200=float(ema200.iloc[-1]),
        bb_upper=float(bb_upper.iloc[-1]),
        bb_mid=float(bb_mid.iloc[-1]),
        bb_lower=float(bb_lower.iloc[-1]),
    )


def _score_snapshot(snapshot: TechnicalSnapshot) -> TechnicalDecision:
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


def run_technicals_analysis(
    symbol: str,
    horizon: str,
) -> tuple[TechnicalDecision, dict[str, float | int | str]]:
    frame = _download_ohlcv(symbol=symbol, horizon=horizon)
    snapshot = _compute_indicators(frame)
    decision = _score_snapshot(snapshot)

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
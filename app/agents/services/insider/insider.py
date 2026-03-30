from app.agents.services.insider.finnhub_client import fetch_insider_transactions
from app.agents.services.insider.scoring import score_insider
from app.agents.services.insider.types import InsiderSnapshot, InsiderDecision

def _to_float(value: object) -> float:
  if value is None:
    return 0.0
  if isinstance(value, (int, float)):
    return float(value)
  if isinstance(value, str):
    cleaned = value.strip().replace(",", "")
    if cleaned == "":
      return 0.0
    try:
      return float(cleaned)
    except ValueError:
      return 0.0
  return 0.0

def run_insider_analysis(symbol: str, lookback_days: int = 30) -> tuple[InsiderDecision, dict[str, float | int | str]]:
  rows = fetch_insider_transactions(symbol=symbol, lookback_days=lookback_days)

  buy_count = sell_count = 0
  buy_shares = sell_shares = 0.0
  buy_value = sell_value = 0.0

  for row in rows:
    code = str(row.get("transactionCode", "")).upper()
    shares = _to_float(row.get("share") or row.get("shares"))
    price = _to_float(row.get("price"))
    value = abs(shares) * price if price > 0 else abs(shares)

    if code == "P":
      buy_count += 1
      buy_shares += abs(shares)
      buy_value += value
    elif code == "S":
      sell_count += 1
      sell_shares += abs(shares)
      sell_value += value

  snapshot = InsiderSnapshot(
    buy_count=buy_count,
    sell_count=sell_count,
    buy_shares=buy_shares,
    sell_shares=sell_shares,
    buy_value_used=buy_value,
    sell_value_used=sell_value,
    net_shares=buy_shares - sell_shares,
    net_value_used=buy_value - sell_value,
    buy_value_usd=buy_value,
    sell_value_usd=sell_value,
    net_value_usd=buy_value - sell_value,
  )

  decision = score_insider(snapshot)

  metrics: dict[str, float | int | str] = {
        "buy_count": snapshot.buy_count,
        "sell_count": snapshot.sell_count,
        "buy_shares": snapshot.buy_shares,
        "sell_shares": snapshot.sell_shares,
        "buy_value_usd": snapshot.buy_value_usd,
        "sell_value_usd": snapshot.sell_value_usd,
        "net_shares": snapshot.net_shares,
        "net_value_usd": snapshot.net_value_usd,
        "insider_score": decision.score,
        "window_days": lookback_days,
        "records": len(rows),
        "data_source": "finnhub",
  }
  return decision, metrics
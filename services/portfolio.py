from typing import Optional, Dict, Any, List
from core.config import settings

_broker_client = None


def get_alpaca_client():
    global _broker_client
    if _broker_client is None:
        if not settings.alpaca_api_key or not settings.alpaca_api_secret:
            return None
        try:
            from alpaca_trade_api import REST
            _broker_client = REST(
                base_url=settings.alpaca_base_url,
                key_id=settings.alpaca_api_key,
                secret_key=settings.alpaca_api_secret,
            )
        except Exception:
            return None
    return _broker_client


def get_account() -> Optional[Dict[str, Any]]:
    client = get_alpaca_client()
    if client is None:
        return None
    try:
        account = client.get_account()
        return {
            "equity": float(account.equity),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "portfolio_value": float(account.portfolio_value),
            "initial_margin": float(account.initial_margin),
            "maintenance_margin": float(account.maintenance_margin),
            "last_equity": float(account.last_equity),
            "long_market_value": float(account.long_market_value),
            "short_market_value": float(account.short_market_value),
            "unrealized_pl": float(account.unrealized_pl),
            "unrealized_plpc": float(account.unrealized_plpc),
            "status": account.status,
            "account_number": account.account_number,
        }
    except Exception:
        return None


def get_positions() -> List[Dict[str, Any]]:
    client = get_alpaca_client()
    if client is None:
        return []
    try:
        positions = client.list_positions()
        return [
            {
                "symbol": p.symbol,
                "qty": int(p.qty),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc) * 100,
                "side": p.side,
                "cost_basis": float(p.cost_basis),
            }
            for p in positions
        ]
    except Exception:
        return []


def get_open_orders() -> List[Dict[str, Any]]:
    client = get_alpaca_client()
    if client is None:
        return []
    try:
        orders = client.list_orders(status="open")
        return [
            {
                "id": o.id,
                "symbol": o.symbol,
                "qty": int(o.qty),
                "side": o.side,
                "type": o.type,
                "status": o.status,
                "limit_price": float(o.limit_price) if o.limit_price else None,
                "stop_price": float(o.stop_price) if o.stop_price else None,
                "created_at": str(o.created_at),
            }
            for o in orders
        ]
    except Exception:
        return []


def submit_order(
    symbol: str,
    qty: int,
    side: str,
    order_type: str = "market",
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None,
    take_profit_price: Optional[float] = None,
    stop_loss_price: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    client = get_alpaca_client()
    if client is None:
        return None
    try:
        kwargs = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": order_type,
            "time_in_force": "gtc",
        }
        if limit_price:
            kwargs["limit_price"] = limit_price
        if stop_price:
            kwargs["stop_price"] = stop_price
        if take_profit_price and stop_loss_price:
            kwargs["order_class"] = "bracket"
            kwargs["take_profit"] = {"limit_price": take_profit_price}
            kwargs["stop_loss"] = {"stop_price": stop_loss_price}

        order = client.submit_order(**kwargs)
        return {
            "id": order.id,
            "symbol": order.symbol,
            "qty": int(order.qty),
            "side": order.side,
            "type": order.type,
            "status": order.status,
            "created_at": str(order.created_at),
        }
    except Exception as e:
        raise ValueError(str(e))


def cancel_order(order_id: str) -> bool:
    client = get_alpaca_client()
    if client is None:
        return False
    try:
        client.cancel_order(order_id)
        return True
    except Exception:
        return False


def close_all_positions() -> bool:
    client = get_alpaca_client()
    if client is None:
        return False
    try:
        client.close_all_positions()
        return True
    except Exception:
        return False


def get_news_from_alpaca(symbol: str, start: str, end: str) -> List[str]:
    client = get_alpaca_client()
    if client is None:
        return []
    try:
        news = client.get_news(symbol=symbol, start=start, end=end)
        return [ev.__dict__["_raw"]["headline"] for ev in news]
    except Exception:
        return []


def is_connected() -> bool:
    return get_account() is not None

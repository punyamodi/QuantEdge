from fastapi import APIRouter, HTTPException
from models.schemas import OrderRequest
from services.portfolio import (
    submit_order,
    cancel_order,
    close_all_positions,
    get_open_orders,
    is_connected,
)

router = APIRouter()


@router.post("/order")
async def place_order(request: OrderRequest):
    if not is_connected():
        raise HTTPException(
            status_code=503,
            detail="Alpaca broker not connected. Please configure API credentials.",
        )
    valid_sides = ["buy", "sell"]
    if request.side not in valid_sides:
        raise HTTPException(status_code=400, detail=f"Side must be one of: {valid_sides}")
    if request.qty <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    try:
        result = submit_order(
            symbol=request.symbol.upper(),
            qty=request.qty,
            side=request.side,
            order_type=request.order_type,
            limit_price=request.limit_price,
            stop_price=request.stop_price,
            take_profit_price=request.take_profit,
            stop_loss_price=request.stop_loss,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders")
async def list_open_orders():
    if not is_connected():
        raise HTTPException(status_code=503, detail="Alpaca broker not connected.")
    return get_open_orders()


@router.delete("/order/{order_id}")
async def cancel_existing_order(order_id: str):
    if not is_connected():
        raise HTTPException(status_code=503, detail="Alpaca broker not connected.")
    success = cancel_order(order_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel order")
    return {"message": f"Order {order_id} cancelled"}


@router.delete("/positions/all")
async def close_positions():
    if not is_connected():
        raise HTTPException(status_code=503, detail="Alpaca broker not connected.")
    success = close_all_positions()
    if not success:
        raise HTTPException(status_code=400, detail="Failed to close positions")
    return {"message": "All positions closed"}

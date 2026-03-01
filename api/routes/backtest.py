from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, List
from models.schemas import BacktestRequest, BacktestResponse
from services.backtesting import run_backtest
from core.database import SessionLocal
from models.orm import BacktestRun
import json
from datetime import datetime

router = APIRouter()


def _execute_backtest(run_id: int, request: BacktestRequest):
    db = SessionLocal()
    try:
        result = run_backtest(
            strategy=request.strategy,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            parameters=request.parameters,
        )
        result_dict = result.to_dict()

        run = db.query(BacktestRun).filter(BacktestRun.id == run_id).first()
        if run:
            run.final_equity = result_dict["final_equity"]
            run.total_return = result_dict["total_return"]
            run.sharpe_ratio = result_dict["sharpe_ratio"]
            run.sortino_ratio = result_dict["sortino_ratio"]
            run.max_drawdown = result_dict["max_drawdown"]
            run.win_rate = result_dict["win_rate"]
            run.profit_factor = result_dict["profit_factor"]
            run.total_trades = result_dict["total_trades"]
            run.parameters = json.dumps(result_dict)
            run.completed = True
            db.commit()
    except Exception as e:
        run = db.query(BacktestRun).filter(BacktestRun.id == run_id).first()
        if run:
            run.completed = True
            run.parameters = json.dumps({"error": str(e)})
            db.commit()
    finally:
        db.close()


@router.post("/run")
async def start_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    valid_strategies = ["momentum", "mean_reversion", "ml_sentiment"]
    if request.strategy not in valid_strategies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy. Choose from: {valid_strategies}",
        )
    db = SessionLocal()
    try:
        run = BacktestRun(
            strategy_name=request.strategy,
            symbol=request.symbol.upper(),
            start_date=datetime.fromisoformat(request.start_date),
            end_date=datetime.fromisoformat(request.end_date),
            initial_capital=request.initial_capital,
            parameters=json.dumps(request.parameters or {}),
            completed=False,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id
    finally:
        db.close()

    background_tasks.add_task(_execute_backtest, run_id, request)
    return {"id": run_id, "status": "running", "message": "Backtest started"}


@router.get("/results/{run_id}")
async def get_backtest_results(run_id: int):
    db = SessionLocal()
    try:
        run = db.query(BacktestRun).filter(BacktestRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Backtest run not found")

        if not run.completed:
            return {"id": run_id, "status": "running"}

        params = {}
        if run.parameters:
            try:
                params = json.loads(run.parameters)
            except Exception:
                pass

        if "error" in params:
            return {"id": run_id, "status": "failed", "error": params["error"]}

        return {"id": run_id, "status": "completed", **params}
    finally:
        db.close()


@router.get("/history")
async def get_backtest_history(limit: int = 20):
    db = SessionLocal()
    try:
        runs = (
            db.query(BacktestRun)
            .order_by(BacktestRun.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "strategy": r.strategy_name,
                "symbol": r.symbol,
                "start_date": str(r.start_date.date()),
                "end_date": str(r.end_date.date()),
                "initial_capital": r.initial_capital,
                "final_equity": r.final_equity,
                "total_return": r.total_return,
                "sharpe_ratio": r.sharpe_ratio,
                "max_drawdown": r.max_drawdown,
                "win_rate": r.win_rate,
                "total_trades": r.total_trades,
                "completed": r.completed,
                "created_at": str(r.created_at),
            }
            for r in runs
        ]
    finally:
        db.close()


@router.delete("/{run_id}")
async def delete_backtest(run_id: int):
    db = SessionLocal()
    try:
        run = db.query(BacktestRun).filter(BacktestRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Backtest run not found")
        db.delete(run)
        db.commit()
        return {"message": f"Backtest run {run_id} deleted"}
    finally:
        db.close()

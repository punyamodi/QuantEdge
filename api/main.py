from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from api.routes import market, portfolio, backtest, trading
from core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="QuantEdge API",
    description="Quantitative trading platform API with sentiment analysis and backtesting",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market.router, prefix="/api/market", tags=["Market Data"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["Backtesting"])
app.include_router(trading.router, prefix="/api/trading", tags=["Trading"])


@app.get("/")
async def root():
    return {"message": "QuantEdge API is running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

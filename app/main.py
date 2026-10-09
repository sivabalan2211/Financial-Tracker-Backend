from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, SessionLocal

from app.services.seed import seed_default_categories

from app.routers import (
    accounts,
    categories,
    transactions,
    transfers,
    dashboard,
    reports,
    statements,
)

import os
from dotenv import load_dotenv

load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL")

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial Tracker API",
    version="1.0.0",
)

@app.on_event("startup")
def startup():
    db = SessionLocal()

    try:
        seed_default_categories(db)
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(transfers.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(statements.router)

@app.get("/")
def root():
    return {
        "message": "Financial Tracker API",
        "status": "running",
    }

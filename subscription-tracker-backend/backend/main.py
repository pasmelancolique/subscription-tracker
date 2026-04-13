from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine, Base
from routers import auth, transactions, subscriptions
from seed import seed
import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    # Seed data
    try:
        seed()
    except Exception as e:
        print(f"Seed warning: {e}")
    yield


app = FastAPI(
    title="SubscriptionTracker API",
    description="Система распознавания банковских документов для управления подписками",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images
app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")

# Routers
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(subscriptions.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "SubscriptionTracker API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}

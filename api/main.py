import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import get_settings
from api.webhooks import stripe_handler, gumroad_handler
from api.routers import payments

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="AgencyOS API",
    description="Backend API for AgencyOS",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(payments.router)
app.include_router(stripe_handler.router)
app.include_router(gumroad_handler.router)

@app.get("/")
async def root():
    return {
        "message": "AgencyOS API is running",
        "env": settings.APP_ENV,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config.settings import settings
logger = settings.get_logger()

<<<<<<< HEAD
log_dir = settings.log_dir

=======
>>>>>>> afa54285879c9934f132cfce60228967bd595849
from app.routers.drug_router import (
    router as drug_router
)


# --------------------------------------------------
# Loguru Configuration
# --------------------------------------------------

logger.remove()

logger.add(
<<<<<<< HEAD
    sink=f"{log_dir}/drug_information_assistant.log",
=======
    sink="logs/drug_information_assistant.log",
>>>>>>> afa54285879c9934f132cfce60228967bd595849
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    enqueue=True,
    backtrace=True,
    diagnose=True
)

logger.add(
    sink=lambda msg: print(msg, end=""),
    level="INFO"
)


# --------------------------------------------------
# Application Lifespan
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info(
        "Starting Drug Information Assistant API..."
    )

    yield

    logger.info(
        "Shutting down Drug Information Assistant API..."
    )


# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="Drug Information Assistant API",
    description="LangChain + FastAPI Drug Information Assistant",
    version="1.0.0",
    lifespan=lifespan
)


# --------------------------------------------------
# Register Routers
# --------------------------------------------------

app.include_router(
    drug_router
)


# --------------------------------------------------
# Root Endpoint
# --------------------------------------------------

@app.get("/")
async def root():

    logger.info(
        "Root endpoint accessed"
    )

    return {
        "application":
            "Drug Information Assistant",
        "version":
            "1.0.0",
        "status":
            "Running"
    }


# --------------------------------------------------
# Health Check Endpoint
# --------------------------------------------------

@app.get("/health")
async def health_check():

    logger.info(
        "Health check endpoint accessed"
    )

    return {
        "status": "UP",
        "application":
            "Drug Information Assistant"
    }
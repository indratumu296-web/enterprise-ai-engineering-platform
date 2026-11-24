from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from Database.db import initialize_database
from api.routes import router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    initialize_database()
    yield


app = FastAPI(
    title="Autonomous Enterprise AI Agent API",
    description="Local mock ERP and CRM endpoints for the Streamlit agent.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "Autonomous Enterprise AI Agent API is running.", "docs": "/docs"}

import os
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers.router import api
from src.database import init_db

load_dotenv(find_dotenv(), override=False)

app = FastAPI(
    title=os.getenv("API_NAME"),
    description=os.getenv("API_DESCRIPTION"),
    version=os.getenv("API_VERSION"),
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api, prefix="/api/v" + os.getenv("API_VERSION"))


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    init_db()
    print("Database initialized")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST"),
        port=int(os.getenv("API_PORT")),
        reload=True,
        reload_excludes=["__pycache__", "logs"],
        log_level="debug"
    )
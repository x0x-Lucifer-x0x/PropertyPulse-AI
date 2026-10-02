import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine, SessionLocal
from app.routers import chat, properties, leads, voice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("property_pulse")

app = FastAPI(title="PropertyPulse AI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

    # Build the RAG index eagerly so the first chat request isn't slow,
    # and so a build-time failure surfaces at startup, not mid-conversation.
    from app.rag.index import get_index
    db = SessionLocal()
    try:
        get_index(db)
    except Exception:
        logger.exception("RAG index build failed at startup; will retry lazily on first use")
    finally:
        db.close()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak stack traces to the client.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong on our end. Please try again."},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(chat.router)
app.include_router(properties.router)
app.include_router(leads.router)
app.include_router(voice.router)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.db.database import engine
from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import ApiException, api_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):

    # --- Startup Logic ---
    print("🔄 Attempting to connect to DB alright...")
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print(f"✅ DB Connection successful: {settings.DATABASE_URL}")
    except Exception as e:
        print(f"❌ DB Connection failed: {e}")
        raise e

    yield

    # --- Shutdown Logic ---
    print("🔄 Closing DB connection pool...")
    await engine.dispose()
    print("✅ DB connection pool closed.")

        

app = FastAPI(title="Shopease", version="0.1.0", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4200","http://deploy-shopease856.s3-website.eu-north-1.amazonaws.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/hello")
async def say_hello():
    return {"message": "Hello World"}

app.add_exception_handler(ApiException, api_exception_handler)

app.include_router(api_router, prefix="/api")

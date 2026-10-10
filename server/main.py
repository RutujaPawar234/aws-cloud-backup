"""
FastAPI application entry point (AWS backend).

Run locally:   uvicorn server.main:app --reload
Swagger docs:  http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routes import auth, files, health

app = FastAPI(
    title="AWS Cloud-Based File Backup & Restore API",
    description=(
        "Backend for the desktop backup app. Handles authentication, file "
        "uploads to Amazon S3, metadata in Amazon DynamoDB, downloads/restores, "
        "and deletion."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(files.router)


@app.get("/", tags=["health"])
async def root() -> dict:
    return {"message": "AWS Cloud Backup API is running. See /docs for the API."}

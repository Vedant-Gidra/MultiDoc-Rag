# uvicorn app.main:app --reload
from dotenv import load_dotenv
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import upload, query, files, auth
from app.models import init_db

# Load environment variables from .env file
load_dotenv()


app = FastAPI()

# Initialize database
init_db()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(auth.router)
app.include_router(files.router)
app.include_router(upload.router)
app.include_router(query.router)
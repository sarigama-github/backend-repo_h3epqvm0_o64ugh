import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from database import db, create_document, get_documents

app = FastAPI(title="Study Time Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utility functions

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split(":")
        return hashlib.sha256((salt + password).encode()).hexdigest() == hashed
    except Exception:
        return False


# Models for requests

class RegisterPayload(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


class BlogCreatePayload(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    author: str
    tags: List[str] = []
    cover_url: Optional[str] = None


class ContactPayload(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str


@app.get("/")
def root():
    return {"message": "Study Time Tracker Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "Unknown"
            try:
                response["collections"] = db.list_collection_names()[:10]
            except Exception as e:
                response["collections"] = [f"Error: {str(e)[:60]}"]
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:60]}"

    return response


# Auth endpoints
@app.post("/api/auth/register")
def register(payload: RegisterPayload):
    # Check if user exists
    existing = db["studentuser"].find_one({"email": payload.email}) if db else None
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = hash_password(payload.password)
    user_doc = {
        "name": payload.name,
        "email": payload.email,
        "password_hash": password_hash,
        "avatar_url": None,
        "school": None,
        "major": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    inserted_id = db["studentuser"].insert_one(user_doc).inserted_id if db else None
    return {"ok": True, "user_id": str(inserted_id)}


@app.post("/api/auth/login")
def login(payload: LoginPayload, request: Request):
    user = db["studentuser"].find_one({"email": payload.email}) if db else None
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session_doc = {
        "user_id": str(user.get("_id")),
        "token": token,
        "user_agent": request.headers.get("user-agent"),
        "ip": request.client.host if request.client else None,
        "expires_at_iso": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    db["session"].insert_one(session_doc)
    return {"ok": True, "token": token, "expires_at": session_doc["expires_at_iso"], "name": user.get("name")}


# Blog endpoints (simple list + create for demo)
@app.get("/api/blog")
def list_blog(limit: int = 10):
    posts = get_documents("blogpost", {}, limit)
    # sanitize _id
    for p in posts:
        p["id"] = str(p.pop("_id", ""))
    return {"ok": True, "items": posts}


@app.post("/api/blog")
def create_blog(payload: BlogCreatePayload):
    doc = payload.model_dump()
    inserted_id = create_document("blogpost", doc)
    return {"ok": True, "id": inserted_id}


# Contact form endpoint
@app.post("/api/contact")
def contact(payload: ContactPayload):
    doc = payload.model_dump()
    inserted_id = create_document("contactmessage", doc)
    return {"ok": True, "id": inserted_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

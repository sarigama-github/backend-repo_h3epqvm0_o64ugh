"""
Database Schemas for Study Time Tracker

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- StudentUser -> "studentuser"
- BlogPost -> "blogpost"
- ContactMessage -> "contactmessage"
- Session -> "session"
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


class StudentUser(BaseModel):
    """
    Students collection schema
    Collection name: "studentuser"
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="Salted password hash (server generated)")
    avatar_url: Optional[str] = Field(None, description="Optional avatar URL")
    school: Optional[str] = Field(None, description="School / University")
    major: Optional[str] = Field(None, description="Major or focus area")


class Session(BaseModel):
    """
    Auth session tokens
    Collection name: "session"
    """
    user_id: str = Field(..., description="Associated user id as string")
    token: str = Field(..., description="Session token")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    ip: Optional[str] = Field(None, description="Client IP")
    expires_at_iso: Optional[str] = Field(None, description="ISO timestamp for expiry")


class BlogPost(BaseModel):
    """
    Blog posts for marketing / study tips
    Collection name: "blogpost"
    """
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    author: str
    tags: List[str] = []
    cover_url: Optional[str] = None
    published: bool = True


class ContactMessage(BaseModel):
    """
    Contact form submissions
    Collection name: "contactmessage"
    """
    name: str
    email: EmailStr
    subject: str
    message: str

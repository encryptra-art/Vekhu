"""
PULSE Request & Response Validation Models
Strict validation for ratings, reviews, profile creation, and reports.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

class ReviewSubmission(BaseModel):
    profile_id: int
    rating: int = Field(..., ge=1, le=5, description="1 to 5 star rating")
    perspective_context: str = Field(..., min_length=2, max_length=100)
    headline: str = Field(..., min_length=3, max_length=120)
    content: str = Field(..., min_length=10, max_length=2500)
    author_alias: Optional[str] = Field("Anonymous Contributor", max_length=50)

class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    title: str = Field(..., min_length=3, max_length=120)
    category: str = Field(..., min_length=2, max_length=50)
    bio: str = Field(..., min_length=20, max_length=1500)
    avatar_url: Optional[str] = None
    external_url: Optional[str] = None

class ReportSubmission(BaseModel):
    target_type: str = Field(..., pattern="^(profile|review)$")
    target_id: int
    reason: str = Field(..., min_length=3, max_length=50)
    details: Optional[str] = Field("", max_length=1000)

class ResolveReport(BaseModel):
    report_id: int
    action: str = Field(..., pattern="^(hide|dismiss)$")

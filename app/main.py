"""
VEKHU Application Server (FastAPI)
See What The World Really Thinks — Public Perception Index
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Header, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pathlib import Path
from typing import Optional

from app.database import init_db, get_db
import app.crud as crud
from app.models import ReviewSubmission, ProfileCreate, ReportSubmission, ResolveReport

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and initial seed dossiers on startup
    await init_db()
    yield

app = FastAPI(
    title="VEKHU — Public Perception Index",
    description="See What The World Really Thinks. The Real-Time Public Sentiment & Perception Index.",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static assets and Jinja2 templates
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ============================================================================
# SEO & SITEMAP ENDPOINTS (Google Crawlers & Indexation)
# ============================================================================

@app.get("/robots.txt", response_class=Response)
async def robots_txt():
    content = "User-agent: *\nAllow: /\nSitemap: https://vekhu.com/sitemap.xml\n"
    return Response(content=content, media_type="text/plain")

@app.get("/sitemap.xml", response_class=Response)
async def sitemap_xml():
    profiles = await crud.get_all_profiles()
    urls = [
        "https://vekhu.com/",
        "https://vekhu.com/discover",
        "https://vekhu.com/guidelines",
        "https://vekhu.com/create"
    ]
    for p in profiles:
        urls.append(f"https://vekhu.com/profile/{p['slug']}")

    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml_lines.append(f"  <url><loc>{u}</loc><changefreq>daily</changefreq><priority>0.8</priority></url>")
    xml_lines.append('</urlset>')
    
    return Response(content="\n".join(xml_lines), media_type="application/xml")


# ============================================================================
# HTML WEB PAGES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Landing Page with featured public figures and core philosophy."""
    featured_profiles = await crud.get_featured_profiles(limit=6)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "profiles": featured_profiles,
            "active_page": "home"
        }
    )

@app.get("/discover", response_class=HTMLResponse)
async def discover(
    request: Request,
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    sort: Optional[str] = Query("heat")
):
    """Discovery & Search Directory with dynamic category and sorting filters."""
    profiles = await crud.get_all_profiles(category=category, search=q, sort_by=sort)
    return templates.TemplateResponse(
        request=request,
        name="discover.html",
        context={
            "profiles": profiles,
            "current_category": category or "All",
            "current_search": q or "",
            "current_sort": sort or "heat",
            "active_page": "discover"
        }
    )

@app.get("/profile/{slug}", response_class=HTMLResponse)
async def profile_detail(request: Request, slug: str):
    """Public Perception Dossier for an individual public figure."""
    profile = await crud.get_profile_by_slug(slug)
    if not profile or profile.get("status") == "hidden":
        raise HTTPException(status_code=404, detail="Public figure dossier not found or unindexed.")

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "profile": profile,
            "active_page": "profile"
        }
    )

@app.get("/create", response_class=HTMLResponse)
async def create_profile_page(request: Request):
    """Instant Public Figure Creator."""
    return templates.TemplateResponse(
        request=request,
        name="create_profile.html",
        context={
            "active_page": "create"
        }
    )

@app.get("/guidelines", response_class=HTMLResponse)
async def guidelines_page(request: Request):
    """Community Standards & Public Figure Doctrine."""
    return templates.TemplateResponse(
        request=request,
        name="guidelines.html",
        context={
            "active_page": "guidelines"
        }
    )

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Moderation Console for inspecting and acting on reports."""
    reports = await crud.get_admin_reports()
    all_profiles = await crud.get_all_profiles()
    
    total_reviews = sum(p["rating_count"] for p in all_profiles)
    stats = {
        "total_profiles": len(all_profiles),
        "total_reviews": total_reviews
    }
    
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "reports": reports,
            "stats": stats,
            "active_page": "admin"
        }
    )


# ============================================================================
# API ENDPOINTS (Ratings, Profiles, Reports, Votes)
# ============================================================================

@app.post("/api/reviews")
async def api_submit_review(
    review: ReviewSubmission,
    request: Request,
    x_session_token: Optional[str] = Header("anonymous-session")
):
    """Submit a zero-friction rating and perspective with anti-duplicate prevention."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    ip_hash = crud.hash_identifier(client_ip)

    # Check for duplicate review from same actor on this profile
    already_reviewed = await crud.check_user_already_reviewed(
        profile_id=review.profile_id,
        ip_hash=ip_hash,
        session_token=x_session_token
    )
    if already_reviewed:
        raise HTTPException(
            status_code=400,
            detail="You have already recorded a perception for this public figure. One perspective per contributor."
        )

    result = await crud.add_review(
        profile_id=review.profile_id,
        rating=review.rating,
        perspective_context=review.perspective_context,
        headline=review.headline,
        content=review.content,
        author_alias=review.author_alias or "Anonymous Observer",
        ip_hash=ip_hash,
        session_token=x_session_token
    )
    return result

@app.post("/api/reviews/{review_id}/helpful")
async def api_vote_helpful(
    review_id: int,
    x_session_token: Optional[str] = Header("anonymous-session")
):
    """Mark a review perspective as helpful."""
    result = await crud.vote_helpful(review_id=review_id, voter_token=x_session_token)
    return result

@app.post("/api/profiles")
async def api_create_profile(profile: ProfileCreate):
    """Instantly publish a new public figure profile."""
    result = await crud.create_profile(
        name=profile.name,
        title=profile.title,
        category=profile.category,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        external_url=profile.external_url
    )
    return {"success": True, "slug": result["slug"], "name": result["name"]}

@app.post("/api/reports")
async def api_submit_report(report: ReportSubmission, request: Request):
    """File a community moderation report."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    ip_hash = crud.hash_identifier(client_ip)
    result = await crud.create_report(
        target_type=report.target_type,
        target_id=report.target_id,
        reason=report.reason,
        details=report.details or "",
        reporter_ip_hash=ip_hash
    )
    return result

@app.post("/api/admin/reports/resolve")
async def api_resolve_report(action_data: ResolveReport):
    """Admin action to dismiss or hide reported content."""
    result = await crud.resolve_report(report_id=action_data.report_id, action=action_data.action)
    return result

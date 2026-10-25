"""
VEKHU Application Server (FastAPI)
See What The World Really Thinks — Public Perception Index
"""

import os
import hashlib
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Header, Depends, Query, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse
from pathlib import Path
from typing import Optional

from app.database import init_db, get_db
import app.crud as crud
from app.models import ReviewSubmission, ProfileCreate, ReportSubmission, ResolveReport

BASE_DIR = Path(__file__).resolve().parent

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "vekhu2026")
ADMIN_SESSION_TOKEN = hashlib.sha256(f"vekhu-secret-salt-{ADMIN_PASSWORD}".encode()).hexdigest()

def is_admin(request: Request) -> bool:
    return request.cookies.get("vekhu_admin_session") == ADMIN_SESSION_TOKEN

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
# SEO, SITEMAP & RSS FEED ENDPOINTS (Google Crawlers & Rich Indexing)
# ============================================================================

@app.get("/robots.txt", response_class=Response)
async def robots_txt():
    """Optimized robots.txt allowing public indexation while protecting admin."""
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin\n"
        "Disallow: /api/\n"
        "Allow: /api/profiles\n"
        "Allow: /api/reviews\n"
        "\n"
        "Sitemap: https://vekhu.com/sitemap.xml\n"
        "Host: https://vekhu.com\n"
    )
    return Response(content=content, media_type="text/plain; charset=utf-8")

@app.get("/sitemap.xml", response_class=Response)
async def sitemap_xml():
    """Standard, 100% compliant XML Sitemap for Google Search Console."""
    profiles = await crud.get_all_profiles()

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  <url>',
        '    <loc>https://vekhu.com/</loc>',
        '    <changefreq>hourly</changefreq>',
        '    <priority>1.0</priority>',
        '  </url>',
        '  <url>',
        '    <loc>https://vekhu.com/discover</loc>',
        '    <changefreq>daily</changefreq>',
        '    <priority>0.9</priority>',
        '  </url>',
        '  <url>',
        '    <loc>https://vekhu.com/create</loc>',
        '    <changefreq>monthly</changefreq>',
        '    <priority>0.7</priority>',
        '  </url>',
        '  <url>',
        '    <loc>https://vekhu.com/guidelines</loc>',
        '    <changefreq>monthly</changefreq>',
        '    <priority>0.6</priority>',
        '  </url>'
    ]

    for p in profiles:
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>https://vekhu.com/profile/{p["slug"]}</loc>')
        xml_lines.append('    <changefreq>daily</changefreq>')
        xml_lines.append('    <priority>0.9</priority>')
        xml_lines.append('  </url>')

    xml_lines.append('</urlset>')
    return Response(content="\n".join(xml_lines), media_type="application/xml; charset=utf-8")

@app.get("/feed.xml", response_class=Response)
async def rss_feed():
    """RSS 2.0 Feed for search engines, web crawlers, and content discovery."""
    profiles = await crud.get_all_profiles(sort_by="newest")
    
    rss = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        '<channel>',
        '  <title>VEKHU — Public Perception Index</title>',
        '  <link>https://vekhu.com</link>',
        '  <description>Real-time public sentiment, reviews, and 5-star distribution curves for founders, creators, and cultural figures.</description>',
        '  <language>en-us</language>',
        '  <atom:link href="https://vekhu.com/feed.xml" rel="self" type="application/rss+xml" />'
    ]

    for p in profiles[:20]:
        rss.append('  <item>')
        rss.append(f'    <title>{p["name"]} ({p["title"]}) - Perception Dossier</title>')
        rss.append(f'    <link>https://vekhu.com/profile/{p["slug"]}</link>')
        rss.append(f'    <description><![CDATA[{p["bio"]} Rated {p["average_rating"]}/5 based on {p["rating_count"]} perspectives.]]></description>')
        rss.append(f'    <guid>https://vekhu.com/profile/{p["slug"]}</guid>')
        rss.append('  </item>')

    rss.append('</channel>')
    rss.append('</rss>')
    return Response(content="\n".join(rss), media_type="application/rss+xml; charset=utf-8")


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

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin Login Screen."""
    if is_admin(request):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={"error": None}
    )

@app.post("/admin/login", response_class=HTMLResponse)
async def admin_login_post(request: Request):
    """Process admin login form."""
    form_data = await request.form()
    password = form_data.get("password", "")

    if password == ADMIN_PASSWORD:
        response = RedirectResponse(url="/admin", status_code=302)
        response.set_cookie(
            key="vekhu_admin_session",
            value=ADMIN_SESSION_TOKEN,
            max_age=86400 * 30,  # 30 days
            httponly=True,
            samesite="lax"
        )
        return response

    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={"error": "Invalid admin passcode. Access denied."}
    )

@app.get("/admin/logout")
async def admin_logout():
    """Logout from admin console."""
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie(key="vekhu_admin_session")
    return response

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Secure Command Center for Approvals, Moderation & Operations."""
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    pending_profiles = await crud.get_pending_profiles()
    all_profiles = await crud.get_all_profiles_admin()
    all_reviews = await crud.get_all_reviews_admin(limit=100)
    reports = await crud.get_admin_reports()
    
    total_reviews = len(all_reviews)
    pending_reports = [r for r in reports if r.get("status") == "pending"]

    stats = {
        "total_profiles": len(all_profiles),
        "active_profiles": len([p for p in all_profiles if p.get("status") == "active"]),
        "pending_profiles": len(pending_profiles),
        "total_reviews": total_reviews,
        "pending_reports": len(pending_reports)
    }
    
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "pending_profiles": pending_profiles,
            "all_profiles": all_profiles,
            "all_reviews": all_reviews,
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
    """Submit a new public figure profile (queued for editorial approval)."""
    result = await crud.create_profile(
        name=profile.name,
        title=profile.title,
        category=profile.category,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        external_url=profile.external_url,
        status="pending"
    )
    return {
        "success": True,
        "status": "pending",
        "slug": result["slug"],
        "name": result["name"],
        "message": "Public figure submitted for editorial approval! It will appear on VEKHU once approved by an admin."
    }

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

# ============================================================================
# ADMIN PROTECTED APIS (Approvals, Deletions, Status Toggles)
# ============================================================================

@app.post("/api/admin/profiles/{profile_id}/approve")
async def api_approve_profile(profile_id: int, request: Request):
    """Approve a pending public figure profile."""
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Unauthorized")
    await crud.approve_profile(profile_id)
    return {"success": True, "message": "Profile approved and published to live index"}

@app.post("/api/admin/profiles/{profile_id}/reject")
async def api_reject_profile(profile_id: int, request: Request):
    """Reject and delete a pending public figure profile."""
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Unauthorized")
    await crud.reject_profile(profile_id)
    return {"success": True, "message": "Profile rejected and deleted"}

@app.post("/api/admin/profiles/{profile_id}/delete")
async def api_delete_profile(profile_id: int, request: Request):
    """Permanently delete an existing public figure profile."""
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Unauthorized")
    await crud.delete_profile_admin(profile_id)
    return {"success": True, "message": "Profile deleted permanently"}

@app.post("/api/admin/profiles/{profile_id}/verify")
async def api_toggle_verify_profile(profile_id: int, request: Request):
    """Toggle verified badge on a public figure profile."""
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Unauthorized")
    await crud.toggle_verify_profile(profile_id)
    return {"success": True, "message": "Verified status toggled"}

@app.post("/api/admin/reviews/{review_id}/delete")
async def api_delete_review(review_id: int, request: Request):
    """Permanently delete a community review."""
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Unauthorized")
    await crud.delete_review_admin(review_id)
    return {"success": True, "message": "Review deleted and scores recalculated"}

@app.post("/api/admin/reviews/{review_id}/toggle-status")
async def api_toggle_review_status(review_id: int, request: Request):
    """Toggle review between published and hidden."""
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Unauthorized")
    new_status = await crud.toggle_review_status_admin(review_id)
    return {"success": True, "status": new_status, "message": f"Review is now {new_status}"}

@app.post("/api/admin/reports/resolve")
async def api_resolve_report(action_data: ResolveReport, request: Request):
    """Admin action to dismiss or hide reported content."""
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Unauthorized")
    result = await crud.resolve_report(report_id=action_data.report_id, action=action_data.action)
    return result

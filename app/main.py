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
    """Dynamic XML Sitemap with priorities and freshness for Google Search Console."""
    profiles = await crud.get_all_profiles()
    now_date = "2026-10-24"

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
        ' xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
        '  <url>',
        '    <loc>https://vekhu.com/</loc>',
        f'    <lastmod>{now_date}</lastmod>',
        '    <changefreq>hourly</changefreq>',
        '    <priority>1.0</priority>',
        '  </url>',
        '  <url>',
        '    <loc>https://vekhu.com/discover</loc>',
        f'    <lastmod>{now_date}</lastmod>',
        '    <changefreq>daily</changefreq>',
        '    <priority>0.9</priority>',
        '  </url>',
        '  <url>',
        '    <loc>https://vekhu.com/create</loc>',
        f'    <lastmod>{now_date}</lastmod>',
        '    <changefreq>monthly</changefreq>',
        '    <priority>0.7</priority>',
        '  </url>',
        '  <url>',
        '    <loc>https://vekhu.com/guidelines</loc>',
        f'    <lastmod>{now_date}</lastmod>',
        '    <changefreq>monthly</changefreq>',
        '    <priority>0.6</priority>',
        '  </url>'
    ]

    for p in profiles:
        avatar = p.get("avatar_url", "")
        name = p.get("name", "")
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>https://vekhu.com/profile/{p["slug"]}</loc>')
        xml_lines.append(f'    <lastmod>{now_date}</lastmod>')
        xml_lines.append('    <changefreq>daily</changefreq>')
        xml_lines.append('    <priority>0.95</priority>')
        if avatar:
            xml_lines.append('    <image:image>')
            xml_lines.append(f'      <image:loc>{avatar}</image:loc>')
            xml_lines.append(f'      <image:title>{name} - Public Perception &amp; Reviews</image:title>')
            xml_lines.append('    </image:image>')
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

"""
PULSE CRUD Operations
High-performance database operations with mathematical aggregation and abuse prevention.
"""

import json
import re
import hashlib
from typing import List, Optional, Dict, Any
from app.database import get_db

def hash_identifier(ip: str) -> str:
    """Hash IP address for one-way privacy preservation and rate-limiting."""
    return hashlib.sha256(f"pulse-salt-{ip}".encode()).hexdigest()

def slugify(text: str) -> str:
    """Generate clean URL slug from name."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

async def get_featured_profiles(limit: int = 4) -> List[Dict[str, Any]]:
    """Retrieve featured public figures for landing page."""
    async with get_db() as db:
        async with db.execute(
            """
            SELECT * FROM profiles 
            WHERE status = 'active' 
            ORDER BY rating_count DESC, average_rating DESC 
            LIMIT ?
            """,
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_all_profiles(
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "heat"
) -> List[Dict[str, Any]]:
    """Retrieve filtered, sorted profiles for Discovery."""
    query = "SELECT * FROM profiles WHERE status = 'active'"
    params = []

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if search and search.strip():
        query += " AND (name LIKE ? OR title LIKE ? OR bio LIKE ?)"
        wildcard = f"%{search.strip()}%"
        params.extend([wildcard, wildcard, wildcard])

    if sort_by == "rating":
        query += " ORDER BY average_rating DESC, rating_count DESC"
    elif sort_by == "newest":
        query += " ORDER BY created_at DESC"
    else:  # "heat" / trending
        query += " ORDER BY rating_count DESC, average_rating DESC"

    async with get_db() as db:
        async with db.execute(query, tuple(params)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_profile_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Retrieve profile and its reviews by slug."""
    async with get_db() as db:
        async with db.execute("SELECT * FROM profiles WHERE slug = ?", (slug,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            profile = dict(row)
            profile["external_links"] = json.loads(profile.get("external_links") or "[]")
            profile["distribution"] = json.loads(profile.get("distribution") or '{"1":0,"2":0,"3":0,"4":0,"5":0}')

        # Fetch published reviews
        async with db.execute(
            """
            SELECT * FROM reviews 
            WHERE profile_id = ? AND status = 'published'
            ORDER BY helpful_count DESC, created_at DESC
            """,
            (profile["id"],)
        ) as cursor:
            reviews = await cursor.fetchall()
            profile["reviews"] = [dict(r) for r in reviews]

        return profile

async def check_user_already_reviewed(profile_id: int, ip_hash: str, session_token: str) -> bool:
    """Check if visitor has already submitted a rating for this profile."""
    async with get_db() as db:
        async with db.execute(
            """
            SELECT id FROM reviews 
            WHERE profile_id = ? AND (ip_hash = ? OR session_token = ?)
            """,
            (profile_id, ip_hash, session_token)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None

async def add_review(
    profile_id: int,
    rating: int,
    perspective_context: str,
    headline: str,
    content: str,
    author_alias: str,
    ip_hash: str,
    session_token: str
) -> Dict[str, Any]:
    """Submit a review, update profile distribution and average score atomically."""
    async with get_db() as db:
        # Insert review
        await db.execute(
            """
            INSERT INTO reviews (profile_id, rating, perspective_context, headline, content, author_alias, ip_hash, session_token)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                rating,
                perspective_context,
                headline.strip(),
                content.strip(),
                author_alias.strip() or "Anonymous Observer",
                ip_hash,
                session_token
            )
        )

        # Recalculate aggregate stats
        async with db.execute(
            "SELECT rating FROM reviews WHERE profile_id = ? AND status = 'published'",
            (profile_id,)
        ) as cursor:
            ratings = [r[0] for r in await cursor.fetchall()]

        total_count = len(ratings)
        avg_rating = round(sum(ratings) / total_count, 1) if total_count > 0 else 0.0
        dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        for r in ratings:
            dist[str(r)] = dist.get(str(r), 0) + 1

        await db.execute(
            """
            UPDATE profiles 
            SET rating_count = ?, average_rating = ?, distribution = ?
            WHERE id = ?
            """,
            (total_count, avg_rating, json.dumps(dist), profile_id)
        )
        await db.commit()

        return {
            "success": True,
            "rating_count": total_count,
            "average_rating": avg_rating,
            "distribution": dist
        }

async def create_profile(
    name: str,
    title: str,
    category: str,
    bio: str,
    avatar_url: Optional[str] = None,
    external_url: Optional[str] = None,
    status: str = "pending"
) -> Dict[str, Any]:
    """Create a new public figure profile (default status is pending approval)."""
    base_slug = slugify(name)
    slug = base_slug
    counter = 1

    async with get_db() as db:
        while True:
            async with db.execute("SELECT id FROM profiles WHERE slug = ?", (slug,)) as cursor:
                if not await cursor.fetchone():
                    break
                counter += 1
                slug = f"{base_slug}-{counter}"

        fallback_avatar = f"https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80"
        avatar = avatar_url.strip() if avatar_url and avatar_url.strip() else fallback_avatar
        
        links = []
        if external_url and external_url.strip():
            links.append({"label": "Official Reference", "url": external_url.strip()})

        cursor = await db.execute(
            """
            INSERT INTO profiles (slug, name, title, category, bio, avatar_url, external_links, rating_count, average_rating, distribution, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0.0, '{"1":0,"2":0,"3":0,"4":0,"5":0}', ?)
            """,
            (slug, name.strip(), title.strip(), category.strip(), bio.strip(), avatar, json.dumps(links), status)
        )
        await db.commit()
        return {"id": cursor.lastrowid, "slug": slug, "name": name, "status": status}

async def get_pending_profiles() -> List[Dict[str, Any]]:
    """Retrieve profiles waiting for administrator approval."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM profiles WHERE status = 'pending' ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def approve_profile(profile_id: int) -> bool:
    """Approve a pending public figure and publish to the live site."""
    async with get_db() as db:
        await db.execute("UPDATE profiles SET status = 'active' WHERE id = ?", (profile_id,))
        await db.commit()
        return True

async def reject_profile(profile_id: int) -> bool:
    """Reject a suggested profile and delete it from the database."""
    async with get_db() as db:
        await db.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        await db.commit()
        return True

async def delete_profile_admin(profile_id: int) -> bool:
    """Permanently delete a profile and its associated reviews."""
    async with get_db() as db:
        await db.execute("DELETE FROM reviews WHERE profile_id = ?", (profile_id,))
        await db.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        await db.commit()
        return True

async def toggle_verify_profile(profile_id: int) -> bool:
    """Toggle verified public figure badge."""
    async with get_db() as db:
        await db.execute(
            "UPDATE profiles SET is_verified = CASE WHEN is_verified = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (profile_id,)
        )
        await db.commit()
        return True

async def get_all_profiles_admin() -> List[Dict[str, Any]]:
    """Retrieve all profiles regardless of status for admin management."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM profiles ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_all_reviews_admin(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieve recent reviews across all figures for admin review."""
    async with get_db() as db:
        async with db.execute(
            """
            SELECT r.*, p.name as profile_name, p.slug as profile_slug 
            FROM reviews r 
            JOIN profiles p ON r.profile_id = p.id 
            ORDER BY r.created_at DESC 
            LIMIT ?
            """,
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def delete_review_admin(review_id: int) -> bool:
    """Permanently delete a review and recalculate profile rating aggregates."""
    async with get_db() as db:
        async with db.execute("SELECT profile_id FROM reviews WHERE id = ?", (review_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False
            profile_id = row[0]

        await db.execute("DELETE FROM votes WHERE review_id = ?", (review_id,))
        await db.execute("DELETE FROM reviews WHERE id = ?", (review_id,))

        # Recalculate aggregate stats
        async with db.execute(
            "SELECT rating FROM reviews WHERE profile_id = ? AND status = 'published'",
            (profile_id,)
        ) as cursor:
            ratings = [r[0] for r in await cursor.fetchall()]

        total_count = len(ratings)
        avg_rating = round(sum(ratings) / total_count, 1) if total_count > 0 else 0.0
        dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        for r in ratings:
            dist[str(r)] = dist.get(str(r), 0) + 1

        await db.execute(
            """
            UPDATE profiles 
            SET rating_count = ?, average_rating = ?, distribution = ? 
            WHERE id = ?
            """,
            (total_count, avg_rating, json.dumps(dist), profile_id)
        )
        await db.commit()
        return True

async def toggle_review_status_admin(review_id: int) -> str:
    """Toggle review between published and hidden."""
    async with get_db() as db:
        async with db.execute("SELECT status, profile_id FROM reviews WHERE id = ?", (review_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return "not_found"
            new_status = "hidden" if row[0] == "published" else "published"
            profile_id = row[1]

        await db.execute("UPDATE reviews SET status = ? WHERE id = ?", (new_status, review_id))

        # Recalculate aggregate stats for published only
        async with db.execute(
            "SELECT rating FROM reviews WHERE profile_id = ? AND status = 'published'",
            (profile_id,)
        ) as cursor:
            ratings = [r[0] for r in await cursor.fetchall()]

        total_count = len(ratings)
        avg_rating = round(sum(ratings) / total_count, 1) if total_count > 0 else 0.0
        dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        for r in ratings:
            dist[str(r)] = dist.get(str(r), 0) + 1

        await db.execute(
            """
            UPDATE profiles 
            SET rating_count = ?, average_rating = ?, distribution = ? 
            WHERE id = ?
            """,
            (total_count, avg_rating, json.dumps(dist), profile_id)
        )
        await db.commit()
        return new_status

async def vote_helpful(review_id: int, voter_token: str) -> Dict[str, Any]:
    """Toggle or record helpful vote on a review."""
    async with get_db() as db:
        async with db.execute(
            "SELECT id FROM votes WHERE review_id = ? AND voter_token = ?",
            (review_id, voter_token)
        ) as cursor:
            if await cursor.fetchone():
                return {"success": False, "message": "Already upvoted"}

        await db.execute(
            "INSERT INTO votes (review_id, voter_token) VALUES (?, ?)",
            (review_id, voter_token)
        )
        await db.execute(
            "UPDATE reviews SET helpful_count = helpful_count + 1 WHERE id = ?",
            (review_id,)
        )
        await db.commit()

        async with db.execute("SELECT helpful_count FROM reviews WHERE id = ?", (review_id,)) as cursor:
            row = await cursor.fetchone()
            return {"success": True, "helpful_count": row[0]}

async def create_report(
    target_type: str,
    target_id: int,
    reason: str,
    details: str,
    reporter_ip_hash: str
) -> Dict[str, Any]:
    """File a report against a profile or review."""
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO reports (target_type, target_id, reason, details, reporter_ip_hash)
            VALUES (?, ?, ?, ?, ?)
            """,
            (target_type, target_id, reason, details.strip(), reporter_ip_hash)
        )
        await db.commit()
        return {"success": True, "message": "Report submitted for moderation review."}

async def get_admin_reports() -> List[Dict[str, Any]]:
    """Retrieve pending moderation reports with target context."""
    async with get_db() as db:
        async with db.execute(
            """
            SELECT * FROM reports 
            ORDER BY created_at DESC 
            LIMIT 50
            """
        ) as cursor:
            reports = [dict(r) for r in await cursor.fetchall()]

        enriched_reports = []
        for r in reports:
            if r["target_type"] == "profile":
                async with db.execute("SELECT name, slug, status FROM profiles WHERE id = ?", (r["target_id"],)) as c:
                    p = await c.fetchone()
                    r["target_title"] = f"Profile: {p['name']}" if p else "Deleted Profile"
                    r["target_slug"] = p["slug"] if p else ""
            else:
                async with db.execute("SELECT headline, content, status FROM reviews WHERE id = ?", (r["target_id"],)) as c:
                    rev = await c.fetchone()
                    r["target_title"] = f"Review: {rev['headline']}" if rev else "Deleted Review"
                    r["target_content"] = rev["content"] if rev else ""
            enriched_reports.append(r)
        return enriched_reports

async def resolve_report(report_id: int, action: str) -> Dict[str, Any]:
    """Admin action to dismiss report or hide flagged content."""
    async with get_db() as db:
        async with db.execute("SELECT * FROM reports WHERE id = ?", (report_id,)) as cursor:
            report = await cursor.fetchone()
            if not report:
                return {"success": False, "message": "Report not found"}

        if action == "hide":
            if report["target_type"] == "profile":
                await db.execute("UPDATE profiles SET status = 'hidden' WHERE id = ?", (report["target_id"],))
            else:
                await db.execute("UPDATE reviews SET status = 'hidden' WHERE id = ?", (report["target_id"],))
            await db.execute("UPDATE reports SET status = 'resolved_hidden' WHERE id = ?", (report_id,))
        else:
            await db.execute("UPDATE reports SET status = 'resolved_dismissed' WHERE id = ?", (report_id,))

        await db.commit()
        return {"success": True, "action": action}

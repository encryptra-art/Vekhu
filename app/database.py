"""
PULSE Database Module
Asynchronous SQLite connection, schema definition, and seed data initialization.
"""

import aiosqlite
import json
import hashlib
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "pulse.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    bio TEXT NOT NULL,
    avatar_url TEXT NOT NULL,
    external_links TEXT DEFAULT '[]',
    is_verified INTEGER DEFAULT 0,
    rating_count INTEGER DEFAULT 0,
    average_rating REAL DEFAULT 0.0,
    distribution TEXT DEFAULT '{"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    perspective_context TEXT NOT NULL,
    headline TEXT NOT NULL,
    content TEXT NOT NULL,
    author_alias TEXT DEFAULT 'Anonymous Observer',
    ip_hash TEXT NOT NULL,
    session_token TEXT NOT NULL,
    helpful_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'published',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_type TEXT NOT NULL,
    target_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    details TEXT,
    reporter_ip_hash TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,
    voter_token TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(review_id, voter_token)
);

CREATE INDEX IF NOT EXISTS idx_profiles_slug ON profiles(slug);
CREATE INDEX IF NOT EXISTS idx_profiles_category ON profiles(category);
CREATE INDEX IF NOT EXISTS idx_reviews_profile ON reviews(profile_id);
"""

INITIAL_PROFILES = [
    {
        "slug": "sam-altman",
        "name": "Sam Altman",
        "title": "CEO, OpenAI & Tech Entrepreneur",
        "category": "Tech & Founders",
        "bio": "Central figure in the global artificial intelligence race. Co-founded OpenAI, formerly President of Y Combinator, and investor across fusion, longevity, and compute infrastructure.",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80",
        "external_links": json.dumps([
            {"label": "X / Twitter", "url": "https://x.com/sama"},
            {"label": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Sam_Altman"}
        ]),
        "is_verified": 1,
        "seed_reviews": [
            {
                "rating": 5,
                "perspective_context": "Industry Peer / Collaborator",
                "headline": "Visionary execution engine of our generation",
                "content": "Regardless of media narratives, Sam is uniquely gifted at galvanizing the highest-caliber talent, securing incomprehensible capital, and directing it toward seismic technological breakthroughs.",
                "author": "Tech Founder"
            },
            {
                "rating": 3,
                "perspective_context": "Critical Reader / Observer",
                "headline": "Brilliant operator, but corporate pivot raised alarms",
                "content": "His ability to ship is undeniable. However, the transition from a non-profit safety mission into a hyper-aggressive commercial powerhouse left legitimate transparency questions.",
                "author": "AI Researcher"
            },
            {
                "rating": 4,
                "perspective_context": "Long-time Observer",
                "headline": "One of the few people executing on sovereign compute",
                "content": "Followed his essays since YC days. He thinks in decades while most tech executives think in quarterly earnings reports. Deeply ambitious.",
                "author": "Venture Observer"
            },
            {
                "rating": 2,
                "perspective_context": "Critical Reader / Observer",
                "headline": "Overselling timelines and shifting governance",
                "content": "Public communication alternates between techno-messianic optimism and apocalyptic caution. The governance crisis showed vulnerability in accountability.",
                "author": "Tech Ethics Analyst"
            }
        ]
    },
    {
        "slug": "mkbhd",
        "name": "Marques Brownlee",
        "title": "Creator, Tech Reviewer & Founder, MKBHD",
        "category": "Creators & Media",
        "bio": "Premier technology reviewer with over 15 years of consumer hardware criticism. Known for unmatched visual production standards, meticulous testing, and ultimate Frisbee championship play.",
        "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80",
        "external_links": json.dumps([
            {"label": "YouTube", "url": "https://youtube.com/mkbhd"},
            {"label": "X / Twitter", "url": "https://x.com/MKBHD"}
        ]),
        "is_verified": 1,
        "seed_reviews": [
            {
                "rating": 5,
                "perspective_context": "Long-time Observer",
                "headline": "The gold standard of objective hardware criticism",
                "content": "When Marques reviews a smartphone or EV, manufacturers pay attention. His honest teardown of undercooked gadgets has repeatedly protected consumers from overhyped hardware.",
                "author": "Hardware Enthusiast"
            },
            {
                "rating": 5,
                "perspective_context": "Long-time Observer",
                "headline": "Unmatched production aesthetics and consistency",
                "content": "More than just tech reviews; his studio is an absolute clinic in visual hierarchy, lighting, and pacing. Never sold out his credibility.",
                "author": "Cinematographer"
            },
            {
                "rating": 4,
                "perspective_context": "Direct Interaction",
                "headline": "Extremely gracious and disciplined professional",
                "content": "Met him at a press briefing. Completely humble, deeply knowledgeable, and treats his crew and audience with genuine respect.",
                "author": "Press Colleague"
            }
        ]
    },
    {
        "slug": "paul-graham",
        "name": "Paul Graham",
        "title": "Essayist, Programmer & Co-Founder, Y Combinator",
        "category": "Thinkers & Authors",
        "bio": "Created Viaweb, co-founded Y Combinator, and authored seminal essays on startups, hacking, philosophy, and societal progress that shaped modern venture creation.",
        "avatar_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=600&q=80",
        "external_links": json.dumps([
            {"label": "Personal Website", "url": "https://paulgraham.com"},
            {"label": "X / Twitter", "url": "https://x.com/paulg"}
        ]),
        "is_verified": 1,
        "seed_reviews": [
            {
                "rating": 5,
                "perspective_context": "Long-time Observer",
                "headline": "His essays literally reprogrammed how founders think",
                "content": "PG's writing is lucid, concise, and razor-sharp. 'Do Things that Don't Scale' and 'Maker's Schedule, Manager's Schedule' are permanent cultural canon for builders.",
                "author": "Bootstrapped Founder"
            },
            {
                "rating": 4,
                "perspective_context": "Critical Reader / Observer",
                "headline": "Brilliant on early-stage creation, occasionally sheltered on macro topics",
                "content": "Masterclass thinker on the psychology of hackers and small teams. His recent takes on global politics sometimes show a classic Silicon Valley bubble perspective, but his core wisdom remains unmatched.",
                "author": "Systems Architect"
            }
        ]
    },
    {
        "slug": "lex-fridman",
        "name": "Lex Fridman",
        "title": "Research Scientist & Host, Lex Fridman Podcast",
        "category": "Creators & Media",
        "bio": "Host of wide-ranging 3-to-5 hour intellectual dialogues with physicists, historians, political leaders, philosophers, and technologists. AI researcher affiliated with MIT.",
        "avatar_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80",
        "external_links": json.dumps([
            {"label": "Podcast", "url": "https://lexfridman.com/podcast"},
            {"label": "X / Twitter", "url": "https://x.com/lexfridman"}
        ]),
        "is_verified": 1,
        "seed_reviews": [
            {
                "rating": 5,
                "perspective_context": "Long-time Observer",
                "headline": "Brought long-form depth and empathy back to public discourse",
                "content": "In an era of 30-second TikTok outrage, Lex gives researchers and thinkers 4 hours to explain complex physics or historical nuance without soundbite interruptions.",
                "author": "Curious Student"
            },
            {
                "rating": 3,
                "perspective_context": "Critical Reader / Observer",
                "headline": "Great guests, but could push back harder on controversial claims",
                "content": "His ethos of radical empathy is admirable, but occasionally allows authoritarian or controversial figures to present unchecked monologues without rigorous journalistic friction.",
                "author": "Investigative Journalist"
            }
        ]
    },
    {
        "slug": "naval-ravikant",
        "name": "Naval Ravikant",
        "title": "Co-founder AngelList & Philosopher-Investor",
        "category": "Thinkers & Authors",
        "bio": "Early investor in Twitter, Uber, and dozens of category-defining tech companies. Renowned for pithy aphorisms on specific knowledge, leverage, accountability, and mental peace.",
        "avatar_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=600&q=80",
        "external_links": json.dumps([
            {"label": "Naval Aphorisms", "url": "https://nav.al"},
            {"label": "X / Twitter", "url": "https://x.com/naval"}
        ]),
        "is_verified": 1,
        "seed_reviews": [
            {
                "rating": 5,
                "perspective_context": "Long-time Observer",
                "headline": "Distilled modern leverage better than any business school",
                "content": "His 'How to Get Rich Without Getting Lucky' storm was a masterclass in modern economic reality. Code and media as permissionless leverage changed millions of careers.",
                "author": "Solo Capitalist"
            },
            {
                "rating": 4,
                "perspective_context": "Critical Reader / Observer",
                "headline": "Deeply inspiring, though sometimes detached from working-class realities",
                "content": "Incredible mental models for intellectual sovereignty. Easy to preach 'peace of mind' with hundreds of millions in capital, but the philosophical foundation is still immensely valuable.",
                "author": "Product Strategist"
            }
        ]
    }
]

from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db():
    """Asynchronous context manager for SQLite database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON;")
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()

        # Check if profiles exist; if not, seed
        async with db.execute("SELECT COUNT(*) FROM profiles") as cursor:
            count = (await cursor.fetchone())[0]

        if count == 0:
            for p in INITIAL_PROFILES:
                seed_reviews = p.get("seed_reviews", [])
                total_ratings = len(seed_reviews)
                dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                total_score = 0
                for r in seed_reviews:
                    rating = r["rating"]
                    dist[rating] += 1
                    total_score += rating
                avg_rating = round(total_score / total_ratings, 1) if total_ratings > 0 else 0.0

                cursor = await db.execute(
                    """
                    INSERT INTO profiles (slug, name, title, category, bio, avatar_url, external_links, is_verified, rating_count, average_rating, distribution)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        p["slug"],
                        p["name"],
                        p["title"],
                        p["category"],
                        p["bio"],
                        p["avatar_url"],
                        p["external_links"],
                        p["is_verified"],
                        total_ratings,
                        avg_rating,
                        json.dumps({str(k): v for k, v in dist.items()})
                    )
                )
                profile_id = cursor.lastrowid

                # Insert reviews
                for r in seed_reviews:
                    fake_ip_hash = hashlib.sha256(f"seed-{p['slug']}-{r['author']}".encode()).hexdigest()
                    await db.execute(
                        """
                        INSERT INTO reviews (profile_id, rating, perspective_context, headline, content, author_alias, ip_hash, session_token, helpful_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            profile_id,
                            r["rating"],
                            r["perspective_context"],
                            r["headline"],
                            r["content"],
                            r["author"],
                            fake_ip_hash,
                            "seed-session",
                            4
                        )
                    )
            await db.commit()

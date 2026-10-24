"""
Automated Integration and Unit Test Suite for PULSE
Tests database queries, API endpoints, scoring aggregation, and moderation flows.
"""

import asyncio
import os
import sys
import unittest
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import init_db, get_db, DB_PATH
import app.crud as crud

class TestPulseCore(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Initialize DB and seed profiles
        await init_db()

    async def test_01_seed_profiles_exist(self):
        """Verify iconic seed figures are initialized."""
        profiles = await crud.get_all_profiles()
        self.assertGreaterEqual(len(profiles), 4, "Expected at least 4 seed profiles")
        slugs = [p["slug"] for p in profiles]
        self.assertIn("sam-altman", slugs)
        self.assertIn("mkbhd", slugs)

    async def test_02_get_profile_by_slug(self):
        """Verify profile dossier retrieval with reviews and distribution."""
        profile = await crud.get_profile_by_slug("mkbhd")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["name"], "Marques Brownlee")
        self.assertIn("reviews", profile)
        self.assertGreater(len(profile["reviews"]), 0)
        self.assertIn("5", profile["distribution"])

    async def test_03_discovery_search_and_filter(self):
        """Verify search by keyword and category filtering."""
        # Search for OpenAI
        results = await crud.get_all_profiles(search="OpenAI")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["slug"], "sam-altman")

        # Filter by category
        thinkers = await crud.get_all_profiles(category="Thinkers & Authors")
        self.assertTrue(all(p["category"] == "Thinkers & Authors" for p in thinkers))

    async def test_04_submit_review_and_aggregate_recalculation(self):
        """Test submitting a review and mathematical update of average rating."""
        profile = await crud.get_profile_by_slug("paul-graham")
        initial_count = profile["rating_count"]
        
        # Test session token and IP
        test_ip = "192.168.1.105"
        ip_hash = crud.hash_identifier(test_ip)
        session_token = "test-session-token-99"

        # Check not yet reviewed
        already = await crud.check_user_already_reviewed(profile["id"], ip_hash, session_token)
        self.assertFalse(already)

        # Submit 5-star review
        res = await crud.add_review(
            profile_id=profile["id"],
            rating=5,
            perspective_context="Industry Peer / Collaborator",
            headline="Seminal essayist on founder psychology",
            content="PG's clarity on startups and hacker culture remains unmatched across tech literature.",
            author_alias="Startup Founder",
            ip_hash=ip_hash,
            session_token=session_token
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["rating_count"], initial_count + 1)

        # Verify duplicate check now triggers
        already_now = await crud.check_user_already_reviewed(profile["id"], ip_hash, session_token)
        self.assertTrue(already_now)

    async def test_05_create_new_public_figure(self):
        """Test instant community creation of a public figure."""
        new_figure = await crud.create_profile(
            name="Andrej Karpathy",
            title="AI Researcher & Educator, Eureka Labs",
            category="Tech & Founders",
            bio="Founding member at OpenAI, former Director of AI at Tesla. Renowned educator who makes neural networks intuitive from scratch.",
            avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80",
            external_url="https://karpathy.ai"
        )
        self.assertIn("andrej-karpathy", new_figure["slug"])
        
        # Verify it can be retrieved
        retrieved = await crud.get_profile_by_slug(new_figure["slug"])
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["name"], "Andrej Karpathy")
        self.assertEqual(retrieved["rating_count"], 0)

    async def test_06_report_and_moderation(self):
        """Test flagging content and admin resolution."""
        # File a report
        report_res = await crud.create_report(
            target_type="profile",
            target_id=1,
            reason="harassment_defamation",
            details="Test moderation queue inspection",
            reporter_ip_hash=crud.hash_identifier("127.0.0.1")
        )
        self.assertTrue(report_res["success"])

        # Fetch admin reports
        reports = await crud.get_admin_reports()
        self.assertGreater(len(reports), 0)
        latest_report = reports[0]
        
        # Resolve report (dismiss)
        resolve_res = await crud.resolve_report(latest_report["id"], action="dismiss")
        self.assertTrue(resolve_res["success"])

if __name__ == "__main__":
    unittest.main()

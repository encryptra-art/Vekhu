# PULSE — The Real-Time Public Perception Index

> **A world-class, psychology-driven social platform where people rate, review, and discover collective sentiment around public figures, creators, founders, and cultural leaders.**

---

## 1. Executive Summary & Design North Star

Traditional social networks reward polarizing outrage, flattening nuanced reputations into 280-character toxic battles or superficial follower counts. **PULSE** is an architectural and editorial perception ledger designed to measure, contextualize, and track how influential individuals are truly perceived by their audience and peers.

### Creative North Star
Rooted in the visual sophistication of warm tactile minimalism:
* **Backgrounds:** Warm bone (`#FAF7F2`) and sandstone surfaces (`#F2EFE9`).
* **Typography:** Deep obsidian charcoal (`#121212`) pairing editorial display faces with ultra-legible modern geometric sans.
* **Kinetic Accent:** Luminous solar orange (`#FF5E1E`) representing active cultural pulse and real-time community heat.
* **Sculptural Composition:** Floating frosted panels, rounded pill geometry, and atmospheric ambient glowing spheres that balance digital precision with organic warmth.

---

## 2. Core Psychological & Structural Innovations

1. **The 5-Star Distribution Curve (Anti-Flattening Histogram):**
   * Instead of hiding reality behind an arbitrary 3.2 mean, PULSE plots the full distribution curve across all 5 stars. Users instantly see whether a public figure enjoys unanimous reverence or sparks intense bimodal controversy.
2. **Perspective Context Tagging:**
   * Reviewers tag their point of view (*Direct Interaction*, *Industry Peer / Collaborator*, *Long-time Observer*, *Critical Reader / Audience*). This elevates reviews from generic hot-takes to contextualized insights.
3. **Zero-Friction Anonymous Candor:**
   * Removes the intimidation of mandatory social logins that discourage speaking truth to power. Submissions are secured via salt-hashed IP fingerprints, browser session tokens, and duplicate vote restrictions.
4. **Instant Public Figure Creation + Community Post-Moderation:**
   * Any user can instantly index a public figure (name, role, category, bio, links, and avatar). Community members can flag any non-public individual for immediate moderator review and removal.
5. **Shareable "Pulse Perception Cards":**
   * Instant HTML5 canvas rendering produces export-ready, high-resolution social preview cards formatted for Twitter/X, LinkedIn, and Instagram stories to power organic viral loops.

---

## 3. Architecture & Technical Stack

* **Backend Framework:** FastAPI (Python 3.13)
* **ASGI Server:** Uvicorn with auto-reload
* **Database:** SQLite (`aiosqlite`) with asynchronous schema initialization, index optimization, foreign key enforcement, and mathematical aggregation
* **Design & Styling:** Tailwind CSS Design Tokens + Custom Tactile CSS (`custom.css`)
* **Templates:** Jinja2 with responsive components, accessible modal dialogs, and toast notifications
* **Client Logic:** Modern Vanilla JS with localStorage session persistence, dynamic canvas perception card generation, and live form validation

---

## 4. Key Routes & Endpoints

### Web Pages
| Route | Description |
|---|---|
| `/` | Landing page featuring editorial hero, live consensus, and featured figures |
| `/discover` | Search and discovery directory with category pills and sort filters |
| `/profile/{slug}` | Full perception dossier, 5-star histogram, context-tagged reviews, and card exporter |
| `/create` | Instant public figure creation form with live interactive card preview |
| `/guidelines` | Platform integrity policies, Public Figure Doctrine, and anti-harassment rules |
| `/admin` | Moderation console for reviewing flags, managing profiles, and resolving reports |

### API Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/reviews` | Submit a rating with context tag, headline, and written perspective |
| `POST` | `/api/reviews/{id}/helpful` | Upvote a review perspective's helpfulness |
| `POST` | `/api/profiles` | Instantly publish a new public figure to the index |
| `POST` | `/api/reports` | File a moderation flag on a profile or review |
| `POST` | `/api/admin/reports/resolve` | Admin action to dismiss or hide reported content |

---

## 5. Running & Testing Locally

To start the PULSE server:

```bash
cd "C:\Users\Laptops collection\.gemini\antigravity\scratch\pulse"
& "C:\Users\Laptops collection\AppData\Local\Programs\Python\Python313\python.exe" run.py
```

Then visit:
👉 **`http://127.0.0.1:8000`** in your browser.

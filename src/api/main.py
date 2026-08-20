"""
Lead Lists API — FastAPI Backend
Scrapes public business directories and compiles targeted lead lists.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3
import os
import uuid
import csv
import json
from datetime import datetime
from pathlib import Path

app = FastAPI(title="Lead Lists API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/leads.db")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/app/output/lists")
API_KEY = os.getenv("API_KEY", "change-me")

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)


# ─── Database Setup ───────────────────────────────────────────────

def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS scrape_jobs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            query TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            total_found INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            company_name TEXT,
            website TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            industry TEXT,
            employee_count TEXT,
            revenue TEXT,
            linkedin TEXT,
            notes TEXT,
            scraped_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES scrape_jobs(id)
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── Scraper Engine ──────────────────────────────────────────────

class ScraperEngine:
    """
    Multi-source scraper for public business directories.
    Uses BeautifulSoup + requests to scrape public data.
    """

    SOURCES = {
        "yellow_pages": {
            "name": "Yellow Pages",
            "base_url": "https://www.yellowpages.com/search",
            "enabled": True
        },
        "yelp": {
            "name": "Yelp",
            "base_url": "https://www.yelp.com/search",
            "enabled": True
        },
        "google_maps": {
            "name": "Google Maps",
            "base_url": "https://www.google.com/maps",
            "enabled": False  # Requires Places API key
        },
        "bbb": {
            "name": "Better Business Bureau",
            "base_url": "https://www.bbb.org/search",
            "enabled": True
        },
        "linkedin": {
            "name": "LinkedIn",
            "base_url": "https://www.linkedin.com/search/results/companies",
            "enabled": False  # Requires auth
        }
    }

    @staticmethod
    def scrape_yellow_pages(query: str, location: str = "", max_results: int = 50) -> list[dict]:
        """
        Scrape Yellow Pages for business listings.
        Public data, rate-limited to be respectful.
        """
        import requests
        from bs4 import BeautifulSoup
        import time

        leads = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        search_term = f"{query} {location}".strip()
        url = f"https://www.yellowpages.com/search?search_terms={requests.utils.quote(search_term)}"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            listings = soup.select(".result")[:max_results]

            for listing in listings:
                try:
                    name_elem = listing.select_one(".business-name")
                    phone_elem = listing.select_one(".phone")
                    address_elem = listing.select_one(".street-address")
                    city_elem = listing.select_one(".locality")
                    website_elem = listing.select_one(".track-visit-website")

                    lead = {
                        "company_name": name_elem.get_text(strip=True) if name_elem else "",
                        "website": website_elem["href"] if website_elem and website_elem.has_attr("href") else "",
                        "phone": phone_elem.get_text(strip=True) if phone_elem else "",
                        "address": address_elem.get_text(strip=True) if address_elem else "",
                        "city": city_elem.get_text(strip=True).replace(",", "").strip() if city_elem else "",
                        "industry": query,
                        "source": "yellow_pages"
                    }

                    if lead["company_name"]:
                        leads.append(lead)

                    # Rate limiting
                    time.sleep(0.5)

                except Exception as e:
                    continue

        except Exception as e:
            print(f"Yellow Pages scrape error: {e}")

        return leads

    @staticmethod
    def scrape_yelp(query: str, location: str = "", max_results: int = 30) -> list[dict]:
        """
        Scrape Yelp for business listings.
        Public data from search results.
        """
        import requests
        from bs4 import BeautifulSoup
        import time

        leads = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        search_term = f"{query} {location}".strip()
        url = f"https://www.yelp.com/search?find_desc={requests.utils.quote(search_term)}"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            containers = soup.select("[data-testid='serp-ia-card']")[:max_results]

            for container in containers:
                try:
                    name_elem = container.css.select_one("a.css-19v1rkv")
                    phone_elem = container.css.select_one("p.css-1p9ibgf")
                    address_elem = container.css.select_one("p.css-1p9ibgf ~ p.css-1p9ibgf")

                    lead = {
                        "company_name": name_elem.get_text(strip=True) if name_elem else "",
                        "website": "",
                        "phone": phone_elem.get_text(strip=True) if phone_elem else "",
                        "address": address_elem.get_text(strip=True) if address_elem else "",
                        "city": location,
                        "industry": query,
                        "source": "yelp"
                    }

                    if lead["company_name"]:
                        leads.append(lead)

                    time.sleep(0.5)

                except Exception:
                    continue

        except Exception as e:
            print(f"Yelp scrape error: {e}")

        return leads

    @staticmethod
    def scrape_bbb(query: str, location: str = "", max_results: int = 30) -> list[dict]:
        """
        Scrape Better Business Bureau for business listings.
        """
        import requests
        from bs4 import BeautifulSoup
        import time

        leads = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        search_term = f"{query} {location}".strip()
        url = f"https://www.bbb.org/search?find_text={requests.utils.quote(search_term)}"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            listings = soup.select(".result-item")[:max_results]

            for listing in listings:
                try:
                    name_elem = listing.select_one(".org-name")
                    phone_elem = listing.select_one(".phone")
                    address_elem = listing.select_one(".address")

                    lead = {
                        "company_name": name_elem.get_text(strip=True) if name_elem else "",
                        "website": "",
                        "phone": phone_elem.get_text(strip=True) if phone_elem else "",
                        "address": address_elem.get_text(strip=True) if address_elem else "",
                        "city": location,
                        "industry": query,
                        "source": "bbb"
                    }

                    if lead["company_name"]:
                        leads.append(lead)

                    time.sleep(0.5)

                except Exception:
                    continue

        except Exception as e:
            print(f"BBB scrape error: {e}")

        return leads


# ─── API Models ──────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    query: str = Field(..., description="Search query (e.g., 'dentist', 'plumber')")
    location: str = Field("", description="Location filter (city, state, or zip)")
    sources: list[str] = Field(["yellow_pages", "yelp", "bbb"], description="Sources to scrape")
    max_results: int = Field(50, ge=10, le=200, description="Max results per source")
    job_name: Optional[str] = Field(None, description="Optional job name")


class ExportRequest(BaseModel):
    job_id: str
    format: str = Field("csv", description="Export format: csv or json")
    fields: Optional[list[str]] = Field(None, description="Specific fields to include")


# ─── API Endpoints ───────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "service": "Lead Lists API",
        "version": "1.0.0",
        "endpoints": {
            "POST /scrape": "Start a new scrape job",
            "GET /jobs": "List all scrape jobs",
            "GET /jobs/{id}": "Get job status and results",
            "GET /jobs/{id}/leads": "Get leads from a job",
            "POST /export": "Export leads to CSV/JSON",
            "GET /sources": "List available sources"
        }
    }


@app.get("/sources")
async def list_sources():
    """List all available scraping sources."""
    return {
        "sources": [
            {"id": k, "name": v["name"], "enabled": v["enabled"]}
            for k, v in ScraperEngine.SOURCES.items()
        ]
    }


@app.post("/scrape")
async def start_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Start a new scrape job in the background."""
    job_id = str(uuid.uuid4())

    # Register job in database
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO scrape_jobs (id, name, source, query, status) VALUES (?, ?, ?, ?, ?)",
        (
            job_id,
            request.job_name or f"{request.query} in {request.location}",
            ",".join(request.sources),
            f"{request.query}|{request.location}",
            "running"
        )
    )
    conn.commit()
    conn.close()

    # Run scrape in background
    background_tasks.add_task(run_scrape_job, job_id, request)

    return {
        "job_id": job_id,
        "status": "running",
        "message": f"Scraping {', '.join(request.sources)} for '{request.query}'"
    }


async def run_scrape_job(job_id: str, request: ScrapeRequest):
    """Execute scrape job in background."""
    scraper = ScraperEngine()
    all_leads = []

    # Scrape each source
    for source in request.sources:
        if source not in ScraperEngine.SOURCES or not ScraperEngine.SOURCES[source]["enabled"]:
            continue

        try:
            if source == "yellow_pages":
                leads = scraper.scrape_yellow_pages(request.query, request.location, request.max_results)
            elif source == "yelp":
                leads = scraper.scrape_yelp(request.query, request.location, request.max_results)
            elif source == "bbb":
                leads = scraper.scrape_bbb(request.query, request.location, request.max_results)
            else:
                leads = []

            all_leads.extend(leads)

        except Exception as e:
            print(f"Error scraping {source}: {e}")

    # Deduplicate by company name
    seen = set()
    unique_leads = []
    for lead in all_leads:
        key = lead.get("company_name", "").lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique_leads.append(lead)

    # Store in database
    conn = get_db()
    c = conn.cursor()

    for lead in unique_leads:
        lead_id = str(uuid.uuid4())
        c.execute(
            """INSERT INTO leads 
               (id, job_id, company_name, website, email, phone, address, city, industry, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                lead_id,
                job_id,
                lead.get("company_name", ""),
                lead.get("website", ""),
                lead.get("email", ""),
                lead.get("phone", ""),
                lead.get("address", ""),
                lead.get("city", ""),
                lead.get("industry", ""),
                f"Source: {lead.get('source', 'unknown')}"
            )
        )

    # Update job status
    c.execute(
        "UPDATE scrape_jobs SET status = ?, total_found = ?, completed_at = ? WHERE id = ?",
        ("completed", len(unique_leads), datetime.utcnow().isoformat(), job_id)
    )

    conn.commit()
    conn.close()

    # Generate CSV export
    await export_to_csv(job_id, unique_leads)


async def export_to_csv(job_id: str, leads: list[dict]):
    """Export leads to CSV file."""
    if not leads:
        return

    filepath = Path(OUTPUT_DIR) / f"{job_id}.csv"

    fieldnames = ["company_name", "website", "email", "phone", "address", "city", "industry", "source"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(leads)


@app.get("/jobs")
async def list_jobs():
    """List all scrape jobs."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM scrape_jobs ORDER BY created_at DESC")
    jobs = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"jobs": jobs}


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job status and results."""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM scrape_jobs WHERE id = ?", (job_id,))
    job = c.fetchone()
    if not job:
        conn.close()
        raise HTTPException(status_code=404, detail="Job not found")

    c.execute("SELECT * FROM leads WHERE job_id = ?", (job_id,))
    leads = [dict(row) for row in c.fetchall()]
    conn.close()

    result = dict(job)
    result["leads"] = leads
    return result


@app.get("/jobs/{job_id}/leads")
async def get_job_leads(job_id: str, limit: int = 100, offset: int = 0):
    """Get leads from a specific job with pagination."""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as total FROM leads WHERE job_id = ?", (job_id,))
    total = c.fetchone()["total"]

    c.execute(
        "SELECT * FROM leads WHERE job_id = ? ORDER BY scraped_at DESC LIMIT ? OFFSET ?",
        (job_id, limit, offset)
    )
    leads = [dict(row) for row in c.fetchall()]
    conn.close()

    return {"total": total, "limit": limit, "offset": offset, "leads": leads}


@app.post("/export")
async def export_leads(request: ExportRequest):
    """Export leads to CSV or JSON file."""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM leads WHERE job_id = ?", (request.job_id,))
    leads = [dict(row) for row in c.fetchall()]
    conn.close()

    if not leads:
        raise HTTPException(status_code=404, detail="No leads found for this job")

    # Filter fields if specified
    if request.fields:
        leads = [{k: v for k, v in lead.items() if k in request.fields} for lead in leads]

    job = get_job(request.job_id)
    filename = f"lead_list_{request.job_id[:8]}.{request.format}"
    filepath = Path(OUTPUT_DIR) / filename

    if request.format == "csv":
        fieldnames = request.fields or ["company_name", "website", "email", "phone", "address", "city", "industry"]
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(leads)
    elif request.format == "json":
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2, default=str)
    else:
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")

    return {
        "download_url": f"/download/{filename}",
        "lead_count": len(leads),
        "file_path": str(filepath)
    }


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download an exported file."""
    filepath = Path(OUTPUT_DIR) / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream"
    )


@app.get("/stats")
async def get_stats():
    """Get overall statistics."""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as total FROM leads")
    total_leads = c.fetchone()["total"]

    c.execute("SELECT COUNT(*) as total FROM scrape_jobs WHERE status = 'completed'")
    completed_jobs = c.fetchone()["total"]

    c.execute("SELECT COUNT(*) as total FROM scrape_jobs WHERE status = 'running'")
    running_jobs = c.fetchone()["total"]

    c.execute("SELECT city, COUNT(*) as count FROM leads GROUP BY city ORDER BY count DESC LIMIT 10")
    top_cities = [{"city": row["city"], "count": row["count"]} for row in c.fetchall()]

    c.execute("SELECT industry, COUNT(*) as count FROM leads GROUP BY industry ORDER BY count DESC LIMIT 10")
    top_industries = [{"industry": row["industry"], "count": row["count"]} for row in c.fetchall()]

    conn.close()

    return {
        "total_leads": total_leads,
        "completed_jobs": completed_jobs,
        "running_jobs": running_jobs,
        "top_cities": top_cities,
        "top_industries": top_industries
    }


# ─── Startup ─────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    init_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

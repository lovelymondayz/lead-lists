# Lead Lists Service

**Revenue Idea #1: Done-For-You Lead Lists**
**Pricing:** $50-200 per list
**Status:** Prototype — ready for deployment

---

## What It Does

Scrapes public business directories (Yellow Pages, Yelp, Better Business Bureau) to compile targeted lead lists. Deduplicates, cleans, and exports to CSV/Excel.

## How It Works

1. User enters a keyword (e.g., "dentist") and optional location
2. System scrapes multiple public directories in parallel
3. Results are deduplicated and stored in SQLite
4. Users can view leads in the dashboard and export to CSV/Excel

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Dashboard   │────▶│  FastAPI      │────▶│  SQLite DB      │
│  (React)     │     │  Backend      │     │  (leads.db)     │
└─────────────┘     └──────────────┘     └─────────────────┘
                            │
                            ▼
                    ┌──────────────────┐
                    │  Scraper Engine   │
                    │  - Yellow Pages   │
                    │  - Yelp           │
                    │  - BBB            │
                    └──────────────────┘
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/health` | GET | Health check |
| `/sources` | GET | List available scrapers |
| `/scrape` | POST | Start a new scrape job |
| `/jobs` | GET | List all jobs |
| `/jobs/{id}` | GET | Get job details + leads |
| `/jobs/{id}/leads` | GET | Get paginated leads |
| `/export` | POST | Export leads to CSV/JSON |
| `/download/{filename}` | GET | Download exported file |
| `/stats` | GET | Get overall statistics |

## Quick Start

```bash
# Clone
git clone https://github.com/lovelymondayz/lead-lists.git
cd lead-lists

# Configure
cp .env.example .env
# Edit .env with your settings

# Run with Docker Compose
docker compose build --no-cache
docker compose up -d

# Check health
curl http://localhost:8091/health

# Open dashboard
open http://localhost:8092
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | Secret API key | Required |
| `DATABASE_PATH` | SQLite database path | `/app/data/leads.db` |
| `OUTPUT_DIR` | Export directory | `/app/output/lists` |
| `SCRAPER_RATE_LIMIT` | Delay between requests (seconds) | `1.0` |
| `SCRAPER_TIMEOUT` | Request timeout (seconds) | `30` |
| `MAX_RESULTS_PER_SOURCE` | Max results per source | `50` |

## Adding New Scrapers

1. Add source to `ScraperEngine.SOURCES` dict in `src/api/main.py`
2. Implement a new `scrape_{source_name}()` method
3. Register in the `/scrape` endpoint handler
4. Push to GitHub — webhook auto-deploys

## Revenue Strategy

**Product:** Done-for-you lead lists
**Pricing:** $50-200 per list (depending on size/niche)
**Target:** Local businesses, recruiters, sales teams

### Sales Play
1. Use the dashboard to scrape leads for a specific niche
2. Export and clean the list
3. Sell to businesses that need leads (B2B)
4. Example: "500 dentist offices in Jakarta — $150"

### Upsells
- Recurring weekly/monthly lead refreshes ($100-300/month)
- Custom targeting (specific cities, industries, company sizes)
- Email append service (find emails for existing lists)

## Roadmap

- [x] Basic scraper engine (Yellow Pages, Yelp, BBB)
- [x] React dashboard
- [x] CSV/JSON export
- [x] SQLite storage
- [x] Docker Compose setup
- [ ] Email finder integration (Hunter.io, etc.)
    - [ ] CRM integrations (HubSpot, Salesforce)
- [ ] Automated delivery (email lists to clients)
- [ ] Payment integration (Midtrans/Xendit)

## Related

- **Pipeline Goal #1:** Lead gen (scout biz with no/bad website)
- **Portfolio:** client.arjism.com
- **Motto:** "Burn VPS, Not Tokens."

## License

MIT

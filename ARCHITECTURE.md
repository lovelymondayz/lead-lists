# lead-lists

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        lead-lists                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Client     │───▶│   FastAPI   │───▶│  Services   │     │
│  │  (HTTP/REST) │    │   (8091)    │    │  (Business) │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                              │                    │         │
│                              ▼                    ▼         │
│                       ┌─────────────┐    ┌─────────────┐   │
│                       │   SQLite    │    │  External   │   │
│                       │   (db)      │    │   APIs      │   │
│                       └─────────────┘    └─────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Server | Uvicorn |
| Database | SQLite |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Testing | pytest |
| Containerization | Docker |

## Design Decisions

- **FastAPI**: Async support, automatic OpenAPI docs, Pydantic validation
- **SQLite**: Lightweight, file-based database suitable for lead data
- **Service Layer**: Separates business logic from API routes
- **Rate Limiting**: Configurable scraper rate limit to respect target servers
- **Async Scraping**: Non-blocking I/O for concurrent lead collection

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/leads` | List all leads |
| GET | `/leads/{id}` | Get lead by ID |
| POST | `/leads` | Create new lead |
| PUT | `/leads/{id}` | Update lead |
| DELETE | `/leads/{id}` | Delete lead |
| POST | `/scrape` | Trigger lead scraping |
| GET | `/scrape/status` | Get scraping status |
| GET | `/export` | Export leads to CSV |
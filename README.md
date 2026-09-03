# lead-lists

API service for collecting, managing, and exporting lead lists with configurable scraping.

## Quick Start

```bash
# Development
make dev

# Docker
make up

# View logs
make logs
```

## Features

- Lead collection and management
- Configurable scraper with rate limiting
- CSV export functionality
- RESTful API with OpenAPI documentation
- SQLite database for lightweight storage

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

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API authentication key | - |
| `DATABASE_PATH` | SQLite database file path | `./data/leads.db` |
| `OUTPUT_DIR` | Export output directory | `./output` |
| `SCRAPER_RATE_LIMIT` | Max requests per second | `10` |
| `SCRAPER_TIMEOUT` | Request timeout in seconds | `30` |

## Deployment

```bash
# Build and deploy with Docker Compose
make deploy

# Or manually
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8091/docs
- ReDoc: http://localhost:8091/redoc
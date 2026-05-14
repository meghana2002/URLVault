# URLVault

**HTTP Metadata Inventory Service** — collects and stores HTTP metadata (headers, cookies, page source) for any URL in MongoDB.

Built with **FastAPI**, **Motor** (async MongoDB driver), and **httpx**.

---

## Features

- **Synchronous collection** — `POST` a URL and get back headers, cookies, and page source immediately.
- **Async background collection** — `GET` a URL; if it's not cached, collection is scheduled in the background and a `202 Accepted` response is returned.
- **MongoDB persistence** — all metadata is stored with upsert semantics (re-fetching refreshes the record).
- **Health endpoint** — includes a live MongoDB ping for readiness probes.
- **12-Factor configuration** — all settings sourced from environment variables / `.env` file via Pydantic Settings.
- **Fully async** — end-to-end async I/O with `httpx` and `motor`.

---

## Tech Stack

| Layer         | Technology               |
|---------------|--------------------------|
| Framework     | FastAPI 0.115            |
| HTTP Client   | httpx 0.27               |
| Database      | MongoDB 7.0 (via Motor)  |
| Validation    | Pydantic v2              |
| Testing       | pytest + pytest-asyncio  |
| Linting       | Ruff                     |
| Runtime       | Python 3.11+             |

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/meghana2002/URLVault.git
cd URLVault
```

### 2. Create an `.env` file

```bash
cp .env.example .env
```

### 3. Run with Docker Compose

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

---

## API Reference

### Health Check

```http
GET /health
```

Returns service and database status.

---

### Collect Metadata (Sync)

```http
POST /api/v1/metadata
Content-Type: application/json
```

Request body:

```json
{
  "url": "https://example.com"
}
```

#### Responses

##### `201 Created`

Returns the collected metadata record.

##### `502 Bad Gateway`

The target URL could not be reached.

---

### Get Metadata (Async)

```http
GET /api/v1/metadata?url=https://example.com
```

#### Responses

##### `200 OK`

Record found, returns metadata.

##### `202 Accepted`

URL not in inventory; background collection has been scheduled.

---

## Interactive Docs

FastAPI auto-generates interactive documentation:

- Swagger UI → http://localhost:8000/docs
- ReDoc → http://localhost:8000/redoc

---

## Configuration

All settings are controlled via environment variables
(see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| APP_NAME | urlvault | Application name |
| APP_ENV | development | development / staging / production / test |
| LOG_LEVEL | INFO | Logging level |
| MONGO_URI | mongodb://mongo:27017 | MongoDB connection string |
| MONGO_DB | metadata_inventory | Database name |
| MONGO_COLLECTION | metadata | Collection name |
| MONGO_MAX_POOL_SIZE | 50 | Max MongoDB connection pool size |
| HTTP_TIMEOUT_SECONDS | 15 | Timeout for outgoing HTTP requests |
| HTTP_MAX_REDIRECTS | 5 | Max redirects to follow |
| HTTP_USER_AGENT | URLVaultBot/1.0 | User-Agent header for requests |
| API_V1_PREFIX | /api/v1 | API route prefix |
| STARTUP_RETRY_SECONDS | 30 | DB connection retry window on start |

---

## Development

### Local Setup (without Docker)

#### Create a virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

#### Install dependencies

```bash
pip install ".[dev]"
```

#### Start local MongoDB

```bash
docker run -d --name mongo -p 27017:27017 mongo:7.0
```

#### Set environment variable

```bash
export MONGO_URI=mongodb://localhost:27017
```

#### Run the application

```bash
uvicorn app.main:app --reload
```

---

## Running Tests

```bash
pytest
```

Tests use:
- `mongomock-motor` for in-memory MongoDB mocking
- `respx` for HTTP request mocking

No running database is required for tests.

### With coverage

```bash
pytest --cov=app
```

---

## Project Structure

```text
URLVault/
├── app/
│   ├── api/            # FastAPI routers & dependencies
│   ├── core/           # Cross-cutting concerns (logging, exceptions)
│   ├── db/             # MongoDB connection & index management
│   ├── models/         # Pydantic schemas
│   ├── repositories/   # Data-access layer
│   ├── services/       # Business logic
│   ├── config.py       # Pydantic Settings configuration
│   └── main.py         # Application factory & lifespan
│
├── tests/              # Test suite
├── docker-compose.yml
├── Dockerfile
├── metadata_api_request.http
├── pyproject.toml
├── .env.example
└── README.md
```
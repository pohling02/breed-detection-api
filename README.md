# Breed Detection API

[![CI/CD](https://github.com/pohling02/pet-breed-api/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/pohling02/pet-breed-api/actions/workflows/ci-cd.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED)
![AWS](https://img.shields.io/badge/Deployed%20on-AWS%20EC2-FF9900)

A production-style REST API built with **FastAPI** that serves a custom **YOLOv8** model for dog and cat breed classification and dominant colour analysis.

Clients upload one or more images and receive breed predictions with confidence scores. The service is secured with hashed API keys, per-key rate limiting and strict file validation, and it logs every request to PostgreSQL. It was built as a standalone, reusable AI backend for the [Pet Adoption and Care System](https://github.com/pohling02/Pet-Adoption-and-Care-system) (Laravel), and is containerised with Docker and deployed to AWS EC2 through a GitHub Actions CI/CD pipeline.

**Live demo:** (http://3.24.69.32/docs) 

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Authentication](#authentication)
- [Endpoint: `POST /api/v1/predict`](#endpoint-post-apiv1predict)
- [Database Schema](#database-schema)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Deployment and CI/CD](#deployment-and-cicd)
- [Future Improvements](#future-improvements)

## Features

- **Breed detection:** classifies dog and cat breeds with a custom YOLOv8 model.
- **Colour extraction:** analyses images to return dominant colours as RGB values with a colour name.
- **Batch processing:** accepts up to 5 images per request and calculates a consensus prediction across them.
- **API key authentication:** keys are generated as secure random strings and stored only as SHA-256 hashes.
- **Rate limiting:** limits usage to 5 requests per minute per API key.
- **Payload validation:** accepts only JPEG, PNG and WEBP files of up to 5 MB each.
- **Telemetry:** logs API usage, response times and model inferences to PostgreSQL.
- **Database migrations:** schema changes are versioned with Alembic.
- **Interactive docs:** Swagger UI and ReDoc are generated automatically from OpenAPI.


## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | FastAPI (Python 3.11) |
| Machine learning | PyTorch, Ultralytics (YOLOv8), OpenCV |
| Database | PostgreSQL 16, SQLAlchemy (ORM), Psycopg, Alembic |
| Infrastructure | Docker, Docker Compose, AWS EC2 |
| CI/CD | GitHub Actions |
| Docs | Swagger UI / ReDoc (OpenAPI) |

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose
- Git

### 2. Clone and configure

```bash
git clone https://github.com/yourusername/pet-breed-api.git
cd pet-breed-api
```

Create a `.env` file in the project root. **Never commit this file.**

```bash
POSTGRES_USER=petapi
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=petbreed
```

### 3. Build and run

```bash
docker compose up -d --build
```

Apply the database migrations (replace `api` with your service name if it differs):

```bash
docker compose exec api alembic upgrade head
```

The API is now available at <http://localhost:8089>.

### 4. Create an API key

Protected endpoints need a valid key. Generate one with:

```bash
# Replace this with your project's actual key-creation command or script
docker compose exec api python scripts/create_api_key.py --name "my-first-key"
```

The plain-text key is shown only once, because only its SHA-256 hash is stored.

## API Documentation

When the containers are running, interactive documentation is available at:

- **Swagger UI:** <http://localhost:8089/docs>
- **ReDoc:** <http://localhost:8089/redoc>

## Authentication

Send your key in the request headers:

```
X-API-Key: your_api_key_here
```

## Endpoint: `POST /api/v1/predict`

### Request format

| Field | Details |
| --- | --- |
| Content-Type | `multipart/form-data` |
| `files` | 1 to 5 images, max 5 MB each. Allowed types: JPEG, PNG, WEBP |

### Example cURL

```bash
curl -X 'POST' \
  'http://localhost:8089/api/v1/predict' \
  -H 'accept: application/json' \
  -H 'X-API-Key: your_api_key_here' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@golden_retriever.jpg;type=image/jpeg'
```

### Example response

```json
{
  "success": true,
  "image_count": 1,
  "individual_results": [
    {
      "filename": "uuid-string.jpeg",
      "breed": {
        "prediction": "Golden Retriever",
        "confidence": 0.8608,
        "species": "Dog"
      },
      "colors": [
        {"color_name": "Tan", "rgb": [163, 151, 136], "percentage": 44.36}
      ]
    }
  ],
  "conclusion": {
    "breed": {
      "final_prediction": "Golden Retriever",
      "final_confidence": 0.8608,
      "final_species": "Dog"
    }
  }
}
```

## Database Schema

PostgreSQL stores three tables for access control and monitoring:

| Table | Purpose |
| --- | --- |
| `api_keys` | Hashed keys, active status and the `last_used_at` timestamp |
| `prediction_logs` | AI predictions, confidence scores and species data |
| `api_usages` | Every API request with its HTTP status code and response time in milliseconds |

## Error Handling

| Status | Meaning |
| --- | --- |
| `400 Bad Request` | Invalid file type, file larger than 5 MB, or image count limit exceeded |
| `401 Unauthorized` | Missing or invalid API key |
| `429 Too Many Requests` | API key exceeded 5 requests per minute |
| `500 Internal Server Error` | Unexpected server or model failure |

## Testing

Automated tests cover authentication, rate limiting, file validation and API responses.

```bash
pip install -r requirements.txt pytest
pytest -v
```

The same suite runs on every push and pull request in CI, against a real PostgreSQL service container.

## Deployment and CI/CD

The API runs on an **AWS EC2** instance using Docker Compose, with PostgreSQL kept on a private Docker network and not exposed to the internet.

Every push to `main` triggers the GitHub Actions pipeline in `.github/workflows/ci-cd.yml`:

1. **Test:** installs dependencies, applies Alembic migrations and runs the test suite.
2. **Build:** verifies that the Docker image builds, using the GitHub Actions layer cache.
3. **Deploy:** connects to the EC2 instance, pulls the latest code, rebuilds the containers and applies migrations.

Pull requests run the test and build steps only.

## Future Improvements

- Add HTTPS with a custom domain (reverse proxy such as Caddy or Nginx).
- Implement JWT user authentication to separate dashboard logins from API key usage.
- Build a frontend dashboard where users can generate API keys and view their usage statistics.
- Push images to a container registry and deploy by pulling them, instead of building on the server.
- Add monitoring and alerting for latency and error rates.

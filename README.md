# Breed Detection API

A REST API built with FastAPI that serves a YOLOv8 computer vision model for pet breed classification and color analysis.

The API accepts image uploads, processes them through the PyTorch model, and returns breed predictions with confidence scores. It includes API key authentication, rate limiting, file validation, and request logging via PostgreSQL.

## Features

* **Breed Detection**: Uses a custom YOLOv8 model to classify dog and cat breeds.
* **Color Extraction**: Analyzes images to determine dominant RGB/HEX colors.
* **Batch Processing**: Accepts up to 5 images per request to calculate a consensus prediction.
* **Authentication**: Requires an API key passed via HTTP headers.
* **Rate Limiting**: Restricts usage to 5 requests per minute per API key.
* **Payload Validation**: Rejects invalid file types (accepts only JPEG, PNG, WEBP) and files over 5MB.
* **Telemetry**: Logs API usage, response times, and model inferences to PostgreSQL.

## Tech Stack

* **Backend**: FastAPI (Python 3.11)
* **Machine Learning**: PyTorch, Ultralytics (YOLOv8), OpenCV
* **Database**: PostgreSQL 16, SQLAlchemy (ORM), Psycopg
* **Infrastructure**: Docker, Docker Compose

## Quick Start

### 1. Prerequisites

* Docker and Docker Compose
* Git

### 2. Clone and Configure

Clone the repository:

```bash
git clone https://github.com/yourusername/pet-breed-api.git
cd pet-breed-api
```

Create a `.env` file in the root directory:

```bash
POSTGRES_USER=petapi
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=petbreed
```

### 3. Build and Run

Start the API and PostgreSQL containers:

```bash
docker compose up -d --build
```

The API will be accessible at <http://localhost:8089>.

## API Documentation

When the container is running, interactive OpenAPI documentation is generated automatically at:

* **Swagger UI**: <http://localhost:8089/docs>
* **ReDoc**: <http://localhost:8089/redoc>

## Authentication

Requests to protected endpoints require a valid key in the headers:

```
X-API-Key: your_api_key_here
```

## Endpoint: `POST /api/v1/predict`

### Request Format

* **Content-Type**: `multipart/form-data`
* **files**: 1 to 5 images (max 5MB each; allowed: JPEG, PNG, WEBP)

### Example cURL

```bash
curl -X 'POST' \
  'http://localhost:8089/api/v1/predict' \
  -H 'accept: application/json' \
  -H 'X-API-Key: your_api_key_here' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@golden_retriever.jpg;type=image/jpeg'
```

### Example Response

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

The PostgreSQL database maintains three tables for tracking and access control:

* `api_keys`: Stores hashed keys, active status, and the `last_used_at` timestamp.
* `prediction_logs`: Records the AI predictions, confidence scores, and species data.
* `api_usages`: Records all API requests, HTTP status codes, and response times in milliseconds.

## Error Handling

* `400 Bad Request`: Invalid file type, file exceeds 5MB, or image count limits exceeded.
* `401 Unauthorized`: Missing or invalid API key.
* `429 Too Many Requests`: API key exceeded the 5 requests/minute threshold.
* `500 Internal Server Error`: Unexpected server or model failure.

## Future Improvements

* Implement user authentication (JWT) to separate dashboard logins from API key usage.
* Deploy to cloud infrastructure (AWS/GCP) with HTTPS.
* Build a frontend dashboard for users to generate API keys and view their usage statistics.

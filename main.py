from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_db, engine, Base 
from app.api.predict import router as predict_router
from app.api import predict, keys
from app.models import api_key
from app.models import api_usage
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse



Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PetBreed API",
    description="""
    A production-ready AI API for detecting pet breeds and extracting color profiles using YOLOv8.
    
    ### Core Features
    * Multi-image consensus processing
    * Secure API key authentication
    * 5-requests-per-minute rate limiting
    """,
    version="1.0.0",
    docs_url="/docs", 
    redoc_url="/redoc"
)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    # Convert standard HTTP status codes into readable text codes if desired
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR"
    }
    
    code_string = error_code_map.get(exc.status_code, "ERROR")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": code_string,
                "message": exc.detail
            }
        }
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    predict_router,
    prefix="/api/v1",
    tags=["Prediction"]
)

app.include_router(
    keys.router, 
    prefix="/api/v1/keys", 
    tags=["API Keys"]
)


@app.get("/")
def root():
    return {
        "message": "PetBreed API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Convert FastAPI/Pydantic's OpenAPI 3.1
    # file representation into the format
    # Swagger UI expects for file upload controls.
    request_schema = (
        schema["paths"]
        ["/api/v1/predict"]
        ["post"]
        ["requestBody"]
        ["content"]
        ["multipart/form-data"]
        ["schema"]
        ["$ref"]
    )

    schema_name = request_schema.split("/")[-1]

    files_schema = schema["components"]["schemas"][schema_name]["properties"]["files"]

    files_schema["items"].pop("contentMediaType", None)
    files_schema["items"]["format"] = "binary"

    app.openapi_schema = schema

    return app.openapi_schema


app.openapi = custom_openapi

@app.get("/api/v1/health/database")
def database_health():
    db = get_db()

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:

                cursor.execute("SELECT 1")

                result = cursor.fetchone()

        return {
            "success": True,
            "database": "connected",
            "result": result[0]
        }

    except Exception as e:

        return {
            "success": False,
            "database": "disconnected",
            "error": str(e)
        }
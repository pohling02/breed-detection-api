from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.predict import router as predict_router


app = FastAPI(
    title="PetBreed API",
    description="AI-powered dog breed detection API",
    version="1.0.0"
)


app.include_router(
    predict_router,
    prefix="/api/v1",
    tags=["Prediction"]
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
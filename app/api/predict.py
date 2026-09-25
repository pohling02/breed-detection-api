from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from typing import List
import tempfile
import os
import uuid
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.services.pet_detect import PetDetector
from app.auth import verify_rate_limit
from app.models.api_key import ApiKey
from app.models.prediction_log import PredictionLog
from app.database import get_db
from app.models.api_usage import ApiUsage
from app.logger import get_logger

router = APIRouter()
detector = PetDetector()
logger = get_logger(__name__)

@router.post(
    "/predict",
    summary="Predict pet breed and colors from images",
    description="""
    Submit up to 5 images of a single pet to receive an AI-powered breed prediction and color analysis.
    
    ### Requirements
    * **Authentication**: Requires a valid `X-API-Key` header.
    * **Rate Limiting**: Maximum 5 requests per minute per API key.
    * **File Constraints**: 
      * 1 to 5 images per request.
      * Maximum **5MB** per file.
      * Supported formats: `JPEG`, `PNG`, `WEBP`.
      
    ### Response Structure
    Returns a detailed JSON object containing:
    1. `individual_results`: Breed and color breakdown for each uploaded image.
    2. `conclusion`: A consolidated final prediction combining data from all images.
    """,
    tags=["AI Prediction"],
    responses={
        200: {
            "description": "Successful prediction containing breed confidence and color detection.",
            # ... (your existing response schema)
        },
        400: {
            "description": "Bad Request - Triggered by invalid file types, files over 5MB, or uploading more than 5 images."
        },
        401: {
            "description": "Unauthorized - Missing or invalid API key."
        },
        429: {
            "description": "Too Many Requests - Rate limit exceeded."
        },
        500: {
            "description": "Internal Server Error - Model or processing failure."
        }
    }
)
async def predict(
    request: Request,
    files: List[UploadFile] = File(..., description="Upload between 1 and 5 pet images (Max 5MB each)."),
    api_key: ApiKey = Depends(verify_rate_limit), # Locks the endpoint
    db: Session = Depends(get_db)                 # Injects DB connection
):
    start_time = time.time()
    
    # NEW LOG: Start of request
    logger.info(f"Received prediction request from API Key ID: {api_key.id} with {len(files)} files.")
    
    # 1. Basic Count Validation
    if len(files) == 0:
        logger.warning(f"API Key ID: {api_key.id} rejected: No images provided.")
        raise HTTPException(status_code=400, detail="At least one image is required.")
    if len(files) > 5:
        logger.warning(f"API Key ID: {api_key.id} rejected: Too many images ({len(files)}).")
        raise HTTPException(status_code=400, detail="Maximum 5 images per request.")

    # 2. File Security & Size Validation
    ALLOWED_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    MAX_SIZE_MB = 5
    MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

    for file in files:
        # Reject non-image files
        if file.content_type not in ALLOWED_TYPES:
            logger.warning(f"API Key ID: {api_key.id} rejected: Invalid file type '{file.content_type}' for file '{file.filename}'.")
            raise HTTPException(
                status_code=400, 
                detail=f"File '{file.filename}' is an invalid type. Only JPEG, PNG, and WEBP are allowed."
            )
        
        # Reject massive files (FastAPI automatically reads file.size in bytes)
        if file.size > MAX_SIZE_BYTES:
            logger.warning(f"API Key ID: {api_key.id} rejected: File '{file.filename}' exceeds size limit ({file.size} bytes).")
            raise HTTPException(
                status_code=400, 
                detail=f"File '{file.filename}' is too large. Maximum size is {MAX_SIZE_MB}MB."
            )

    # 3. Proceed to Temporary Directory and AI Processing
    with tempfile.TemporaryDirectory() as temp_dir:
        image_paths = []
        for file in files:
            extension = os.path.splitext(file.filename)[1]
            filename = f"{uuid.uuid4()}{extension}"
            file_path = os.path.join(temp_dir, filename)
            
            with open(file_path, "wb") as temp:
                temp.write(await file.read())
            
            image_paths.append(file_path)

        try:
            # NEW LOG: Inference starting
            logger.info(f"Starting YOLOv8 model inference on {len(image_paths)} images for API Key ID: {api_key.id}.")
            
            # Run your AI model
            result = detector.predict(image_paths)
            
            # Extract the data exactly as it appears in your JSON structure
            conclusion = result.get("conclusion", {})
            breed_info = conclusion.get("breed", {})
            final_prediction = breed_info.get("final_prediction", "Unknown")

            # Save the prediction log mapping to the correct JSON keys
            log_entry = PredictionLog(
                api_key_id=api_key.id,
                image_count=len(files),
                species=breed_info.get("final_species", "Unknown"),
                breed=final_prediction,
                confidence=float(breed_info.get("final_confidence", 0.0))
            )
            db.add(log_entry)

            # Update the key's last_used_at timestamp
            api_key.last_used_at = datetime.now(timezone.utc)

            # Calculate final response time and log the API usage
            process_time_ms = int((time.time() - start_time) * 1000)
            usage_entry = ApiUsage(
                api_key_id=api_key.id,
                endpoint="/api/v1/predict",
                status_code=200,
                response_time_ms=process_time_ms
            )
            db.add(usage_entry)

            # Commit EVERYTHING at once
            db.commit()
            
            # NEW LOG: Successful completion
            logger.info(f"Inference successful for API Key ID: {api_key.id}. Predicted: {final_prediction} (Time: {process_time_ms}ms).")

        except Exception as e:
            # NEW LOG: Error with full traceback
            logger.error(f"Prediction failed for API Key ID: {api_key.id}. Error: {str(e)}", exc_info=True)
            
            # If it fails, log the failure time but with a 500 status code
            process_time_ms = int((time.time() - start_time) * 1000)
            usage_entry = ApiUsage(
                api_key_id=api_key.id,
                endpoint=request.url.path,
                status_code=500,
                response_time_ms=process_time_ms
            )
            db.add(usage_entry)
            db.commit()
            
            raise HTTPException(status_code=500, detail="Internal server error during prediction.")

    return result
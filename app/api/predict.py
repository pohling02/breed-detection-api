from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import tempfile
import os
import uuid
from sqlalchemy.orm import Session

from app.services.pet_detect import PetDetector
from app.auth import get_valid_api_key
from app.models.api_key import ApiKey
from app.models.prediction_log import PredictionLog
from app.database import get_db

router = APIRouter()
detector = PetDetector()

@router.post("/predict")
async def predict(
    files: List[UploadFile] = File(...),
    api_key: ApiKey = Depends(get_valid_api_key), # 1. Locks the endpoint
    db: Session = Depends(get_db)                 # 2. Injects DB connection
):
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="At least one image is required.")
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 images per request.")

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
            # 3. Run your actual AI model
            result = detector.predict(image_paths)
            
            # 4. Save the prediction to the database logs
            # Adjust these dict keys ("species", "breed", "confidence") 
            # to match exactly what your PetDetector returns.
            log_entry = PredictionLog(
                api_key_id=api_key.id,
                image_count=len(files),
                species=result.get("species", "Unknown"),
                breed=result.get("breed", "Unknown"),
                confidence=float(result.get("confidence", 0.0))
            )
            db.add(log_entry)
            db.commit()

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return result
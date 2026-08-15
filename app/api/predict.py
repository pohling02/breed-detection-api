from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import tempfile
import os
import uuid

from app.services.pet_detect import PetDetector

router = APIRouter()
detector = PetDetector()


@router.post("/predict")
async def predict(files: List[UploadFile] = File(...)):

    if len(files) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one image is required."
        )

    if len(files) > 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum 5 images per request."
        )

    with tempfile.TemporaryDirectory() as temp_dir:

        image_paths = []

        for file in files:

            extension = os.path.splitext(file.filename)[1]

            filename = f"{uuid.uuid4()}{extension}"

            file_path = os.path.join(
                temp_dir,
                filename
            )

            with open(file_path, "wb") as temp:
                temp.write(await file.read())

            image_paths.append(file_path)

        try:
            result = detector.predict(image_paths)

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

    return result

# from typing import Annotated

# from fastapi import APIRouter, UploadFile, File

# router = APIRouter()


# @router.post("/predict")
# async def predict(
#     files: Annotated[list[UploadFile], File()]
# ):
#     return {
#         "count": len(files),
#         "files": [
#             {
#                 "filename": file.filename,
#                 "content_type": file.content_type
#             }
#             for file in files
#         ]
#     }
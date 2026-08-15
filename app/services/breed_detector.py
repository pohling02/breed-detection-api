import os
import sys
import json
from collections import Counter
from ultralytics import YOLO


MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "app/model/best.pt"
)

class BreedDetector:

    CONF_THRESHOLD = 0.60

    CAT_BREEDS = [
        "Abyssinian",
        "American Shorthair",
        "Bengal",
        "Birman",
        "Bombay",
        "British Shorthair",
        "Domestic Shorthair",
        "Egyptian Mau",
        "Himalayan",
        "Maine Coon",
        "Persian",
        "Ragdoll",
        "Russian Blue",
        "Siamese",
        "Sphynx"
    ]

    def __init__(self):
        self.model = YOLO(MODEL_PATH)
        self.class_names = self.model.names

    def predict(self, image_paths):

        try:

            # Allow single image or multiple images
            if isinstance(image_paths, str):
                image_paths = [image_paths]

            if not image_paths:
                return {
                    "success": False,
                    "error": "No images provided."
                }

            # Limit number of images
            if len(image_paths) > 5:
                return {
                    "success": False,
                    "error": "Maximum 5 images are allowed."
                }

            individual_results = []

            # ==================================================
            # STEP 1: Run YOLO on every image
            # ==================================================

            for image_path in image_paths:

                results = self.model.predict(
                    source=image_path,
                    imgsz=224,
                    verbose=False
                )

                probs = results[0].probs

                if probs is None:
                    raise ValueError(
                        f"No classification probabilities returned "
                        f"for {image_path}."
                    )

                # Get highest probability class
                top_idx = int(
                    probs.data.argmax().item()
                )

                top_conf = float(
                    probs.data[top_idx].item()
                )

                breed_name = self.class_names[top_idx]

                # Determine breed
                if top_conf < self.CONF_THRESHOLD:
                    prediction = "Mixed Breed"
                else:
                    prediction = breed_name

                # Determine species
                species = (
                    "Cat"
                    if breed_name in self.CAT_BREEDS
                    else "Dog"
                )

                individual_results.append({
                    "filename": image_path.split("/")[-1],
                    "prediction": prediction.replace("_", " "),
                    "confidence": top_conf,
                    "species": species
                })

            # ==================================================
            # STEP 2: Check species consistency
            # ==================================================

            species_list = [
                result["species"]
                for result in individual_results
            ]

            unique_species = set(species_list)

            if len(unique_species) > 1:

                return {
                    "success": False,
                    "error": (
                        "Images contain different species. "
                        "Please upload images of the same animal."
                    ),
                    "individual_predictions": individual_results
                }

            final_species = species_list[0]

            # ==================================================
            # STEP 3: Single image
            # ==================================================

            if len(individual_results) == 1:

                result = individual_results[0]

                return {
                    "success": True,
                    "image_count": 1,
                    "final_prediction": result["prediction"],
                    "final_confidence": result["confidence"],
                    "final_species": result["species"],
                    "individual_predictions": individual_results
                }

            # ==================================================
            # STEP 4: Multiple images
            # ==================================================

            predictions = [
                result["prediction"]
                for result in individual_results
            ]

            count = Counter(predictions)

            # Remove Mixed Breed from voting
            count_without_mixed = {
                breed: votes
                for breed, votes in count.items()
                if breed != "Mixed Breed"
            }

            # If every image is below confidence threshold
            if not count_without_mixed:

                return {
                    "success": True,
                    "image_count": len(individual_results),
                    "final_prediction": "Mixed Breed",
                    "final_confidence": 0.0,
                    "final_species": final_species,
                    "individual_predictions": individual_results,
                    "vote_summary": dict(count)
                }

            # ==================================================
            # STEP 5: Majority vote
            # ==================================================

            final_breed, vote_count = max(
                count_without_mixed.items(),
                key=lambda item: item[1]
            )

            total_images = len(individual_results)

            vote_ratio = vote_count / total_images

            # Calculate average confidence
            winning_confidences = [
                result["confidence"]
                for result in individual_results
                if result["prediction"] == final_breed
            ]

            average_confidence = (
                sum(winning_confidences)
                / len(winning_confidences)
            )

            # ==================================================
            # STEP 6: Final result
            # ==================================================

            return {
                "success": True,
                "image_count": total_images,

                "final_prediction": final_breed,

                "final_confidence": average_confidence,

                "final_species": final_species,

                "votes": vote_count,

                "vote_ratio": vote_ratio,

                "individual_predictions": individual_results,

                "vote_summary": dict(count)
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }


if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            json.dumps({
                "success": False,
                "error": "No image path provided"
            })
        )

        sys.exit(1)

    image_paths = sys.argv[1:]

    detector = BreedDetector()

    result = detector.predict(image_paths)

    print(json.dumps(result))
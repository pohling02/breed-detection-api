from app.services.breed_detector import BreedDetector
from app.services.color_detector import ColorDetector


class PetDetector:

    def __init__(self):
        self.breed_detector = BreedDetector()
        self.color_detector = ColorDetector()

    def predict(self, image_paths):

        if isinstance(image_paths, str):
            image_paths = [image_paths]

        breed_result = self.breed_detector.predict(
            image_paths
        )

        if not breed_result.get("success"):
            return breed_result

        breed_lookup = {
            item["filename"]: item 
            for item in breed_result.get("individual_predictions", [])
        }

        individual_results = []
        
        color_aggregation = {}

        for image_path in image_paths:
            filename = image_path.split("/")[-1]

            # 1. Get colors for this specific image
            color_result = self.color_detector.predict(image_path)
            
            # 2. Get breed for this specific image
            ind_breed = breed_lookup.get(filename, {})

            individual_results.append({
                "filename": filename,
                "breed": {
                    "prediction": ind_breed.get("prediction"),
                    "confidence": ind_breed.get("confidence"),
                    "species": ind_breed.get("species")
                },
                "colors": color_result
            })
            
            # 3. Add to color aggregation
            for color in color_result:
                c_name = color["color_name"]
                c_pct = color["percentage"]
                
                if c_name not in color_aggregation:
                    color_aggregation[c_name] = 0.0
                color_aggregation[c_name] += c_pct

        # =====================================
        # Calculate Overall Color Conclusion
        # =====================================
        num_images = len(image_paths)
        final_colors = []
        
        for c_name, total_pct in color_aggregation.items():
            avg_pct = round(total_pct / num_images, 2)
            final_colors.append({
                "color_name": c_name,
                "percentage": avg_pct
            })
            
        # Sort the final colors by percentage (highest first)
        final_colors = sorted(
            final_colors, 
            key=lambda x: x["percentage"], 
            reverse=True
        )

        # =====================================
        # Output Generation
        # =====================================
        return {
            "success": True,
            "image_count": num_images,
            
            # List out image one by one
            "individual_results": individual_results,

            # Make a conclusion at the end
            "conclusion": {
                "breed": {
                    "final_prediction": breed_result.get("final_prediction"),
                    "final_confidence": breed_result.get("final_confidence"),
                    "final_species": breed_result.get("final_species"),
                    "votes": breed_result.get("votes"),
                    "vote_ratio": breed_result.get("vote_ratio")
                },
                "colors": final_colors
            }
        }
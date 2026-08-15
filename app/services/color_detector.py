import cv2
import numpy as np
from sklearn.cluster import KMeans
import math


class ColorDetector:

    def __init__(self, number_of_colors=3):
        self.number_of_colors = number_of_colors
        
        # A baseline dictionary mapping human-readable names to RGB values.
        # You can tweak these RGB values or add more colors if needed.
        self.color_map = {
            # --- Blacks, Grays & Whites ---
            "Black": (25, 25, 25),                 # Very dark, accounts for shadows
            "Charcoal / Dark Gray": (60, 60, 60),
            "Gray": (128, 128, 128),
            "Light Gray / Silver": (180, 180, 180),
            "White": (240, 240, 245),              # Slight blue/cool tint common in white fur
            
            # --- Creams & Golds ---
            "Cream / Ivory": (240, 230, 215),
            "Blonde / Light Gold": (225, 200, 150),
            "Golden": (210, 165, 60),
            
            # --- Tans, Reds & Coppers ---
            "Fawn / Light Tan": (210, 180, 140),
            "Tan": (180, 150, 110),
            "Copper / Rust": (184, 115, 51),       # Common in foxes, Irish Setters
            "Red-Brown / Chestnut": (139, 58, 20),
            
            # --- Browns ---
            "Saddle Brown": (139, 69, 19),
            "Brown": (101, 67, 33),
            "Dark Brown": (60, 40, 20),
            "Chocolate": (45, 30, 15)
        }

    def _get_color_name(self, rgb):
        """Finds the closest matching color name using Euclidean distance."""
        r, g, b = rgb
        min_distance = float('inf')
        closest_name = "Unknown"
        
        for name, (cr, cg, cb) in self.color_map.items():
            # Calculate distance between the extracted RGB and our predefined colors
            distance = math.sqrt((r - cr)**2 + (g - cg)**2 + (b - cb)**2)
            if distance < min_distance:
                min_distance = distance
                closest_name = name
                
        return closest_name

    def predict(self, image_path):

        image = cv2.imread(image_path)

        if image is None:
            raise ValueError(
                f"Unable to read image: {image_path}"
            )

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        image = cv2.resize(
            image,
            (224, 224)
        )

        pixels = image.reshape(-1, 3)

        kmeans = KMeans(
            n_clusters=self.number_of_colors,
            random_state=42,
            n_init=10
        )

        labels = kmeans.fit_predict(pixels)
        centers = kmeans.cluster_centers_
        counts = np.bincount(labels)

        sorted_indices = np.argsort(counts)[::-1]

        colors = []

        for index in sorted_indices:

            rgb = centers[index].astype(int).tolist()
            percentage = (counts[index] / len(labels)) * 100
            
            # Map the RGB to a string color name
            color_name = self._get_color_name(rgb)

            colors.append({
                "color_name": color_name,  # Output the text color instead of just numbers
                "rgb": rgb,
                "percentage": round(float(percentage), 2)
            })

        return colors
"""OCR functions."""
# Read text from an image
import re
from decimal import Decimal, InvalidOperation

import easyocr
import numpy as np
from PIL import Image

# Create an OCR reader object
reader = easyocr.Reader(["en"])


def get_distance_easyocr(image: Image) -> Decimal:
    # Convert the image to an appropriate format for easyocr
    # Note: easyocr can work directly with numpy arrays, so we'll convert the image to a numpy array
    image_np = np.array(image)
    result = reader.readtext(image_np)
    distance_list = []
    prev_text = ""
    for detection in result:
        text: str = detection[1]
        text = text.strip().lower()
        text = text.replace("/km", "")
        text = text.replace("km/", "")
        # if contain only km, the distance might be in previous text.
        if text == "km":
            text = prev_text + text

        if "km" in text:
            distance = get_number_before_km(text)

            try:
                prased_distance = Decimal(distance)
                distance_list.append(prased_distance)
            except InvalidOperation:
                return Decimal(0)
        prev_text = text
    if len(distance_list) == 1:
        return distance_list[0]
    return Decimal(0)


def get_number_before_km(text: str) -> str:
    pattern = r"(\d+\.?\d*)\s*km"

    match = re.search(pattern, text)
    if match:
        number_before_km = match.group(1)
        return number_before_km
    return ""

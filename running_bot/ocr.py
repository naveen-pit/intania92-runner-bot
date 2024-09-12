"""OCR functions."""

# Read text from an image
import re
from decimal import Decimal, InvalidOperation

from rapidocr_onnxruntime import RapidOCR

# Create an OCR reader object
engine = RapidOCR()


def extract_distance_from_image(image_path: str) -> Decimal:
    result, _ = engine(image_path)
    distance_list = []
    prev_text = ""
    if result:
        for detection in result:
            text = detection[1].strip().lower().replace("/km", "").replace("km/", "")

            # if contain only km, the distance might be in previous text.
            if text == "km":
                text = prev_text + text

            if "km" in text:
                distance = get_number_before_km(text)
                try:
                    parsed_distance = Decimal(distance)
                    distance_list.append(parsed_distance)
                except InvalidOperation:
                    pass
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

"""Test ocr functions."""

from decimal import Decimal
from pathlib import Path

from running_bot.ocr import extract_distance_from_image, get_number_before_km


def test_extract_distance_from_image():
    test_image_path = Path(__file__).parent.resolve() / "test_images"
    image_path = test_image_path / "5_01.jpg"
    assert extract_distance_from_image(image_path) == Decimal("5.01")

    image_path = test_image_path / "18_54.jpg"
    assert extract_distance_from_image(image_path) == Decimal("18.54")

    image_path = test_image_path / "21_20.jpg"
    assert extract_distance_from_image(image_path) == Decimal("21.20")

    image_path = test_image_path / "24_0.jpg"
    assert extract_distance_from_image(image_path) == Decimal("24.0")

    # No distance in the slip
    image_path = test_image_path / "NA 1.jpg"
    assert extract_distance_from_image(image_path) == Decimal("0")

    # Multiple km in the slip
    image_path = test_image_path / "NA 2.jpg"
    assert extract_distance_from_image(image_path) == Decimal("0")

    # Multiple km in the slip
    image_path = test_image_path / "NA 3.jpg"
    assert extract_distance_from_image(image_path) == Decimal("0")


def test_get_number_before_km():
    text = "14.06 km"
    assert get_number_before_km(text) == "14.06"

    text = "14.06km"
    assert get_number_before_km(text) == "14.06"

    text = "a14.06 km"
    assert get_number_before_km(text) == "14.06"

    text = "14.06 /km"
    assert get_number_before_km(text) == ""

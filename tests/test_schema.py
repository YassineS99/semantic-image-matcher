from app.models.schemas import ImageTag
import pytest
from pydantic import ValidationError


def test_valid_image_tag():
    tag = ImageTag(
        subject="red fox",
        category="canid",
        attributes=["reddish fur", "pointed ears"],
        caption="A red fox in a field.",
        confidence=0.9,
    )
    assert tag.subject == "red fox"
    assert tag.confidence == 0.9


def test_confidence_out_of_range_rejected():
    with pytest.raises(ValidationError):
        ImageTag(
            subject="red fox",
            category="canid",
            attributes=["reddish fur"],
            caption="A red fox in a field.",
            confidence=1.5,  # invalid: above 1.0
        )
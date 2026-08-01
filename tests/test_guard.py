from app.services.guard import evaluate_match


def test_guard_rejects_coyote_for_wolf_post():
    result = evaluate_match(
        post_text="Amazing shot of a wolf pack howling at night",
        image_subject="coyote",
        similarity=0.6340,
    )
    assert result["decision"] == "rejected"
    assert "subject mismatch" in result["reason"]


def test_guard_accepts_correct_wolf_match():
    result = evaluate_match(
        post_text="Amazing shot of a wolf pack howling at night",
        image_subject="gray wolf",
        similarity=0.7013,
    )
    assert result["decision"] == "suggested"
    assert result["reason"] is None


def test_guard_accepts_wolf_subspecies_variant():
    # tibetan wolf should still be treated as a wolf match
    result = evaluate_match(
        post_text="Amazing shot of a wolf pack howling at night",
        image_subject="tibetan wolf",
        similarity=0.6257,
    )
    assert result["decision"] == "suggested"


def test_guard_rejects_low_similarity_even_with_correct_subject():
    result = evaluate_match(
        post_text="A photo of a red fox",
        image_subject="red fox",
        similarity=0.3,  # below threshold
    )
    assert result["decision"] == "rejected"
    assert "similarity below threshold" in result["reason"]
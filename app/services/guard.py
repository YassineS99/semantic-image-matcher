SIMILARITY_THRESHOLD = 0.60

# maps words that might appear in a post to the canonical subject name
SUBJECT_KEYWORDS = {
    "red fox": ["fox", "vulpes"],
    "gray wolf": ["wolf", "wolves"],
    "coyote": ["coyote"],
    "german shepherd": ["german shepherd", "gsd"],
    "siberian husky": ["husky"],
}


def infer_post_subject(post_text: str) -> str | None:
    text_lower = post_text.lower()
    for subject, keywords in SUBJECT_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return subject
    return None


def evaluate_match(post_text: str, image_subject: str, similarity: float) -> dict:
    reasons = []

    if similarity < SIMILARITY_THRESHOLD:
        reasons.append(f"similarity below threshold ({similarity:.4f} < {SIMILARITY_THRESHOLD})")

    inferred_subject = infer_post_subject(post_text)
    if inferred_subject:
        # loose match: check if the core subject word appears in the image's subject
        # e.g. "wolf" matches both "gray wolf" and "tibetan wolf"
        core_word = inferred_subject.split()[-1]  # "gray wolf" -> "wolf", "red fox" -> "fox"
        if core_word not in image_subject.lower():
            reasons.append(f"subject mismatch: post implies '{inferred_subject}', image is '{image_subject}'")

    if reasons:
        return {"decision": "rejected", "reason": "; ".join(reasons)}
    else:
        return {"decision": "suggested", "reason": None}
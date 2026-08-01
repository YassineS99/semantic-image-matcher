from app.models.db import SessionLocal
from sqlalchemy import text as sql_text

EXPECTED = {
    2: "wolf",
    3: "fox",
    4: "fox",
    5: "coyote",
    6: "husky",
    7: "german",
}


def test_top1_precision_meets_minimum():
    session = SessionLocal()
    correct = 0
    total = len(EXPECTED)

    for post_id, expected_prefix in EXPECTED.items():
        row = session.execute(
            sql_text("""
                SELECT i.filename
                FROM pairings p
                JOIN images i ON i.id = p.image_id
                WHERE p.post_id = :pid AND p.guard_decision = 'suggested'
                ORDER BY p.similarity_score DESC
                LIMIT 1
            """),
            {"pid": post_id}
        ).first()

        if row and row.filename.startswith(expected_prefix):
            correct += 1

    session.close()
    precision = correct / total

    # require at least 80% top-1 precision (allows some tolerance vs. requiring literally perfect)
    assert precision >= 0.8, f"Top-1 precision {precision:.2%} below 80% threshold"
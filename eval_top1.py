from app.models.db import SessionLocal
from sqlalchemy import text as sql_text

# maps post_id -> expected species prefix (matches filename convention: fox_, wolf_, coyote_, husky_, german_)
EXPECTED = {
    2: "wolf",
    3: "fox",
    4: "fox",
    5: "coyote",
    6: "husky",
    7: "german",
}


def eval_top1():
    session = SessionLocal()
    correct = 0
    total = len(EXPECTED)

    for post_id, expected_prefix in EXPECTED.items():
        row = session.execute(
            sql_text("""
                SELECT i.filename, p.similarity_score
                FROM pairings p
                JOIN images i ON i.id = p.image_id
                WHERE p.post_id = :pid AND p.guard_decision = 'suggested'
                ORDER BY p.similarity_score DESC
                LIMIT 1
            """),
            {"pid": post_id}
        ).first()

        if row is None:
            print(f"Post {post_id}: NO MATCH FOUND")
            continue

        is_correct = row.filename.startswith(expected_prefix)
        correct += int(is_correct)
        status = "CORRECT" if is_correct else "WRONG"
        print(f"Post {post_id}: top-1 = {row.filename} ({status}, expected prefix '{expected_prefix}')")

    session.close()
    precision = correct / total
    print(f"\nTop-1 precision: {correct}/{total} = {precision:.2%}")


if __name__ == "__main__":
    eval_top1()
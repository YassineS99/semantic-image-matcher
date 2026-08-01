from app.models.db import SessionLocal
from app.services.guard import evaluate_match
from sqlalchemy import text as sql_text


def match_post(post_id: int, top_n: int = 5):
    session = SessionLocal()

    # 1. get the post's text
    post_row = session.execute(
        sql_text("SELECT text FROM posts WHERE id = :pid"),
        {"pid": post_id}
    ).first()
    post_text = post_row.text

    # 2. get top candidate images by similarity
    candidates = session.execute(
        sql_text("""
            SELECT
                t.id AS tag_id,
                i.id AS image_id,
                t.subject,
                1 - (iv.embedding <=> pv.embedding) AS similarity
            FROM post_vectors pv
            JOIN image_vectors iv ON true
            JOIN image_tags t ON t.id = iv.image_tag_id
            JOIN images i ON i.id = t.image_id
            WHERE pv.post_id = :pid
            ORDER BY similarity DESC
            LIMIT :n
        """),
        {"pid": post_id, "n": top_n}
    ).fetchall()

    # 3. clear any previous pairings for this post (so reruns don't duplicate)
    session.execute(sql_text("DELETE FROM pairings WHERE post_id = :pid"), {"pid": post_id})
    session.commit()

    # 4. evaluate each candidate through the guard, insert into pairings
    best_suggested = None
    for c in candidates:
        result = evaluate_match(post_text, c.subject, c.similarity)

        session.execute(
            sql_text("""
                INSERT INTO pairings (post_id, image_id, similarity_score, guard_decision, guard_reason)
                VALUES (:post_id, :image_id, :similarity, :decision, :reason)
            """),
            {
                "post_id": post_id,
                "image_id": c.image_id,
                "similarity": c.similarity,
                "decision": result["decision"],
                "reason": result["reason"],
            }
        )

        if result["decision"] == "suggested" and best_suggested is None:
            best_suggested = c

    session.commit()
    session.close()

    if best_suggested:
        print(f"Best match: image_id={best_suggested.image_id} (subject={best_suggested.subject}, similarity={best_suggested.similarity:.4f})")
    else:
        print("No good match found for this post.")


if __name__ == "__main__":
    match_post(post_id=10, top_n=10)

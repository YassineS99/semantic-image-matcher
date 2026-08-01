from app.models.db import SessionLocal
from sqlalchemy import text as sql_text

def rank_matches(post_id: int, top_n: int = 5):
    session = SessionLocal()

    results = session.execute(
        sql_text("""
            SELECT
                i.filename,
                t.subject,
                t.category,
                t.caption,
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

    session.close()

    for r in results:
        print(f"{r.filename} | subject={r.subject} | similarity={r.similarity:.4f}")
        print(f"  caption: {r.caption}")

    return results


if __name__ == "__main__":
    rank_matches(post_id=2, top_n=15)
    
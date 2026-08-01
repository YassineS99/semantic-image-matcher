from app.models.db import SessionLocal
from app.models.tables import Image, ImageTagRow
from app.services.embeddings import embed_text
from sqlalchemy import text as sql_text

def add_post(post_text: str):
    session = SessionLocal()

    result = session.execute(
        sql_text("INSERT INTO posts (text) VALUES (:t) RETURNING id"),
        {"t": post_text}
    )
    post_id = result.scalar()
    session.commit()

    vector = embed_text(post_text, reference_id=post_id, call_type="embedding")

    session.execute(
        sql_text("INSERT INTO post_vectors (post_id, embedding) VALUES (:pid, :vec)"),
        {"pid": post_id, "vec": str(vector)}
    )
    session.commit()
    session.close()

    print(f"Post created: id={post_id}")
    return post_id


if __name__ == "__main__":
    add_post("My cat knocked a plant off the shelf again")
from app.models.db import SessionLocal
from app.models.tables import ImageTagRow
from app.services.embeddings import embed_text
from sqlalchemy import text as sql_text

def run_embed_images():
    session = SessionLocal()
    tags = session.query(ImageTagRow).filter(ImageTagRow.status == "tagged").all()

    for tag in tags:
        # skip if this tag already has an embedding
        existing = session.execute(
            sql_text("SELECT id FROM image_vectors WHERE image_tag_id = :tid"),
            {"tid": tag.id}
        ).first()
        if existing:
            print(f"Skipping tag_id={tag.id} (already embedded)")
            continue

        print(f"Embedding tag_id={tag.id} ({tag.subject})...")
        vector = embed_text(tag.caption, reference_id=tag.image_id, call_type="embedding")

        session.execute(
            sql_text("INSERT INTO image_vectors (image_tag_id, embedding) VALUES (:tid, :vec)"),
            {"tid": tag.id, "vec": str(vector)}
        )
        session.commit()

    session.close()
    print("Embedding complete.")


if __name__ == "__main__":
    run_embed_images()
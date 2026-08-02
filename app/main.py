from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.models.db import SessionLocal
from sqlalchemy import text as sql_text
from datetime import datetime, timezone
from pydantic import BaseModel
from app.services.embeddings import embed_text
from app.services.guard import evaluate_match

app = FastAPI(title="FlyRank Capstone API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory="data/images"), name="images")


@app.get("/pairings")
def list_pairings(status: str = "suggested"):
    session = SessionLocal()
    rows = session.execute(
        sql_text("""
            SELECT p.id, p.post_id, p.image_id, i.filename, p.similarity_score,
                   p.guard_decision, p.guard_reason, p.review_status
            FROM pairings p
            JOIN images i ON i.id = p.image_id
            WHERE p.guard_decision = :status
            ORDER BY p.similarity_score DESC
        """),
        {"status": status}
    ).fetchall()
    session.close()

    return [dict(r._mapping) for r in rows]


@app.post("/pairings/{pairing_id}/approve")
def approve_pairing(pairing_id: int):
    session = SessionLocal()
    result = session.execute(
        sql_text("""
            UPDATE pairings
            SET review_status = 'approved', reviewed_at = :now
            WHERE id = :id
            RETURNING id
        """),
        {"id": pairing_id, "now": datetime.now(timezone.utc)}
    ).first()
    session.commit()
    session.close()

    if not result:
        raise HTTPException(status_code=404, detail="Pairing not found")
    return {"id": pairing_id, "review_status": "approved"}


@app.post("/pairings/{pairing_id}/reject")
def reject_pairing(pairing_id: int):
    session = SessionLocal()
    result = session.execute(
        sql_text("""
            UPDATE pairings
            SET review_status = 'rejected', reviewed_at = :now
            WHERE id = :id
            RETURNING id
        """),
        {"id": pairing_id, "now": datetime.now(timezone.utc)}
    ).first()
    session.commit()
    session.close()

    if not result:
        raise HTTPException(status_code=404, detail="Pairing not found")
    return {"id": pairing_id, "review_status": "rejected"}


class PostCreate(BaseModel):
    text: str


@app.post("/posts")
def create_post(post: PostCreate):
    session = SessionLocal()

    result = session.execute(
        sql_text("INSERT INTO posts (text) VALUES (:t) RETURNING id"),
        {"t": post.text}
    )
    post_id = result.scalar()
    session.commit()

    vector = embed_text(post.text, reference_id=post_id, call_type="embedding")

    session.execute(
        sql_text("INSERT INTO post_vectors (post_id, embedding) VALUES (:pid, :vec)"),
        {"pid": post_id, "vec": str(vector)}
    )
    session.commit()
    session.close()

    return {"post_id": post_id, "text": post.text}


@app.post("/posts/{post_id}/match")
def run_match(post_id: int, top_n: int = 10):
    session = SessionLocal()

    post_row = session.execute(
        sql_text("SELECT text FROM posts WHERE id = :pid"),
        {"pid": post_id}
    ).first()
    if not post_row:
        raise HTTPException(status_code=404, detail="Post not found")
    post_text = post_row.text

    candidates = session.execute(
        sql_text("""
            SELECT t.id AS tag_id, i.id AS image_id, i.filename, t.subject,
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

    session.execute(sql_text("DELETE FROM pairings WHERE post_id = :pid"), {"pid": post_id})
    session.commit()

    results = []
    for c in candidates:
        result = evaluate_match(post_text, c.subject, c.similarity)

        session.execute(
            sql_text("""
                INSERT INTO pairings (post_id, image_id, similarity_score, guard_decision, guard_reason)
                VALUES (:post_id, :image_id, :similarity, :decision, :reason)
            """),
            {
                "post_id": post_id, "image_id": c.image_id, "similarity": c.similarity,
                "decision": result["decision"], "reason": result["reason"],
            }
        )
        results.append({
            "image_id": c.image_id,
            "filename": c.filename,
            "subject": c.subject,
            "similarity": c.similarity,
            "decision": result["decision"],
            "reason": result["reason"],
        })

    session.commit()
    session.close()

    best = next((r for r in results if r["decision"] == "suggested"), None)
    return {"post_id": post_id, "best_match": best, "candidates": results}
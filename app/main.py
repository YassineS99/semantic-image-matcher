from fastapi import FastAPI, HTTPException
from app.models.db import SessionLocal
from sqlalchemy import text as sql_text
from datetime import datetime, timezone

app = FastAPI(title="FlyRank Capstone API")


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
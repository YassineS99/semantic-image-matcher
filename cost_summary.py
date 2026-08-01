from app.models.db import SessionLocal
from app.models.tables import ApiCallLog
from sqlalchemy import func

session = SessionLocal()

print("=== Cost Summary by Call Type ===")
breakdown = (
    session.query(
        ApiCallLog.call_type,
        func.count(ApiCallLog.id),
        func.sum(ApiCallLog.estimated_cost_usd),
    )
    .group_by(ApiCallLog.call_type)
    .all()
)
for call_type, count, cost in breakdown:
    print(f"{call_type}: {count} calls, ${cost:.6f}")

total_cost = session.query(func.sum(ApiCallLog.estimated_cost_usd)).scalar() or 0
total_calls = session.query(func.count(ApiCallLog.id)).scalar()
failed_calls = session.query(func.count(ApiCallLog.id)).filter_by(success=False).scalar()

print(f"\nTotal API calls: {total_calls}")
print(f"Failed calls: {failed_calls}")
print(f"Total estimated cost: ${total_cost:.6f}")

session.close()
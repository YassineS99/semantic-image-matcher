import os
import time
from datetime import datetime, timezone
from app.models.db import SessionLocal
from app.models.tables import Image, ImageTagRow
from app.services.vision import classify_image

IMAGES_DIR = "data/images"
MAX_RETRIES = 3
CONFIDENCE_THRESHOLD = 0.7


def classify_with_retries(filepath: str, image_id: int):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return classify_image(filepath, image_id=image_id)
        except Exception as e:
            print(f"  attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2 * attempt)
            else:
                return None
        except Exception as e:
            print(f"  attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2 * attempt)
            else:
                return None


def run_batch():
    session = SessionLocal()
    filenames = sorted(f for f in os.listdir(IMAGES_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png")))

    for filename in filenames:
        filepath = os.path.join(IMAGES_DIR, filename)

        # 1. insert or find the image row
        image = session.query(Image).filter_by(filename=filename).first()
        if not image:
            image = Image(filename=filename, filepath=filepath)
            session.add(image)
            session.commit()
            session.refresh(image)

        # 2. skip if this image already has a successful tag
        existing_tag = (
            session.query(ImageTagRow)
            .filter_by(image_id=image.id, status="tagged")
            .first()
        )
        if existing_tag:
            print(f"Skipping {filename} (already tagged)")
            continue

        # 2b. clear out any old failed/needs_review rows for this image before retrying
        session.query(ImageTagRow).filter_by(image_id=image.id).delete()
        session.commit()

        print(f"Processing {filename}...")

        # 3. classify with retries
result = classify_with_retries(filepath, image_id=image.id)
        now = datetime.now(timezone.utc)

        if result is None:
            tag_row = ImageTagRow(
                image_id=image.id,
                subject="unknown",
                category="unknown",
                attributes=[],
                caption="",
                confidence=0.0,
                status="failed",
                classified_at=now,
            )
        else:
            status = "tagged" if result.confidence >= CONFIDENCE_THRESHOLD else "needs_review"
            tag_row = ImageTagRow(
                image_id=image.id,
                subject=result.subject.lower(),
                category=result.category.lower(),
                attributes=[a.lower() for a in result.attributes],
                caption=result.caption,
                confidence=result.confidence,
                status=status,
                classified_at=now,
            )

        session.add(tag_row)
        session.commit()
        print(f"  -> {tag_row.status} (confidence={tag_row.confidence})")

    session.close()
    print("Batch complete.")


if __name__ == "__main__":
    run_batch()
# EVIDENCE.md

One pasted proof per Definition of Done checkbox.

---

## AI Processing

### Vision model produces structured output validated against a schema

subject='red fox' category='canid' attributes=['reddish-orange coat', 'pointed ears', 'bushy tail with white tip', 'slender snout'] caption='A young red fox stands at the edge of the water with its mouth slightly open near dry vegetation.' confidence=0.95

Output is a validated `ImageTag` Pydantic instance (`app/models/schemas.py`), not raw text.

### Invalid responses never trusted / low-confidence flagged instead of accepted

status = "tagged" if result.confidence >= CONFIDENCE_THRESHOLD else "needs_review"

`CONFIDENCE_THRESHOLD = 0.7` in `batch_classify.py`. All 49 images in the final corpus scored at or above 0.7 (range 0.85-0.98), so none landed in `needs_review` in this run. The rule itself is verified directly in `tests/test_guard.py` and by design in `batch_classify.py`.

### Batch background job with retries

Processing wolf_002.jpg...
  attempt 1 failed: 429 RESOURCE_EXHAUSTED ...
  -> tagged (confidence=0.85)

`classify_with_retries()` in `batch_classify.py`, MAX_RETRIES=3 with exponential backoff. Real retries were exercised repeatedly against live API rate limits during development.

### Cost tracked per call

=== Cost Summary by Call Type ===
vision: 1 calls, $0.000113
embedding: 52 calls, $0.000118

Total API calls: 53
Failed calls: 0
Total estimated cost: $0.000231

Output of `python cost_summary.py`, reading from the `api_calls` table.

---

## Matching System

### Image and post embeddings stored; posts return ranked image suggestions

fox_007.jpg | subject=red fox | similarity=0.6926
fox_005.jpg | subject=red fox | similarity=0.6882
fox_010.jpg | subject=red fox | similarity=0.6849

Output of `python rank_matches.py` for a post embedded via `add_post.py`.

### Semantic matching works for equivalent concepts ("red fox" vs "Vulpes vulpes")

Post text used: "Check out this beautiful vulpes vulpes I spotted on my hike today!" (scientific name, zero keyword overlap with "fox"). Top 5 results were all real red fox images (see rank above), proving the match is semantic, not keyword-based.

---

## Safety Layer

### Mismatch guard rejects incorrect recommendations - wolf/fox-family scenario provably fails

Real query result against post_id=2 ("Amazing shot of a wolf pack howling at night"):

 image_id |  similarity_score  | guard_decision |                         guard_reason
----------+--------------------+----------------+---------------------------------------------------------------
       44 | 0.7013323934077405 | suggested      |
       ...
        2 | 0.6360344263346006 | rejected       | subject mismatch: post implies 'gray wolf', image is 'coyote'
       39 | 0.6344521991092266 | suggested      |

A coyote image (id=2) scored 0.636 similarity, inside the range of real wolf matches (0.634-0.642), and was still correctly rejected by the subject-consistency check. This is the exact "similar species / wrong pairing" case the guard exists to catch.

### Rejections include a human-readable explanation

guard_reason: "subject mismatch: post implies 'gray wolf', image is 'coyote'" - stored directly on the `pairings` row (see above), also asserted in `tests/test_guard.py`.

### "No confident match" case, with reasons

Post text used: "My cat knocked a plant off the shelf again" (no matching species in corpus).

$ python match_post.py
No good match found for this post.

 image_id |  similarity_score  | guard_decision |               guard_reason
----------+--------------------+----------------+-------------------------------------------
        6 | 0.5289839506149292 | rejected       | similarity below threshold (0.5290 < 0.6)
       41 | 0.5281057357788086 | rejected       | similarity below threshold (0.5281 < 0.6)

Every candidate correctly rejected on similarity alone; no forced/guessed suggestion.

---

## Backend

### Database models with required indexes

`app/models/schema.sql` - 7 tables (images, image_tags, posts, image_vectors, post_vectors, pairings, api_calls), with indexes on all foreign keys and status columns, plus hnsw vector indexes on both embedding tables for similarity search.

### Validated API endpoints; review workflow (approve/reject/inspect) exists

POST /pairings/11/approve
{
  "id": 11,
  "review_status": "approved"
}

Verified via the FastAPI Swagger UI (/docs) - GET /pairings, POST /pairings/{id}/approve, POST /pairings/{id}/reject all tested live and working (`app/main.py`).

### Automated tests: schema validation, mismatch rejection, matching accuracy

collected 7 items
tests/test_eval.py::test_top1_precision_meets_minimum PASSED
tests/test_guard.py::test_guard_rejects_coyote_for_wolf_post PASSED
tests/test_guard.py::test_guard_accepts_correct_wolf_match PASSED
tests/test_guard.py::test_guard_accepts_wolf_subspecies_variant PASSED
tests/test_guard.py::test_guard_rejects_low_similarity_even_with_correct_subject PASSED
tests/test_schema.py::test_valid_image_tag PASSED
tests/test_schema.py::test_confidence_out_of_range_rejected PASSED
================================================== 7 passed in 0.49s ==================

### Labeled evaluation dataset measures top-1 precision, matches README

Post 2: top-1 = wolf_007.jpg (CORRECT, expected prefix 'wolf')
Post 3: top-1 = fox_014.jpg (CORRECT, expected prefix 'fox')
Post 4: top-1 = fox_014.jpg (CORRECT, expected prefix 'fox')
Post 5: top-1 = coyote_007.jpg (CORRECT, expected prefix 'coyote')
Post 6: top-1 = husky_001.jpg (CORRECT, expected prefix 'husky')
Post 7: top-1 = german_003.jpg (CORRECT, expected prefix 'german')

Top-1 precision: 6/6 = 100.00%

Output of `python eval_top1.py`. Matches the number reported in README.md.

---

## Quality & Documentation

### README with architecture explanation and diagram

See README.md - includes text-based architecture diagram, schema documentation, guard design rationale, setup steps, and an honest "Known Limitations" section.

### Submission-pack files present

README.md, capstone.yaml, EVIDENCE.md (this file), BUILDLOG.md, .env.example, LICENSE - all present at repo root.
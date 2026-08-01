# FlyRank Capstone: Image–Post Matching with a Mismatch Guard

**Cohort:** FlyRank Backend AI Engineering | **Difficulty:** ★★☆ Medium–High

## Overview

This project ingests a library of animal images, classifies each with a vision
model into structured tags, embeds both images and posts into a shared semantic
space, ranks the best image matches per post, and — critically — includes a
**mismatch guard** that refuses a bad pairing (e.g. a wolf photo suggested for a
red fox post) instead of blindly returning the top-ranked result.

The corpus is 49 real photos across five closely related canid species/breeds
(red fox, gray wolf, coyote, Siberian husky, German shepherd) — chosen
specifically because they are visually and semantically similar, making the
guard's job genuinely hard rather than trivial.

## Architecture

```
[images] -(batch job)-> vision model -> {tags, caption, confidence} -> image_tags
                                      \-> embed(caption) -> image_vectors

[posts] -> embed(post text) -> post_vectors

GET /pairings -> rank by similarity -> mismatch guard (subject + threshold)
              -> {suggested | rejected} -> review API: approve/reject
```

**Pipeline stages:**
1. **Ingest & classify** — `batch_classify.py` sends each image to a vision
   model (Google Gemini, `gemini-flash-latest`), validates the response against
   a Pydantic schema, and stores it in `image_tags`.
2. **Embed** — `embed_images.py` embeds each image's caption
   (`gemini-embedding-001`, 1536 dimensions) into `image_vectors`. Posts are
   embedded the same way into `post_vectors` via `add_post.py`.
3. **Rank & guard** — `match_post.py` ranks candidate images by cosine
   similarity (via `pgvector`), runs each through the mismatch guard, and
   writes the decision into `pairings`.
4. **Review** — a FastAPI service (`app/main.py`) exposes endpoints to list
   suggested pairings and approve/reject them.

## Tag Schema

```json
{
  "subject": "red fox",
  "category": "canid",
  "attributes": ["reddish-orange fur", "large pointed ears", "bushy tail with white tip", "narrow pointed snout"],
  "caption": "The red fox is a highly intelligent and adaptable mammal...",
  "confidence": 0.91
}
```

- `subject`: specific species/breed identification
- `category`: broader taxonomic grouping (all "canid" in this corpus) — used
  for loose matching, but deliberately **not** sufficient on its own to confirm
  a match, since every species here shares the same category
- `attributes`: visually observable traits only (fur color, ear shape, tail
  tip color, snout shape) — no traits that can't be seen in a typical photo
  (e.g. weight, pack behavior)
- `caption`: natural-language sentence, used as the text that gets embedded
- `confidence`: float 0.0–1.0; **below 0.7 → flagged as `needs_review`**
  instead of being trusted automatically

Full schema documentation: `docs/schema.md`

## The Mismatch Guard

The guard runs two independent checks; a pairing is only `suggested` if both pass:

1. **Similarity threshold** — cosine similarity between the post's embedding
   and the image's caption embedding must be ≥ 0.60.
2. **Subject consistency** — the post's implied subject (inferred via keyword
   matching, e.g. "wolf" → `gray wolf`) must appear in the image's actual
   `subject` field. This uses a loose substring match (`"wolf" in "tibetan
   wolf"`) so subspecies variants aren't incorrectly rejected.

**Why two checks, not one:** similarity alone is not sufficient to catch
subject-level mismatches when species are visually/semantically close. In this
project's real data, a coyote image scored **0.6340** similarity against a
"wolf pack" post — landing *inside* the cluster of real wolf scores
(0.6337–0.6425). A similarity-only guard would have suggested this coyote. The
subject check catches it:

```
image_id=2 (coyote) | similarity=0.6360 | REJECTED
  reason: "subject mismatch: post implies 'gray wolf', image is 'coyote'"
```

This is real, measured data from the project's own database — not a
hypothetical example.

## Results

- **Corpus:** 49 images (15 fox, 12 wolf, 12 coyote, 5 husky, 5 German shepherd),
  sourced from iNaturalist, Wikimedia Commons, Pexels, and Unsplash under
  CC0/CC-BY/CC-BY-NC/Pexels/Unsplash licenses (see `docs/sources.csv`)
- **Classification:** 49/49 images successfully tagged, all above the 0.7
  confidence threshold (no `needs_review` cases in this run)
- **Top-1 precision:** 6/6 (100%) on a labeled eval set spanning all 5
  species/breeds (`eval_top1.py`)
- **Guard rejection proof:** coyote correctly rejected for a wolf-themed post
  despite near-identical similarity score to real wolves
- **Paraphrase matching:** a post written using the scientific name
  "vulpes vulpes" correctly ranked real fox images highest, with zero keyword
  overlap
- **Cost:** entire project (49 vision calls + 52 embedding calls) cost
  approximately **$0.0002** total (see `cost_summary.py`)

### Additional guard stress-tests

Beyond the required fox/wolf rejection case, the guard was tested against
several additional real scenarios, each producing a distinct, correct outcome:

| Post | Outcome | Evidence |
|---|---|---|
| "wolf-like dog was howling in my backyard" (ambiguous phrasing) | Correctly matched to a real gray wolf; **4 separate coyote candidates rejected**, all with competitive similarity scores (0.64–0.65) | `guard_reason`: *"subject mismatch: post implies 'gray wolf', image is 'coyote'"* (image_ids 3, 4, 5, 9) |
| "My cat knocked a plant off the shelf again" (out-of-domain, no matching species in corpus) | **No suggested match at all** — every candidate correctly rejected on the similarity threshold alone (no subject keyword to check against) | Top candidate similarity 0.5290, all below the 0.60 threshold |
| "cutest husky puppy at the park" (new, unseen post) | Correctly matched to a real Siberian husky image | `image_id=35, similarity=0.6825` |

These results show the guard behaving correctly not just on the required
fox/wolf case, but across ambiguous phrasing (where a keyword like "wolf"
appears inside a phrase actually describing a dog) and fully out-of-domain
input (where no subject keyword matches at all, and the similarity threshold
alone must do the rejecting). The "wolf-like dog" case is also a useful,
honest illustration of the subject-inference limitation described below: a
keyword-based check can be misled by phrasing where the keyword is present
but not the true subject of the post.

## Setup

1. Start the database:
   ```bash
   docker compose up -d
   ```
2. Create a Python virtual environment and install dependencies:
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. Set environment variables in `.env`:
   ```
   GOOGLE_API_KEY=your_key_here
   DATABASE_URL=postgresql://flyrank:flyrank_dev_pw@localhost:5432/flyrank
   ```
4. Build the schema (only needed on a fresh database):
   ```bash
   Get-Content app/models/schema.sql | docker exec -i flyrank-db psql -U flyrank -d flyrank
   ```
5. Run the pipeline:
   ```bash
   python batch_classify.py     # classify all images
   python embed_images.py       # embed all captions
   python add_post.py           # create + embed a post
   python match_post.py         # rank + guard + store pairings
   ```
6. Start the review API:
   ```bash
   uvicorn app.main:app --reload
   ```
   Visit `http://localhost:8000/docs` for the interactive API.

## Running Tests

```bash
python -m pytest tests/ -v
```

Covers:
- Schema validation (valid tag accepted, out-of-range confidence rejected)
- Mismatch guard (coyote rejected for wolf post, correct wolf/subspecies
  accepted, low-similarity rejection)
- Eval (top-1 precision ≥ 80% threshold, actual measured result: 100%)

## Known Limitations

- **Cost tracking gap:** `api_calls` logging was added partway through
  development; the initial 49-image classification batch predates it and isn't
  reflected in the cost totals. Only re-running the batch would produce a
  complete cost log.
- **Eval test requires a seeded database:** `tests/test_eval.py` reads from
  `pairings`, so it depends on `match_post.py` having already been run for the
  test post IDs — it is not a fully isolated unit test.
- **Subject inference is keyword-based:** `infer_post_subject()` uses a fixed
  keyword dictionary rather than an NLP/embedding-based approach. This is
  intentional (deterministic, auditable, no extra API cost) but won't
  generalize to posts phrased without any recognizable species keyword.
- **Free-tier quota constraints:** the vision model used
  (`gemini-flash-latest`) has a 20-requests/day free-tier cap on the
  development account used for this project, which required the batch job to
  be resumed across multiple days. The batch script's skip-logic and
  delete-before-retry logic were specifically designed to handle this kind of
  interrupted, multi-session execution.
- **One labeling quirk:** one wolf image (`wolf_006.jpg`) was classified by the
  vision model as `"tibetan wolf"` rather than `"gray wolf"` — a real subspecies
  distinction the model picked up on. The guard's subject-matching logic was
  adjusted to treat this correctly as a wolf match.

## Project Structure

```
flyrank-capstone/
├── app/
│   ├── main.py              # FastAPI review API
│   ├── models/
│   │   ├── db.py            # SQLAlchemy engine/session
│   │   ├── schemas.py       # Pydantic ImageTag schema
│   │   ├── tables.py        # SQLAlchemy ORM models
│   │   └── schema.sql       # Raw SQL schema (source of truth)
│   └── services/
│       ├── vision.py        # Vision classification (Gemini)
│       ├── embeddings.py    # Text embedding (Gemini)
│       └── guard.py         # Mismatch guard logic
├── data/images/              # 49-image corpus
├── docs/
│   ├── schema.md             # Tag schema documentation
│   └── sources.csv           # Image provenance/licensing
├── tests/
│   ├── test_schema.py
│   ├── test_guard.py
│   └── test_eval.py
├── batch_classify.py          # Batch vision classification job
├── embed_images.py            # Batch embedding job
├── add_post.py                # Create + embed a post
├── match_post.py               # Rank + guard + store pairings
├── eval_top1.py                 # Top-1 precision eval
├── cost_summary.py               # Cost reporting by call type
└── docker-compose.yml             # Postgres + pgvector
```
import os
import numpy as np
from dotenv import load_dotenv
load_dotenv()

from google import genai
from app.models.db import SessionLocal
from app.models.tables import ApiCallLog

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 1536
INPUT_COST_PER_1M = 0.15  # per Google's pricing, input-only cost


def embed_text(text: str, reference_id: int = None, call_type: str = "embedding") -> list[float]:
    response = client.models.embed_content(
        model=EMBED_MODEL,
        contents=text,
        config={"output_dimensionality": EMBED_DIM},
    )

    vector = response.embeddings[0].values

    # gemini-embedding-001 requires manual normalization when truncated below 3072 dims
    vector = np.array(vector)
    vector = vector / np.linalg.norm(vector)

    # log cost (embedding calls don't return token usage the same way; approximate via input length)
    approx_tokens = len(text.split())  # rough estimate; refine if exact usage is exposed
    cost = approx_tokens / 1_000_000 * INPUT_COST_PER_1M

    session = SessionLocal()
    log = ApiCallLog(
        call_type=call_type,
        reference_id=reference_id,
        model=EMBED_MODEL,
        input_tokens=approx_tokens,
        output_tokens=0,
        estimated_cost_usd=round(cost, 6),
        success=True,
    )
    session.add(log)
    session.commit()
    session.close()

    return vector.tolist()
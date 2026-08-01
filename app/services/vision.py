import os
from dotenv import load_dotenv
load_dotenv()

from google import genai
from app.models.schemas import ImageTag
from app.models.db import SessionLocal
from app.models.tables import ApiCallLog

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

MODEL_NAME = "gemini-flash-latest"

# Gemini Flash pricing (approx, per 1M tokens) - adjust if you confirm exact current rates
INPUT_COST_PER_1M = 0.075
OUTPUT_COST_PER_1M = 0.30

SYSTEM_PROMPT = """You are an image classification assistant for a wildlife/animal image library.
For the image provided, identify:
- subject: the specific species/breed shown (e.g. "red fox", "gray wolf", "husky")
- category: the broader taxonomic grouping (e.g. "canid")
- attributes: a list of 3-5 visually observable traits only (fur color, ear shape,
  tail shape/tip color, snout shape) - do NOT include traits that can't be seen in
  a photo, such as weight or behavior
- caption: one natural-language sentence describing the animal
- confidence: your certainty (0.0-1.0) that the "subject" identification is correct

Be conservative with confidence if the image is blurry, distant, or ambiguous."""


def log_api_call(reference_id, input_tokens, output_tokens, success, error_message=None):
    cost = (input_tokens / 1_000_000 * INPUT_COST_PER_1M) + \
           (output_tokens / 1_000_000 * OUTPUT_COST_PER_1M)
    session = SessionLocal()
    log = ApiCallLog(
        call_type="vision",
        reference_id=reference_id,
        model=MODEL_NAME,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=round(cost, 6),
        success=success,
        error_message=error_message,
    )
    session.add(log)
    session.commit()
    session.close()


def classify_image(filepath: str, image_id: int = None) -> ImageTag:
    with open(filepath, "rb") as f:
        image_bytes = f.read()

    ext = os.path.splitext(filepath)[1].lstrip(".").lower()
    mime_type = f"image/{'jpeg' if ext == 'jpg' else ext}"

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                SYSTEM_PROMPT,
                genai.types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": ImageTag,
            },
        )

        usage = response.usage_metadata
        log_api_call(image_id, usage.prompt_token_count, usage.candidates_token_count, success=True)

        return ImageTag.model_validate_json(response.text)

    except Exception as e:
        log_api_call(image_id, 0, 0, success=False, error_message=str(e))
        raise
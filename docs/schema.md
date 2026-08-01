# Vision Tag Schema

Each image is classified by the vision model into this structured shape:

​```json
{
  "subject": "red fox",
  "category": "canid",
  "attributes": ["reddish-orange fur", "large pointed ears", "bushy tail with white tip", "narrow pointed snout"],
  "caption": "The red fox is a highly intelligent and adaptable mammal known for its striking reddish fur, pointed snout, and bushy, white-tipped tail.",
  "confidence": 0.91
}
​```

## Field notes
- `subject`: specific identification (e.g. "red fox")
- `category`: broader grouping (e.g. "canid") — used for loose matching
- `attributes`: list of visually observable traits only (color, ear/tail/snout shape) —
  no traits that can't be seen in a typical photo (e.g. weight, behavior)
- `caption`: natural language sentence, human-readable
- `confidence`: float 0.0–1.0, model's certainty in `subject`

## Confidence rule
If `confidence < 0.7` → tag status = `needs_review`. Excluded from matching/ranking
until a human confirms it. Threshold may be tuned after seeing real eval results.
# lambda_validate.py

## Purpose
Performs **NLP (Natural Language Processing) validation** on extracted text using Amazon Comprehend. Analyzes the text for language, entities, key phrases, sentiment, and syntax quality to help assess whether OCR output is accurate and coherent.

## Trigger
`POST /validate` with JSON body `{"text": "..."}` via API Gateway HTTP API.

## AWS Services Used
- **Comprehend** — 5 synchronous API calls:
  - `detect_dominant_language`
  - `detect_entities`
  - `detect_key_phrases`
  - `detect_sentiment`
  - `detect_syntax`

## Configuration
- **Memory**: 128 MB
- **Timeout**: 15 seconds
- **Runtime**: Python 3.11

## IAM Permissions
Uses AWS managed policies:
- **AWSLambdaBasicExecutionRole**: CloudWatch Logs
- **ComprehendFullAccess**: NLP operations

## Environment Variables
None.

## Input
| Parameter | Source | Required | Description |
|-----------|--------|----------|-------------|
| `text`    | JSON body | Yes | The text to validate (truncated to 5000 chars) |

## Output
```json
{
  "languages": [{"code": "en", "score": 99.8}],
  "entities": [{"text": "London", "type": "LOCATION", "score": 99.2}],
  "key_phrases": [{"text": "image upload", "score": 98.5}],
  "sentiment": {"label": "NEUTRAL", "scores": {"positive": 1.2, "negative": 0.3, "neutral": 98.1, "mixed": 0.4}},
  "low_confidence_syntax": [{"text": "xk3", "tag": "NOUN", "score": 45.2}],
  "quality": {
    "rating": "good",
    "language_confidence": 99.8,
    "entity_count": 5,
    "key_phrase_count": 12,
    "suspicious_tokens": 0
  }
}
```

## Logic Flow
1. Parses JSON body, extracts `text`. Returns 400 if empty.
2. Truncates text to 5000 characters (Comprehend synchronous API limit).
3. **Step 1 — Language Detection**: Calls `detect_dominant_language`. Returns language codes with confidence scores (converted to %). Uses the top language code for all subsequent calls.
4. **Step 2 — Entity Detection**: Calls `detect_entities` with the detected language. Returns named entities (PERSON, LOCATION, DATE, ORGANIZATION, etc.) with confidence scores.
5. **Step 3 — Key Phrase Detection**: Calls `detect_key_phrases`. Returns significant phrases with confidence scores.
6. **Step 4 — Sentiment Analysis**: Calls `detect_sentiment`. Returns the dominant sentiment label (POSITIVE, NEGATIVE, NEUTRAL, MIXED) and per-sentiment confidence scores.
7. **Step 5 — Syntax Analysis (POS Tagging)**: Calls `detect_syntax`. Iterates all syntax tokens and flags any where the Part-of-Speech confidence is below 70% as "suspicious tokens" — these may indicate OCR errors (garbled text that doesn't parse as natural language).
8. **Quality Heuristic**: Computes an overall quality rating:
   - `poor` — language confidence < 80% OR suspicious tokens > 10
   - `fair` — language confidence < 95% OR suspicious tokens > 3
   - `good` — everything else

## Quality Rating Logic
| Rating | Condition |
|--------|-----------|
| `poor` | Language confidence < 80% OR > 10 suspicious tokens |
| `fair` | Language confidence < 95% OR > 3 suspicious tokens |
| `good` | Language confidence >= 95% AND <= 3 suspicious tokens |

## Critical Notes
- **5000-char limit** for Comprehend synchronous APIs. Text is truncated before processing.
- All confidence scores are converted from 0–1 floats to 0–100 percentages for consistency with the frontend display.
- The dominant language from step 1 is used as the `LanguageCode` parameter for steps 2–5.

## IAM Permissions Required
- `comprehend:DetectDominantLanguage`, `comprehend:DetectEntities`, `comprehend:DetectKeyPhrases`, `comprehend:DetectSentiment`, `comprehend:DetectSyntax` on `*`
- CloudWatch Logs

## Runtime
Python 3.11 | Timeout: 15s | Memory: 128MB

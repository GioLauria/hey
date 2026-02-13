import os
import json
import boto3

def lambda_handler(event, context):
    """Validate extracted text using Amazon Comprehend."""
    comprehend = boto3.client('comprehend', region_name='eu-west-2')

    # Parse body (POST request with JSON body)
    try:
        body = json.loads(event.get('body', '{}'))
    except Exception:
        body = {}

    text = body.get('text', '')
    if not text or not text.strip():
        return {
            'statusCode': 400,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Missing text parameter'})
        }

    # Truncate to 5000 bytes (Comprehend limit for synchronous calls)
    text = text[:5000]

    results = {}

    try:
        # 1. Detect dominant language
        lang_res = comprehend.detect_dominant_language(Text=text)
        languages = lang_res.get('Languages', [])
        results['languages'] = [
            {'code': l['LanguageCode'], 'score': round(l['Score'] * 100, 1)}
            for l in languages
        ]

        # Use the dominant language for subsequent calls
        lang_code = languages[0]['LanguageCode'] if languages else 'en'

        # 2. Detect entities (people, places, dates, etc.)
        ent_res = comprehend.detect_entities(Text=text, LanguageCode=lang_code)
        results['entities'] = [
            {
                'text': e['Text'],
                'type': e['Type'],
                'score': round(e['Score'] * 100, 1)
            }
            for e in ent_res.get('Entities', [])
        ]

        # 3. Detect key phrases
        kp_res = comprehend.detect_key_phrases(Text=text, LanguageCode=lang_code)
        results['key_phrases'] = [
            {
                'text': kp['Text'],
                'score': round(kp['Score'] * 100, 1)
            }
            for kp in kp_res.get('KeyPhrases', [])
        ]

        # 4. Detect sentiment
        sent_res = comprehend.detect_sentiment(Text=text, LanguageCode=lang_code)
        results['sentiment'] = {
            'label': sent_res.get('Sentiment', 'UNKNOWN'),
            'scores': {
                k.lower(): round(v * 100, 1)
                for k, v in sent_res.get('SentimentScore', {}).items()
            }
        }

        # 5. Detect syntax (POS tagging) - flag tokens with low confidence
        syntax_res = comprehend.detect_syntax(Text=text, LanguageCode=lang_code)
        low_confidence_tokens = []
        for token in syntax_res.get('SyntaxTokens', []):
            top_tag = token.get('PartOfSpeech', {})
            if top_tag.get('Score', 1) < 0.7:
                low_confidence_tokens.append({
                    'text': token.get('Text', ''),
                    'tag': top_tag.get('Tag', ''),
                    'score': round(top_tag.get('Score', 0) * 100, 1)
                })
        results['low_confidence_syntax'] = low_confidence_tokens

        # Summary: overall text quality assessment
        entity_count = len(results['entities'])
        phrase_count = len(results['key_phrases'])
        low_syntax_count = len(low_confidence_tokens)
        lang_score = results['languages'][0]['score'] if results['languages'] else 0

        # Heuristic quality score
        quality = 'good'
        if lang_score < 80 or low_syntax_count > 10:
            quality = 'poor'
        elif lang_score < 95 or low_syntax_count > 3:
            quality = 'fair'

        results['quality'] = {
            'rating': quality,
            'language_confidence': lang_score,
            'entity_count': entity_count,
            'key_phrase_count': phrase_count,
            'suspicious_tokens': low_syntax_count
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(results)
    }

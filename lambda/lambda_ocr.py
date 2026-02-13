import os
import json
import uuid
import boto3
import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from pypdf import PdfReader
import io

def lambda_handler(event, context):
    print("=== OCR Lambda v2.0 with pypdf support ===")
    print("Event:", json.dumps(event))
    
    # Test return - just return immediately
    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'message': 'Test response', 'event_received': bool(event)})
    }
    
    # Original code below - commented out for testing
    # bucket = os.environ['BUCKET']
    s3_client = boto3.client('s3', region_name='eu-west-2')
    s3_key = event.get('queryStringParameters', {}).get('s3_key')
    if s3_key:
        key = s3_key
        filename = key.split('/')[-1]
    else:
        # Backward compatibility for old format
        filename = event.get('queryStringParameters', {}).get('key')
        restaurant = event.get('queryStringParameters', {}).get('restaurant') or 'default'
        if not filename:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Missing s3_key or key parameter'})
            }
        # Try new location first
        key = f"r/turin/{restaurant}/{filename}"
        try:
            s3_client.head_object(Bucket=bucket, Key=key)
        except s3_client.exceptions.NoSuchKey:
            # Fall back to old location
            key = f"uploads/{filename}"

    textract = boto3.client('textract', region_name='eu-west-2')
    s3_client = boto3.client('s3', region_name='eu-west-2')
    print(f"About to check file type for: '{filename}'")
    
    # Initialize variables
    extracted_text = ""
    all_lines = []
    words = []
    avg_confidence = 0.0
    response = {'Blocks': []}
    
    # Check file type and process accordingly
    if filename.lower().endswith('.pdf'):
        print("DETECTED PDF FILE - Processing with pypdf")
        try:
            print("Getting PDF from S3...")
            # Get PDF from S3
            pdf_obj = s3_client.get_object(Bucket=bucket, Key=key)
            pdf_content = pdf_obj['Body'].read()
            print(f"Downloaded PDF, size: {len(pdf_content)} bytes")
            
            # Extract text using pypdf
            pdf_reader = PdfReader(io.BytesIO(pdf_content))
            print(f"PDF has {len(pdf_reader.pages)} pages")
            
            extracted_text = ""
            all_lines = []
            words = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                extracted_text += page_text + "\n\n"
                
                # Split into lines (approximate)
                lines = page_text.split('\n')
                for line_num, line in enumerate(lines):
                    line = line.strip()
                    if line:
                        all_lines.append({
                            'text': line,
                            'words': [{'text': word, 'confidence': 100.0} for word in line.split()],
                            'indent': 0
                        })
                        words.extend([{'text': word, 'confidence': 100.0, 'top': page_num * 100 + line_num * 20, 'left': 0} for word in line.split()])
            
            avg_confidence = 100.0  # PDFs don't have confidence scores
            response = {'Blocks': []}  # Dummy response for compatibility
                
        except Exception as e:
            error_str = str(e)
            print(f"PDF processing error: {error_str}")
            
            # Provide specific error messages for common PDF issues
            if 'password' in error_str.lower() or 'encrypted' in error_str.lower():
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'PDF is password-protected. Please provide an unprotected PDF.'})
                }
            elif 'format' in error_str.lower() or 'corrupt' in error_str.lower():
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'PDF appears to be corrupted or in an unsupported format. Please try a different PDF.'})
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': f'PDF processing failed: {error_str}'})
                }
                
    elif filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.tif')):
        print("DETECTED IMAGE FILE - Processing with Textract")
        try:
            # Use detect_document_text for images
            response = textract.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                }
            )
            print(f"Textract response received, blocks: {len(response.get('Blocks', []))}")
        except Exception as e:
            error_str = str(e)
            print(f"Textract error: {error_str}")
            
            # Provide more user-friendly error messages
            if 'UnsupportedDocumentException' in error_str:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Unsupported image format. Please try with PNG, JPG, or TIFF.'})
                }
            elif 'DocumentTooLargeException' in error_str:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Image is too large. Maximum size is 10MB.'})
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': f'Textract processing failed: {error_str}'})
                }
    else:
        print(f"UNSUPPORTED FILE TYPE: {filename}")
        return {
            'statusCode': 400,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Unsupported file type: {filename}. Supported formats: PDF, PNG, JPG, JPEG, TIFF'})
        }

    # Check for duplicate by s3_key instead of hash
    # dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
    # table = dynamodb.Table(table_name)
    # try:
    #     # Check if s3_key already exists
    #     check_response = table.scan(
    #         FilterExpression=boto3.dynamodb.conditions.Attr('s3_key').eq(key)
    #     )
    #     if check_response['Items']:
    #         # Already processed this exact file
    #         return {
    #             'statusCode': 409,
    #             'headers': {'Access-Control-Allow-Origin': '*'},
    #             'body': json.dumps({'error': 'File has already been processed'})
    #         }
    # except Exception as e:
    #     # If check fails, log but proceed
    #     print(f"Duplicate check error: {e}")

    # If this is an image, process Textract response
    # COMMENTED OUT FOR PDF DEBUGGING
    # if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.tif')):
    # COMMENTED OUT FOR PDF DEBUGGING
        # # Build a lookup of block ID -> block
        # blocks = response.get('Blocks', [])
        # block_map = {b['Id']: b for b in blocks}

        # # Build per-word confidence data: list of {text, confidence}
        # words = []
        # for b in blocks:
        #     if b['BlockType'] == 'WORD':
        #         words.append({
        #             'text': b.get('Text', ''),
        #             'confidence': round(b.get('Confidence', 0), 1),
        #             'top': b.get('Geometry', {}).get('BoundingBox', {}).get('Top', 0),
        #             'left': b.get('Geometry', {}).get('BoundingBox', {}).get('Left', 0)
        #         })

        # # Compute average confidence
        # avg_confidence = 0
        # if words:
        #         avg_confidence = round(sum(w['confidence'] for w in words) / len(words), 1)

        # # Collect lines in order
        # lines = [b for b in blocks if b['BlockType'] == 'LINE']
        # lines.sort(key=lambda b: b.get('Geometry', {}).get('BoundingBox', {}).get('Top', 0))

        # sections = []
        # all_lines = []

        # for line in lines:
        #     top = line.get('Geometry', {}).get('BoundingBox', {}).get('Top', 0)
        #     left = line.get('Geometry', {}).get('BoundingBox', {}).get('Left', 0)
        #     # Get per-word confidence for this line
        #     line_words = []
        #     for rel in line.get('Relationships', []):
        #         if rel['Type'] == 'CHILD':
        #             for wid in rel['Ids']:
        #             w = block_map.get(wid)
        #             if w and w['BlockType'] == 'WORD':
        #                 line_words.append({
        #                     'text': w.get('Text', ''),
        #                     'confidence': round(w.get('Confidence', 0), 1)
        #                 })
        #     indent = int(left * 80)
        #     sections.append(' ' * indent + line['Text'])
        #     all_lines.append({'text': line['Text'], 'words': line_words, 'indent': indent})

        # # Fallback
        # if not sections:
        #     for b in blocks:
        #         if b['BlockType'] == 'LINE':
        #             sections.append(b['Text'])
        #             all_lines.append({'text': b['Text'], 'words': [], 'indent': 0})

        # extracted_text = '\n'.join(sections)

    # Save to DynamoDB
    item_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    item = {
        'id': item_id,
        'filename': filename,
        's3_key': key,
        'text': extracted_text,
        'line_count': len(all_lines),
        'avg_confidence': Decimal(str(avg_confidence)),
        'timestamp': timestamp
    }
    if hash_value:
        item['hash'] = hash_value
    # Temporarily disable database writes for testing
    try:
        table.put_item(Item=item)
        print(f"Successfully saved to DynamoDB: {item_id}")
    except Exception as e:
        print(f"DynamoDB write error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Failed to save results: {str(e)}'})
        }

    # Insert record into tblUploads
    # try:
    #     # Extract restaurant_id from s3_key (format: r/restaurant_id/filename)
    #     s3_key_parts = key.split('/')
    #     if len(s3_key_parts) >= 3 and s3_key_parts[0] == 'r':
    #         restaurant_id = int(s3_key_parts[1])
            
    #         # Database connection
    #         conn = pg8000.connect(
    #             host=os.environ['DB_HOST'],
    #             port=5432,
    #             user='postgres',
    #             password='password123',
    #             database='hey'
    #         )
    #         cursor = conn.cursor()
            
    #         # Insert into tblUploads
    #         cursor.execute(
    #             'INSERT INTO tblUploads (Restaurant_ID, S3_Path) VALUES (%s, %s)',
    #             (restaurant_id, key)
    #         )
    #         conn.commit()
    #         conn.close()
    #         print(f"Inserted upload record for restaurant {restaurant_id}: {key}")
    #     else:
    #         print(f"Could not parse restaurant_id from s3_key: {key}")
    # except Exception as e:
    #     print(f"Database insert error for tblUploads: {e}")

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({
            'text': extracted_text,
            'lines': all_lines,
            'key': key,
            'id': item_id,
            'timestamp': timestamp,
            'avg_confidence': avg_confidence,
            'words': words
        })
    }
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Unexpected error: {str(e)}'})
        }

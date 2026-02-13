import os
import json
import boto3
import urllib.request
import urllib.error
from datetime import datetime, timezone
import re

def lambda_handler(event, context):
    table_name = os.environ['TABLE_NAME']
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
    table = dynamodb.Table(table_name)

    # Get visitor IP from API Gateway request context
    ip = (event.get('requestContext', {}).get('http', {}).get('sourceIp', '')
          or event.get('headers', {}).get('x-forwarded-for', '').split(',')[0].strip())

    if not ip or ip == 'unknown':
        ip = 'unknown'

    # Extract additional data from request
    headers = event.get('headers', {})
    user_agent = headers.get('user-agent', '')
    accept_language = headers.get('accept-language', '')
    referer = headers.get('referer', '')

    # Parse User-Agent
    browser_info = parse_user_agent(user_agent)

    # Get geolocation data
    geo_data = get_geolocation(ip) if ip != 'unknown' else {}

    # Current timestamp
    now = datetime.now(timezone.utc).isoformat()

    # Prepare visitor data
    visitor_data = {
        'ip': ip,
        'visit': now,
        'user_agent': user_agent,
        'browser': browser_info.get('browser', 'Unknown'),
        'browser_version': browser_info.get('version', 'Unknown'),
        'os': browser_info.get('os', 'Unknown'),
        'device_type': browser_info.get('device', 'Unknown'),
        'referer': referer,
        'country': geo_data.get('country_name', 'Unknown'),
        'city': geo_data.get('city', 'Unknown'),
        'region': geo_data.get('region', 'Unknown'),
        'timezone': geo_data.get('timezone', 'Unknown'),
        'isp': geo_data.get('org', 'Unknown')
    }

    # Try to update existing visitor or create new one
    try:
        # First, try to get existing visitor data
        response = table.get_item(Key={'ip': ip})
        existing_visitor = response.get('Item')

        if existing_visitor:
            # Update existing visitor - just update the visit timestamp and other fields
            # Build update expression and values
            update_expression = 'SET visit = :t, user_agent = :ua, browser = :b, browser_version = :bv, os = :os, device_type = :dt, referer = :r'
            expression_values = {
                ':t': now,
                ':ua': user_agent,
                ':b': browser_info.get('browser', 'Unknown'),
                ':bv': browser_info.get('version', 'Unknown'),
                ':os': browser_info.get('os', 'Unknown'),
                ':dt': browser_info.get('device', 'Unknown'),
                ':r': referer
            }
            expression_names = {}

            # Only update geolocation fields if we have valid data
            if geo_data:
                update_expression += ', country = :co, city = :ci, #region = :re, #timezone = :tz, isp = :isp'
                expression_values.update({
                    ':co': geo_data.get('country_name', 'Unknown'),
                    ':ci': geo_data.get('city', 'Unknown'),
                    ':re': geo_data.get('region', 'Unknown'),
                    ':tz': geo_data.get('timezone', 'Unknown'),
                    ':isp': geo_data.get('org', 'Unknown')
                })
                expression_names.update({
                    '#region': 'region',
                    '#timezone': 'timezone'
                })

            update_params = {
                'Key': {'ip': ip},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_values
            }
            if expression_names:
                update_params['ExpressionAttributeNames'] = expression_names

            table.update_item(**update_params)
        else:
            # Create new visitor
            table.put_item(Item=visitor_data)

    except Exception as e:
        print(f"Database operation error: {e}")
        # Fallback: just update visit if record exists, or create minimal record
        try:
            table.put_item(
                Item={
                    'ip': ip,
                    'visit': now,
                    'user_agent': user_agent
                },
                ConditionExpression='attribute_not_exists(ip)'
            )
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            table.update_item(
                Key={'ip': ip},
                UpdateExpression='SET visit = :t',
                ExpressionAttributeValues={':t': now}
            )

    # Get total unique visitor count
    count = 0
    try:
        response = table.scan(Select='COUNT')
        count = response.get('Count', 0)
    except Exception as e:
        print(f"Scan error: {e}")

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'count': count})
    }

def parse_user_agent(user_agent):
    """Parse User-Agent string to extract browser, OS, and device info"""
    if not user_agent:
        return {'browser': 'Unknown', 'version': 'Unknown', 'os': 'Unknown', 'device': 'Unknown'}

    # Browser detection
    browsers = {
        'Chrome': r'Chrome/(\d+)',
        'Firefox': r'Firefox/(\d+)',
        'Safari': r'Version/(\d+).*Safari',
        'Edge': r'Edg/(\d+)',
        'Opera': r'OPR/(\d+)',
        'IE': r'MSIE (\d+)'
    }

    browser = 'Unknown'
    version = 'Unknown'

    for name, pattern in browsers.items():
        match = re.search(pattern, user_agent, re.IGNORECASE)
        if match:
            browser = name
            version = match.group(1)
            break

    # OS detection
    os_patterns = {
        'Windows': r'Windows NT (\d+\.\d+)',
        'macOS': r'Mac OS X (\d+[_\.]\d+)',
        'Linux': r'Linux',
        'Android': r'Android (\d+)',
        'iOS': r'iPhone|iPad|iPod'
    }

    os = 'Unknown'
    for name, pattern in os_patterns.items():
        if re.search(pattern, user_agent, re.IGNORECASE):
            os = name
            break

    # Device type detection
    device = 'Unknown'
    user_agent_lower = user_agent.lower()
    
    if 'tv' in user_agent_lower or 'smarttv' in user_agent_lower or 'googletv' in user_agent_lower or 'appletv' in user_agent_lower or 'roku' in user_agent_lower or 'firetv' in user_agent_lower:
        device = 'TV'
    elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower or 'kindle' in user_agent_lower or 'playbook' in user_agent_lower:
        device = 'Tablet'
    elif 'mobile' in user_agent_lower or 'android' in user_agent_lower or 'iphone' in user_agent_lower or 'blackberry' in user_agent_lower or 'windows phone' in user_agent_lower or 'opera mini' in user_agent_lower:
        device = 'Mobile'
    elif 'console' in user_agent_lower or 'playstation' in user_agent_lower or 'xbox' in user_agent_lower or 'nintendo' in user_agent_lower or 'wii' in user_agent_lower:
        device = 'Console'
    elif 'bot' in user_agent_lower or 'crawler' in user_agent_lower or 'spider' in user_agent_lower or 'scraper' in user_agent_lower:
        device = 'Bot'
    else:
        device = 'Desktop'

    return {
        'browser': browser,
        'version': version,
        'os': os,
        'device': device
    }

def get_geolocation(ip):
    """Get geolocation data for an IP address using ipapi.co"""
    if ip == 'unknown' or ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
        return {}

    try:
        with urllib.request.urlopen(f'http://ipapi.co/{ip}/json/', timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            return {
                'country_name': data.get('country_name', 'Unknown'),
                'country_code': data.get('country_code', 'Unknown'),
                'city': data.get('city', 'Unknown'),
                'region': data.get('region', 'Unknown'),
                'timezone': data.get('timezone', 'Unknown'),
                'org': data.get('org', 'Unknown')
            }
    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        print(f"Geolocation error for {ip}: {e}")

    return {}

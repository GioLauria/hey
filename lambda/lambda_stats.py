import boto3
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

# Custom JSON encoder for Decimal objects
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        # Check if this is a request for detailed statistics
        query_params = event.get('queryStringParameters') or {}
        if query_params.get('stats') == 'detailed':
            return get_detailed_stats()
        else:
            return get_visitor_count()
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }

def get_visitor_count():
    """Get total unique visitor count"""
    try:
        response = table.scan(Select='COUNT')
        count = response['Count']

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'count': count})
        }
    except Exception as e:
        print(f"Error getting visitor count: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Failed to get visitor count'})
        }

def get_detailed_stats():
    """Get detailed visitor statistics"""
    try:
        # Scan all visitors
        response = table.scan()
        visitors = response['Items']

        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            visitors.extend(response['Items'])

        # Calculate statistics
        stats = analyze_visitors(visitors)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(stats, default=decimal_default)
        }
    except Exception as e:
        print(f"Error getting detailed stats: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Failed to get statistics'})
        }
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Failed to get statistics'})
        }

def analyze_visitors(visitors):
    """Analyze visitor data and return statistics"""
    now = datetime.utcnow()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Initialize counters
    total_visitors = len(visitors)
    today_visitors = 0
    week_visitors = 0
    month_visitors = 0

    browser_counts = defaultdict(int)
    os_counts = defaultdict(int)
    country_counts = defaultdict(int)
    device_counts = defaultdict(int)
    recent_visitors = []

    for visitor in visitors:
        try:
            # Parse visit timestamp - handle both old and new record formats
            visit_str = visitor.get('visit', '')
            
            if not visit_str:
                # Handle old records with first_visit/last_visit
                last_visit_str = visitor.get('last_visit', '')
                if not last_visit_str:
                    # Skip records without any timestamps
                    continue
                visit_str = last_visit_str

            visit = datetime.fromisoformat(visit_str.replace('Z', '+00:00'))

            # Count visitors by time period
            if visit.date() == today:
                today_visitors += 1
            if visit.date() >= week_ago:
                week_visitors += 1
            if visit.date() >= month_ago:
                month_visitors += 1

            # Count browsers
            browser = visitor.get('browser', 'Unknown')
            if browser:
                browser_counts[browser] += 1

            # Count operating systems
            os = visitor.get('os', 'Unknown')
            if os:
                os_counts[os] += 1

            # Count countries
            country = visitor.get('country', 'Unknown')
            if country:
                country_counts[country] += 1

            # Count device types
            device = visitor.get('device_type', 'Unknown')
            if device:
                device_counts[device] += 1

            # Collect recent visitors (last 10)
            if len(recent_visitors) < 10:
                recent_visitors.append({
                    'ip': visitor.get('ip', 'Unknown'),
                    'country': visitor.get('country', 'Unknown'),
                    'city': visitor.get('city', 'Unknown'),
                    'browser': visitor.get('browser', 'Unknown'),
                    'os': visitor.get('os', 'Unknown'),
                    'device_type': visitor.get('device_type', 'Unknown'),
                    'visit': visit_str
                })

        except Exception as e:
            print(f"Error processing visitor {visitor.get('ip')}: {str(e)}")
            # Skip visitors with invalid data
            continue

    # Sort recent visitors by visit (most recent first)
    recent_visitors.sort(key=lambda x: x['visit'], reverse=True)

    # Convert defaultdicts to sorted lists
    def sort_dict_desc(d):
        return sorted(d.items(), key=lambda x: x[1], reverse=True)[:10]  # Top 10

    return {
        'total_visitors': total_visitors,
        'today_visitors': today_visitors,
        'week_visitors': week_visitors,
        'month_visitors': month_visitors,
        'browsers': sort_dict_desc(browser_counts),
        'operating_systems': sort_dict_desc(os_counts),
        'countries': sort_dict_desc(country_counts),
        'devices': sort_dict_desc(device_counts),
        'recent_visitors': recent_visitors
    }
# site/stats.html

## Purpose
Dedicated **visitor statistics and analytics page** accessible by clicking the visitor count on the main page. Provides comprehensive visitor insights including total counts, time-based breakdowns, browser/OS/country distributions, device types, and recent visitor details.

## Navigation
- **Accessed from**: Clickable visitor count number on `index.html`
- **Back navigation**: "← Back to Main Page" button at bottom
- **URL**: `stats.html` (served from S3 via CloudFront)

## Layout & Sections

### Header
- Hey logo at top center
- "Visitor Statistics" title
- Debug div (hidden by default) for troubleshooting

### Statistics Grid (4 cards)
- **Total Visitors**: All-time unique visitor count
- **Today's Visitors**: Visitors from current day
- **This Week**: Visitors from past 7 days
- **This Month**: Visitors from past 30 days

### Charts Section
- **Top Browsers**: Bar chart showing browser distribution
- **Top Operating Systems**: Bar chart showing OS distribution
- **Top Countries**: Bar chart showing geographic distribution
- **Device Types**: Bar chart showing device categories (Desktop/Mobile/Tablet)

### Recent Visitors Table
- Shows last 10 visitors with details:
  - IP address
  - Country and city
  - Browser and OS
  - Device type
- Loading state: "Loading visitor data..." initially
- Error handling: Shows error messages if API fails

## API Integration
- **Endpoint**: `GET /stats?stats=detailed`
- **Data Source**: Calls `loadStatistics()` on page load
- **Dynamic URL**: Uses `window.APP_CONFIG.apiUrl` from `config.js`
- **Response Format**: JSON with visitor counts, distributions, and recent visitor array

## Dependencies
- `config.js` — For API URL configuration
- `script.js` — For `loadStatistics()` and `displayStatistics()` functions
- `styles.css` — For consistent styling with main page

## Error Handling
- Network failures show error messages in recent visitors section
- Debug information logged to console and optional debug div
- Graceful fallbacks for missing data

## Mobile Responsiveness
- Responsive grid layout that stacks on smaller screens
- Charts adapt to container width
- Touch-friendly navigation buttons</content>
<parameter name="filePath">c:\Users\giova\OneDrive\Development\HeyAWS\scripts\stats_html.md
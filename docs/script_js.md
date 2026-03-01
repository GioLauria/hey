# script.js

## Purpose
Main frontend JavaScript file for the OCR web application. Handles all client-side functionality including OCR processing, UI interactions, API calls, visitor tracking, statistics display, and feature management (to-do lists, menu, cache, costs).

## Key Features
- **OCR Processing**: File upload, SHA256 hashing, progress tracking, result display
- **Visitor Analytics**: Automatic visitor tracking with geolocation and user agent parsing
- **Statistics Dashboard**: Loads and displays visitor statistics with charts and tables
- **To-Do Management**: CRUD operations for task management
- **Menu System**: Dynamic menu display and management
- **Cache Management**: Cache clearing and statistics
- **Cost Tracking**: AWS service cost monitoring
- **UI Components**: Overlay modals, tab switching, history management, confidence bars

## API Endpoints Used
- `POST /ocr` — OCR processing
- `GET /presign` — S3 upload URLs
- `GET /history` — OCR history
- `GET /counter` — Visitor count
- `GET /stats?stats=detailed` — Detailed statistics
- `GET /todos` — To-do list
- `POST /todos` — Create to-do
- `PUT /todos/{id}` — Update to-do
- `DELETE /todos/{id}` — Delete to-do
- `GET /menu` — Menu items
- `POST /menu` — Add menu item
- `DELETE /menu/{id}` — Remove menu item
- `GET /cache` — Cache statistics
- `DELETE /cache` — Clear cache
- `GET /costs` — Cost data

## Global Variables
| Variable | Description |
|----------|-------------|
| `isLocalDevelopment` | Boolean flag for HTTP vs HTTPS environment |
| `apiUrl` | API Gateway base URL (from `window.APP_CONFIG.apiUrl` with fallback) |
| `siteBaseUrl` | Current site origin |
| `currentExtractionId` | Currently displayed OCR result ID |

## Core Functions

### OCR Processing
- `computeSHA256(file)` — Generates SHA256 hash for file deduplication
- `uploadFile(file)` — Handles file upload to S3 via presigned URL
- `processOCR(file)` — Main OCR processing workflow
- `displayResults(data)` — Renders OCR results in overlay
- `loadHistory()` — Loads and displays OCR history

### Visitor Tracking
- `trackVisitor()` — Records visitor data with geolocation
- `getGeolocation()` — Fetches IP geolocation data
- `parseUserAgent()` — Extracts browser/OS info from user agent

### Statistics
- `loadStatistics()` — Fetches and displays visitor analytics
- `displayStatistics(data)` — Populates stats dashboard with counts, charts, and tables
- `displayChart(containerId, data, label)` — Renders bar charts for browsers, OS, countries, and device types
- `displayRecentVisitors(visitors)` — Shows recent visitor table with device information

### UI Management
- `setProgress(pct, label)` — Updates progress bar
- `resetUI()` — Resets form state
- `switchTab(tab)` — Handles tab switching
- `showOverlay(type, data)` — Displays modal overlays
- `closeOverlay()` — Closes modals

### Feature Functions
- `loadTodos()` / `addTodo()` / `updateTodo()` / `deleteTodo()` — To-do CRUD
- `loadMenu()` / `addMenuItem()` / `removeMenuItem()` — Menu management
- `loadCacheStats()` / `clearCache()` — Cache operations
- `loadCosts()` — Cost monitoring

## Event Listeners
- Form submission for OCR uploads
- Tab clicks for navigation
- Button clicks for various actions
- **Visitor counter clicks** — Navigate to stats page
- Page load for visitor tracking and stats loading

## Dependencies
- External APIs: ipapi.co for geolocation
- Browser APIs: File API, Fetch API, Crypto API, Geolocation API
- DOM manipulation for dynamic UI updates

## Error Handling
- Network error catching with user-friendly messages
- CORS handling for cross-origin requests
- Fallbacks for missing browser features
- Console logging for debugging

## Browser Compatibility
- Modern browsers with ES6+ support
- HTTPS required for geolocation and some APIs
- Progressive enhancement for optional features
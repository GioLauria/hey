# site/index.html

## Purpose
Single-page **frontend web application** for the OCR service. Provides image upload, extraction history, text viewing with confidence highlighting, text editing, NLP validation, and a visitor counter. Hosted as a static website on S3 with CloudFront CDN and WAF protection.

## Hosting
**CloudFront CDN** distribution with HTTPS and WAF protection at `https://<cloudfront-domain>.cloudfront.net`
- S3 static website as origin with Origin Access Identity
- Automatic HTTPS redirect from HTTP
- Web Application Firewall (WAF) with comprehensive security rules:
  - AWS Managed Rules Common Rule Set
  - SQL Injection protection
  - Known bad inputs filtering
  - Bot control and management
- Direct S3 access still available at `http://ocr-site-<hex>.s3-website.eu-west-2.amazonaws.com`

## API Endpoint
All API calls use the dynamic API Gateway endpoint loaded from `config.js`:
```javascript
window.APP_CONFIG.apiUrl  // Set by Terraform outputs
```

This ensures the frontend automatically uses the correct API Gateway URL without hardcoding.

## Sections & Features

### 1. Upload Section (top card)
- File input accepting `image/*` files.
- **Restaurant dropdown** — select from 10 Turin restaurants (e.g., "Del Cambio", "La Piola") with values like `turin_delcambio_1234`.
- "Extract Text" submit button — disabled during processing.
- **Progress bar** with animated blue gradient showing stages:
  - 10% — Getting presigned URL
  - 30% — Uploading to S3
  - 50% — Upload complete
  - 60% — Starting OCR
  - 80% — Processing
  - 100% — Done
- Status text updates at each step.

### 2. Extraction History (second card)
- Loaded automatically on page load via `GET /extractions`.
- Each row displays:
  - **Filename** (bold, truncated with ellipsis)
  - **"Corrected" badge** (green) if text was manually edited
  - **Metadata**: date/time, line count, average confidence %
  - **"View" button** — opens overlay with text + image
  - **Delete icon** (✕) — confirms, then calls `DELETE /extractions?id=<id>`, removes row from DOM
- "Refresh" button to reload the list.

### 3. Overlay/Modal (triggered by View or after OCR)
- Full-screen dark backdrop, centered white modal (780px max).
- **Image display** at top — loaded from the same S3 bucket (`window.location.origin + '/' + filename`).
- **Confidence meter** — horizontal bar showing average confidence colored green/yellow/red.
- **Four-tab interface**:

  #### Tab 1: Confidence View (default)
  - Renders text with per-word color-coded highlighting:
    - Green (`conf-high`): confidence >= 95%
    - Yellow (`conf-med`): confidence >= 80%
    - Red (`conf-low`): confidence < 80%
  - Each word has a hover tooltip showing exact confidence %.
  - Falls back to plain text for history items (no per-word data available).

  #### Tab 2: Edit Text
  - Editable `<textarea>` pre-filled with extracted text.
  - "Save Corrections" button appears in footer (green).
  - Saves via `PUT /extractions` with `{id, text}`.
  - Shows "Saving..."/"Saved!" feedback, refreshes history on success.

  #### Tab 3: NLP Validation
  - Initially shows a prompt to click the validate button.
  - After running, displays Amazon Comprehend results:
    - **Quality badge** (good/fair/poor with color)
    - **Language detection** with confidence
    - **Sentiment** label
    - **Entities** (up to 30, with type labels)
    - **Key phrases** (up to 20, purple tags)
    - **Suspicious tokens** (red tags for low-confidence syntax)

  #### Tab 4: Menu (new feature)
  - Displays menu items associated with the extraction via `GET /menu?extraction_id=<id>`.
  - Each menu item shows:
    - AI-generated dish image (from S3)
    - Dish name, description, ingredients list, time to serve, price to public
  - "Add Menu Item" button opens a form for creating new items.
  - Form includes fields for dish name, description, dynamic ingredients (add/remove rows), TTS, PTB.
  - "Generate AI Image" button — generates image using Bedrock based on dish name and ingredients, previews it.
  - "Save" button — saves via POST/PUT to `/menu`, refreshes the list.
  - Edit/Delete buttons per item — edit pre-fills the form, delete confirms and removes via DELETE.

- **Footer buttons**:
  - Left: "Copy Text", "Run NLP Validation" (yellow)
  - Right: "Save Corrections" (green, edit tab only), "Close" (gray)

### 4. Visitor Counter
- Displayed below the history section, centered.
- On page load, calls `GET /counter` to record the visit and fetch the count.
- Shows "N unique visitors" with the number displayed as **clickable underlined text**.
- **Clicking the visitor count** navigates to `stats.html` for detailed visitor analytics.
- Uses event listener for reliable click handling instead of inline onclick.

### 5. Cache Controls
- Interactive cache refresh controls at the bottom of the page.
- **Status Display**: Shows current cache refresh interval and next refresh time.
- **Immediate Refresh Button**: "Refresh Now" button that triggers CloudFront invalidation with loading state and success/error feedback.
- **Interval Selector**: Dropdown with options: Immediate (0 min), 1 minute, 5 minutes, 10 minutes, 15 minutes, 30 minutes, 1 hour.
- Updates display when interval changes, but actual CloudFront TTL is set to 0 (no caching).

### 6. Cost Dashboard Panel (right side)
- **Controlled by `site/config.js`** — only shown when `window.APP_CONFIG.showCostPanel` is `true`.
- Fixed-position panel on the right side of the page (320px wide, resizable up to 496px).
- **Header**: Dark background with "AWS Costs" title and current period label. Collapsible via ▲/▼ toggle button (starts collapsed by default, showing only the toggle).
- **Period toggle**: "This Month" / "This Year" buttons to switch between current month and year-to-date costs.
- **Total section**: Shows total cost for the selected period in USD (2 decimal places). Label updates dynamically.
- **Services list**: Scrollable list of all project AWS services with costs > $0.00 (free tier hidden), sorted by cost descending then alphabetically. Each row shows service name and cost ($X.XX).
- On page load, if config flag is true, calls `GET /costs?period=month` and renders the data.
- Error handling: shows error message if the cost API fails.
- Z-index 900 (below the extraction overlay).

### 7. To-Do Panel (left side)
- Fixed-position panel on the left side of the page (top: 20px; left: 20px).
- **Header**: "To-Do Lists" title with ▲/▼ toggle button (starts collapsed by default).
- **Add Task**: Input field with placeholder "Add new task..." and "Add" button. Enter key also adds tasks.
- **Task List**: Shows all tasks with checkboxes for completion, task text, and delete (×) button.
- **Completed Tasks**: Visually distinguished with strikethrough and grayed-out styling.
- On page load, calls `GET /todos` to load all tasks.
- Tasks refresh automatically after add/delete/toggle operations.
- Z-index: 800 (below cost panel).
- **Responsive**: On screens ≤768px, repositions to bottom of screen; on screens ≤480px, spans full width with reduced padding.

## JavaScript Functions

| Function | Description |
|----------|-------------|
| `setProgress(pct, label)` | Updates progress bar width and status text |
| `resetUI()` | Re-enables submit button, hides progress bar |
| `switchTab(tab)` | Switches between confidence/edit/validate tabs, toggles save button |
| `showOverlay(text, title, imageKey, ocrData)` | Opens modal with image, confidence bar, tabbed text views |
| `hideOverlay()` | Closes the modal, clears current extraction ID |
| `formatDate(iso)` | Formats ISO timestamp to locale date + time |
| `loadHistory()` | Fetches and renders extraction history from API |
| `escapeHtml(s)` | Escapes HTML entities for safe rendering |
| `escapeAttr(s)` | Escapes attribute values (quotes, angle brackets) |
| `viewExtraction(btn)` | Opens overlay for a history item using data attributes |
| `deleteExtraction(btn)` | Confirms and deletes an extraction, removes DOM element |
| `saveCorrection()` | Sends edited text to `PUT /extractions`, refreshes history |
| `runValidation()` | Posts text to `POST /validate`, renders Comprehend results |
| `toggleCostPanel()` | Collapses/expands the cost dashboard panel |
| `loadCosts()` | Fetches cost data from `GET /costs` and renders services list |
| `loadTodos()` | Fetches and renders To-Do items from `GET /todos` |
| `addTodo()` | Creates new To-Do item via `POST /todos` |
| `deleteTodo(id)` | Deletes To-Do item via `DELETE /todos?id=<id>` |
| `toggleTodo(id)` | Updates To-Do completion status via `PUT /todos` |
| `toggleTodoPanel()` | Collapses/expands the To-Do panel |
| `invalidateCache()` | Triggers CloudFront cache invalidation via `POST /cache/invalidate` |
| `updateCacheTime()` | Updates cache display when interval selector changes |

## API Calls Made

| Method | Endpoint | When |
|--------|----------|------|
| `GET` | `/presign?key=<filename>` | On form submit (step 1) |
| `PUT` | Presigned S3 URL | On form submit (step 2) — direct to S3 |
| `GET` | `/ocr?key=<filename>` | On form submit (step 3) |
| `GET` | `/extractions` | On page load, after OCR, after save |
| `DELETE` | `/extractions?id=<id>` | On delete button click |
| `PUT` | `/extractions` | On save corrections |
| `POST` | `/validate` | On "Run NLP Validation" click |
| `GET` | `/counter` | On page load |
| `GET` | `/costs` | On page load (if `showCostPanel` is true) |
| `GET` | `/todos` | On page load, after add/delete/toggle |
| `POST` | `/todos` | On add task |
| `PUT` | `/todos` | On task completion toggle |
| `DELETE` | `/todos?id=<id>` | On task delete |
| `POST` | `/cache/invalidate` | On "Refresh Now" button click |

## Styling
- Segoe UI font, `#f0f2f5` background, white cards with 12px border-radius and subtle shadows.
- Logo image (hey.png) centered at top of container.
- Favicon set to hey.png.
- Page max-width: 496px (centered).
- Cost panel: starts collapsed, resizable up to 496px width, hides free tier services, shows costs rounded to 2 decimals.
- Responsive: max-width containers, flex-wrap for form elements.
- **Mobile responsive cost panel**: On screens ≤768px, moves to bottom of screen with page padding-bottom to prevent overlap; on screens ≤480px, spans full width with reduced padding.
- Color scheme: blue primary (`#2563eb`), green success (`#16a34a`), yellow warning (`#ca8a04`), red danger (`#ef4444`), gray secondary (`#6b7280`).

## Critical Notes
- The `Content-Type: application/octet-stream` header in the S3 PUT upload **must match** the presigned URL's `ContentType` parameter.
- Image URLs are constructed from `window.location.origin` — this works because images and the HTML are in the same S3 bucket.
- The `currentExtractionId` variable tracks which extraction is open in the overlay for save operations.

// Check if we're running on HTTP (local development)
const isLocalDevelopment = window.location.protocol === 'http:';

console.log('Script loaded, current URL:', window.location.href);

if (isLocalDevelopment) {
  console.warn('Running on HTTP - To-Do list may not work due to mixed content policy. Use production site: https://d1qc6fbrksmxtc.cloudfront.net');
}
let form, statusEl, progressWrap, progressBar, submitBtn, overlay, overlayTitle, historyList, confText, editArea, saveBtn, confidenceBar, confidenceFill, confidenceLabel;
const siteBaseUrl = window.location.origin;
const apiUrl = (window.APP_CONFIG && window.APP_CONFIG.apiUrl) || "https://nrnnywp9u0.execute-api.eu-west-2.amazonaws.com";
const imageBaseUrl = (window.APP_CONFIG && window.APP_CONFIG.imageBaseUrl) || siteBaseUrl;

let currentExtractionId = null;

// Restaurant data from tblRistoranti
const restaurants = [
  { id: 1, name: 'Trattoria Roma' },
  { id: 2, name: 'Pizzeria Napoli' },
  { id: 3, name: 'Osteria Milano' },
  { id: 4, name: 'Ristorante Firenze' },
  { id: 5, name: 'Bar Torino' }
];

function populateRestaurantSelect() {
  const select = document.getElementById('restaurantSelect');
  select.innerHTML = '<option value="">Select Restaurant</option>';
  restaurants.forEach(r => {
    const option = document.createElement('option');
    option.value = r.id;
    option.textContent = r.name;
    select.appendChild(option);
  });
}

function setProgress(pct, label) {
  progressWrap.style.display = 'block';
  progressBar.style.width = pct + '%';
  if (label) statusEl.innerText = label;
}

function resetUI() {
  submitBtn.disabled = false;
  progressWrap.style.display = 'none';
  progressBar.style.width = '0%';
}

async function computeSHA256(file) {
  const buffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

function switchTab(tab) {
  document.querySelectorAll('.overlay-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
  document.getElementById('tab-' + tab).classList.add('active');
  saveBtn.style.display = tab === 'edit' ? '' : 'none';
  if (tab === 'menu') {
    loadMenu();
  }
}

function showOverlay(text, title, imageKey, ocrData) {
  overlayTitle.innerText = title;
  currentExtractionId = ocrData ? ocrData.id : null;

  // Confidence bar
  if (ocrData && ocrData.avg_confidence !== undefined && confidenceBar && confidenceFill && confidenceLabel) {
    const avg = ocrData.avg_confidence;
    confidenceBar.style.display = 'flex';
    confidenceFill.style.width = avg + '%';
    confidenceFill.style.background = avg >= 95 ? '#22c55e' : avg >= 80 ? '#eab308' : '#ef4444';
    confidenceLabel.innerText = avg + '%';
  } else if (confidenceBar) {
    confidenceBar.style.display = 'none';
  }

  // Confidence-highlighted text
  if (ocrData && ocrData.lines && ocrData.lines.length > 0 && ocrData.lines[0].words) {
    let html = '';
    ocrData.lines.forEach((line, i) => {
      if (i > 0) html += '<br>';
      const indent = line.indent || 0;
      if (indent > 0) html += '&nbsp;'.repeat(indent);
      line.words.forEach((w, j) => {
        const cls = w.confidence >= 95 ? 'conf-high' : w.confidence >= 80 ? 'conf-med' : 'conf-low';
        html += `<span class="conf-word ${cls}" title="${w.confidence}%">${escapeHtml(w.text)}</span>`;
        if (j < line.words.length - 1) html += ' ';
      });
    });
    confText.innerHTML = html;
  } else {
    confText.innerText = text || '(No text detected)';
  }

  // Edit area
  editArea.value = text || '';

  // Reset validate panel
  document.getElementById('validateResults').innerHTML = '<p style="color:#888">Click "Run NLP Validation" to analyze the text with Amazon Comprehend.</p>';

  // Default to confidence tab
  switchTab('confidence');
  overlay.classList.add('active');
}

function hideOverlay() {
  overlay.classList.remove('active');
  currentExtractionId = null;
}

function formatDate(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  } catch(e) { return iso; }
}

async function loadHistory() {
  historyList.innerHTML = '<li class="history-loading">Loading...</li>';
  try {
    const res = await fetch(`${apiUrl}/extractions`);
    if (!res.ok) throw new Error('Failed to load');
    const data = await res.json();
    const items = data.extractions || [];
    if (items.length === 0) {
      historyList.innerHTML = '<li class="history-empty">No extractions yet. Upload an image to get started!</li>';
      return;
    }
    historyList.innerHTML = '';
    items.forEach(item => {
      const li = document.createElement('li');
      const lines = item.line_count || 0;
      const conf = item.avg_confidence !== undefined ? ` &bull; ${item.avg_confidence}%` : '';
      const corrected = item.corrected ? '<span class="badge-corrected">Corrected</span>' : '';
      const fileWarning = item.file_exists === false ? '<span class="file-warning" title="Original file not found in S3">⚠️ File Missing</span>' : '';
      li.innerHTML = `
        <div class="history-item-info">
          <div class="history-item-name">${escapeHtml(item.filename)}${corrected}${fileWarning}</div>
          <div class="history-item-meta">${formatDate(item.timestamp)} &mdash; ${lines} line${lines !== 1 ? 's' : ''}${conf}</div>
        </div>
        <div class="history-item-actions">
          <button class="history-item-btn" onclick="viewExtraction(this)" data-text="${escapeAttr(item.text)}" data-filename="${escapeAttr(item.filename)}" data-s3-key="${escapeAttr(item.s3_key)}" data-timestamp="${escapeAttr(item.timestamp)}" data-id="${escapeAttr(item.id)}" data-conf="${item.avg_confidence || ''}">View</button>
          <button class="history-item-download" onclick="downloadExtraction(this)" data-s3-key="${escapeAttr(item.s3_key)}" data-filename="${escapeAttr(item.filename)}" title="Download Original File">📥</button>
        </div>
        <button class="history-item-delete" onclick="deleteExtraction(this)" data-id="${escapeAttr(item.id)}" title="Delete">&times;</button>
      `;
      historyList.appendChild(li);
    });
  } catch (err) {
    historyList.innerHTML = '<li class="history-empty">Failed to load history.</li>';
    console.error(err);
  }
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}
function escapeAttr(s) {
  return (s || '').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function viewExtraction(btn) {
  const text = btn.getAttribute('data-text');
  const filename = btn.getAttribute('data-filename');
  const s3Key = btn.getAttribute('data-s3-key');
  const timestamp = btn.getAttribute('data-timestamp');
  const id = btn.getAttribute('data-id');
  const conf = btn.getAttribute('data-conf');
  const ocrData = {
    id: id,
    avg_confidence: conf ? parseFloat(conf) : undefined,
    lines: null
  };
  showOverlay(text, filename + ' \u2014 ' + formatDate(timestamp), s3Key, ocrData);
}

function downloadExtraction(btn) {
  const s3Key = btn.getAttribute('data-s3-key');
  const filename = btn.getAttribute('data-filename');
  if (s3Key) {
    const link = document.createElement('a');
    link.href = imageBaseUrl + '/' + encodeURIComponent(s3Key);
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

async function deleteExtraction(btn) {
  const id = btn.getAttribute('data-id');
  if (!confirm('Delete this extraction?')) return;
  try {
    const res = await fetch(`${apiUrl}/extractions?id=${encodeURIComponent(id)}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Delete failed');
    const li = btn.closest('li');
    if (li) li.remove();
    if (historyList.children.length === 0) {
      historyList.innerHTML = '<li class="history-empty">No extractions yet. Upload an image to get started!</li>';
    }
  } catch (err) {
    alert('Failed to delete: ' + err.message);
    console.error(err);
  }
}

async function saveCorrection() {
  if (!currentExtractionId) { alert('No extraction to save.'); return; }
  const correctedText = editArea.value;
  saveBtn.disabled = true;
  saveBtn.innerText = 'Saving...';
  try {
    const res = await fetch(`${apiUrl}/extractions`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: currentExtractionId, text: correctedText })
    });
    if (!res.ok) throw new Error('Save failed');
    saveBtn.innerText = 'Saved!';
    setTimeout(() => { saveBtn.innerText = 'Save Corrections'; saveBtn.disabled = false; }, 1500);
    loadHistory();
  } catch (err) {
    alert('Failed to save: ' + err.message);
    saveBtn.innerText = 'Save Corrections';
    saveBtn.disabled = false;
  }
}

async function runValidation() {
  const text = editArea.value || confText.innerText;
  if (!text || !text.trim()) { alert('No text to validate.'); return; }
  const panel = document.getElementById('validateResults');
  panel.innerHTML = '<p style="color:#888">Analyzing text with Amazon Comprehend...</p>';
  switchTab('validate');
  try {
    const res = await fetch(`${apiUrl}/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    });
    if (!res.ok) throw new Error('Validation failed: ' + res.status);
    const data = await res.json();
    let html = '';

    // Quality rating
    if (data.quality) {
      const q = data.quality;
      const cls = q.rating === 'good' ? 'quality-good' : q.rating === 'fair' ? 'quality-fair' : 'quality-poor';
      html += `<div class="validate-section"><h3>Overall Quality</h3>
        <span class="quality-badge ${cls}">${q.rating}</span>
        <span style="margin-left:12px;font-size:0.85rem;color:#555">Language confidence: ${q.language_confidence}% &bull; ${q.entity_count} entities &bull; ${q.key_phrase_count} key phrases &bull; ${q.suspicious_tokens} suspicious tokens</span>
      </div>`;
    }

    // Languages
    if (data.languages && data.languages.length > 0) {
      html += `<div class="validate-section"><h3>Detected Languages</h3>`;
      data.languages.forEach(l => { html += `<span class="entity-tag">${l.code} (${l.score}%)</span>`; });
      html += '</div>';
    }

    // Sentiment
    if (data.sentiment) {
      html += `<div class="validate-section"><h3>Sentiment</h3>
        <span class="entity-tag">${data.sentiment.label}</span></div>`;
    }

    // Entities
    if (data.entities && data.entities.length > 0) {
      html += `<div class="validate-section"><h3>Entities Detected</h3>`;
      data.entities.slice(0, 30).forEach(e => {
        html += `<span class="entity-tag" title="${e.type}: ${e.score}%">${escapeHtml(e.text)} <small>(${e.type})</small></span>`;
      });
      if (data.entities.length > 30) html += `<span style="color:#888;font-size:0.8rem"> +${data.entities.length - 30} more</span>`;
      html += '</div>';
    }

    // Key phrases
    if (data.key_phrases && data.key_phrases.length > 0) {
      html += `<div class="validate-section"><h3>Key Phrases</h3>`;
      data.key_phrases.slice(0, 20).forEach(kp => {
        html += `<span class="phrase-tag" title="${kp.score}%">${escapeHtml(kp.text)}</span>`;
      });
      if (data.key_phrases.length > 20) html += `<span style="color:#888;font-size:0.8rem"> +${data.key_phrases.length - 20} more</span>`;
      html += '</div>';
    }

    // Suspicious tokens
    if (data.low_confidence_syntax && data.low_confidence_syntax.length > 0) {
      html += `<div class="validate-section"><h3>Suspicious Tokens (low syntax confidence)</h3>`;
      data.low_confidence_syntax.forEach(t => {
        html += `<span class="suspicious-tag" title="${t.tag}: ${t.score}%">${escapeHtml(t.text)}</span>`;
      });
      html += '</div>';
    }

    panel.innerHTML = html || '<p style="color:#888">No issues detected.</p>';
  } catch (err) {
    panel.innerHTML = `<p style="color:#ef4444">Validation error: ${escapeHtml(err.message)}</p>`;
    console.error(err);
  }
}

// Menu functions
let currentMenuItems = [];

async function loadMenu() {
  const list = document.getElementById('menuList');
  list.innerHTML = 'Loading menu items...';
  try {
    const res = await fetch(`${apiUrl}/menu?extraction_id=${currentExtractionId}`);
    if (res.ok) {
      const data = await res.json();
      currentMenuItems = data.menu_items;
      if (data.menu_items.length === 0) {
        list.innerHTML = '<p style="color:#888">No menu items yet. Add one below.</p>';
      } else {
        list.innerHTML = '';
        data.menu_items.forEach(item => {
          const div = document.createElement('div');
          div.className = 'menu-item';
          div.innerHTML = `
            <img src="${siteBaseUrl}/${encodeURIComponent(item.image_key)}" alt="${escapeHtml(item.dish_name)}">
            <div class="menu-item-details">
              <div class="menu-item-name">${escapeHtml(item.dish_name)}</div>
              <div class="menu-item-desc">${escapeHtml(item.description)}</div>
              <div class="menu-item-ingredients">Ingredients: ${item.ingredients.map(i => `${i.quantity} ${i.name}`).join(', ')}</div>
              <div class="menu-item-meta">TTS: ${escapeHtml(item.tts)} | Price: $${item.ptb}</div>
            </div>
            <div class="menu-item-actions">
              <button onclick="editMenuItem('${item.id}')">Edit</button>
              <button onclick="deleteMenuItem('${item.id}')" class="btn-danger">Delete</button>
            </div>
          `;
          list.appendChild(div);
        });
      }
    } else {
      list.innerHTML = '<p style="color:#ef4444">Failed to load menu items.</p>';
    }
  } catch (err) {
    list.innerHTML = '<p style="color:#ef4444">Error loading menu: ' + escapeHtml(err.message) + '</p>';
  }
}

function showMenuForm(item = null) {
  const form = document.getElementById('menuForm');
  const title = document.getElementById('menuFormTitle');
  if (item) {
    title.textContent = 'Edit Menu Item';
    document.getElementById('menuDishName').value = item.dish_name;
    document.getElementById('menuDescription').value = item.description;
    document.getElementById('menuTTS').value = item.tts;
    document.getElementById('menuPTB').value = item.ptb;
    const ingList = document.getElementById('ingredientsList');
    ingList.innerHTML = '';
    item.ingredients.forEach(ing => {
      addIngredient(ing.name, ing.quantity);
    });
    if (item.image_key) {
      document.getElementById('menuImagePreview').src = siteBaseUrl + '/' + encodeURIComponent(item.image_key);
      document.getElementById('menuImagePreview').style.display = 'block';
    }
    form.dataset.editId = item.id;
  } else {
    title.textContent = 'Add New Menu Item';
    form.reset();
    document.getElementById('ingredientsList').innerHTML = '<div class="ingredient-row"><input type="text" placeholder="Ingredient" class="ing-name"><input type="text" placeholder="Quantity" class="ing-qty"><button onclick="removeIngredient(this)">Remove</button></div>';
    document.getElementById('menuImagePreview').style.display = 'none';
    delete form.dataset.editId;
  }
  form.style.display = 'block';
}

function hideMenuForm() {
  document.getElementById('menuForm').style.display = 'none';
}

function addIngredient(name = '', qty = '') {
  const row = document.createElement('div');
  row.className = 'ingredient-row';
  row.innerHTML = `<input type="text" placeholder="Ingredient" class="ing-name" value="${escapeHtml(name)}"><input type="text" placeholder="Quantity" class="ing-qty" value="${escapeHtml(qty)}"><button onclick="removeIngredient(this)">Remove</button>`;
  document.getElementById('ingredientsList').appendChild(row);
}

function removeIngredient(btn) {
  btn.parentElement.remove();
}

async function generateImage() {
  const dishName = document.getElementById('menuDishName').value;
  const ingredients = Array.from(document.querySelectorAll('.ing-name')).map((el, i) => ({
    name: el.value,
    quantity: document.querySelectorAll('.ing-qty')[i].value
  })).filter(ing => ing.name);
  if (!dishName) {
    alert('Enter dish name first');
    return;
  }
  const btn = event.target;
  btn.disabled = true;
  btn.textContent = 'Generating...';
  try {
    const res = await fetch(`${apiUrl}/menu`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        extraction_id: currentExtractionId,
        dish_name: dishName,
        description: document.getElementById('menuDescription').value,
        ingredients: ingredients,
        tts: document.getElementById('menuTTS').value,
        ptb: parseFloat(document.getElementById('menuPTB').value) || 0
      })
    });
    if (res.ok) {
      const data = await res.json();
      document.getElementById('menuImagePreview').src = siteBaseUrl + '/' + encodeURIComponent(data.image_key);
      document.getElementById('menuImagePreview').style.display = 'block';
      alert('Image generated! Now save the item.');
    } else {
      alert('Failed to generate image');
    }
  } catch (err) {
    alert('Error: ' + err.message);
  }
  btn.disabled = false;
  btn.textContent = 'Generate AI Image';
}

async function saveMenuItem() {
  const form = document.getElementById('menuForm');
  const dishName = document.getElementById('menuDishName').value;
  const ingredients = Array.from(document.querySelectorAll('.ing-name')).map((el, i) => ({
    name: el.value,
    quantity: document.querySelectorAll('.ing-qty')[i].value
  })).filter(ing => ing.name);
  if (!dishName) {
    alert('Dish name is required');
    return;
  }
  const body = {
    extraction_id: currentExtractionId,
    dish_name: dishName,
    description: document.getElementById('menuDescription').value,
    ingredients: ingredients,
    tts: document.getElementById('menuTTS').value,
    ptb: parseFloat(document.getElementById('menuPTB').value) || 0
  };
  const method = form.dataset.editId ? 'PUT' : 'POST';
  if (method === 'PUT') body.id = form.dataset.editId;
  try {
    const res = await fetch(`${apiUrl}/menu`, {
      method: method,
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    if (res.ok) {
      hideMenuForm();
      loadMenu();
    } else {
      alert('Failed to save');
    }
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

function editMenuItem(id) {
  const item = currentMenuItems.find(i => i.id === id);
  if (item) {
    showMenuForm(item);
  }
}

async function deleteMenuItem(id) {
  if (!confirm('Delete this menu item?')) return;
  try {
    const res = await fetch(`${apiUrl}/menu?id=${id}`, { method: 'DELETE' });
    if (res.ok) {
      loadMenu();
    } else {
      alert('Failed to delete');
    }
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

document.addEventListener('DOMContentLoaded', function() {
  form = document.getElementById('uploadForm');
  statusEl = document.getElementById('status');
  progressWrap = document.getElementById('progressWrap');
  progressBar = document.getElementById('progressBar');
  submitBtn = document.getElementById('submitBtn');
  overlay = document.getElementById('overlay');
  overlayTitle = document.getElementById('overlayTitle');
  historyList = document.getElementById('historyList');
  confText = document.getElementById('confText');
  editArea = document.getElementById('editArea');
  saveBtn = document.getElementById('saveBtn');
  confidenceBar = document.getElementById('confidenceBar');
  confidenceFill = document.getElementById('confidenceFill');
  confidenceLabel = document.getElementById('confidenceLabel');

  document.getElementById('overlayClose').onclick = hideOverlay;
  document.getElementById('closeBtn').onclick = hideOverlay;
  document.getElementById('copyBtn').onclick = function() {
    const text = editArea.value || confText.innerText;
    navigator.clipboard.writeText(text);
    this.innerText = 'Copied!';
    setTimeout(() => { this.innerText = 'Copy Text'; }, 1500);
  };
  overlay.onclick = function(e) { if (e.target === overlay) hideOverlay(); };

  form.onsubmit = async function(e) {
    e.preventDefault();
    const file = document.getElementById('imageInput').files[0];
    const restaurant = document.getElementById('restaurantSelect').value;
    if (!file) return;
    if (!restaurant) {
      statusEl.innerText = 'Please select a restaurant.';
      return;
    }
    submitBtn.disabled = true;
    statusEl.innerText = '';

    try {
      setProgress(5, 'Computing file hash...');
      const hash = await computeSHA256(file);

      setProgress(10, 'Getting upload URL...');
      const presignRes = await fetch(`${apiUrl}/presign?key=${encodeURIComponent(file.name)}&hash=${hash}&restaurant=${encodeURIComponent(restaurant)}`);
      if (!presignRes.ok) {
        if (presignRes.status === 409) {
          statusEl.innerText = 'This image has already been processed.';
        } else {
          statusEl.innerText = 'Failed to get upload URL.';
        }
        resetUI();
        return;
      }
      const { url, s3_key } = await presignRes.json();

      setProgress(30, 'Uploading image...');
      const uploadRes = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/octet-stream' },
        body: file
      });
      if (!uploadRes.ok) {
        const errText = await uploadRes.text();
        statusEl.innerText = 'Upload failed: ' + errText;
        resetUI();
        return;
      }
      setProgress(50, 'Image uploaded. Starting OCR...');

      setProgress(60, 'Extracting text from image...');
      const ocrRes = await fetch(`${apiUrl}/ocr?s3_key=${encodeURIComponent(s3_key)}`);
      setProgress(80, 'Processing...');
      if (!ocrRes.ok) {
        const errBody = await ocrRes.text();
        statusEl.innerText = 'OCR failed: ' + ocrRes.status + ' ' + errBody;
        resetUI();
        return;
      }
      const ocrData = await ocrRes.json();
      setProgress(100, 'Done!');

      const txt = ocrData.text && ocrData.text.trim().length > 0 ? ocrData.text : '(No text detected in this image)';
      showOverlay(txt, 'Extracted Text \u2014 ' + file.name, s3_key, ocrData);
      statusEl.innerText = ocrData.text && ocrData.text.trim().length > 0 ? 'Text extracted successfully!' : 'No text found in the image.';

      loadHistory();
    } catch (err) {
      statusEl.innerText = 'Error: ' + err.message;
      console.error(err);
    }
    resetUI();
  };

  // Visitor counter
  (async function() {
    try {
      const res = await fetch(`${apiUrl}/counter`);
      if (res.ok) {
        const data = await res.json();
        const counterElement = document.getElementById('visitorCounter');
        counterElement.innerHTML = '<span id="visitorCount" style="cursor: pointer; text-decoration: underline;">' + data.count + '</span> unique visitor' + (data.count !== 1 ? 's' : '');
        
        // Add click event listener
        document.getElementById('visitorCount').addEventListener('click', function(e) {
          e.preventDefault();
          window.location.href = 'stats.html';
        });
      }
    } catch(e) { console.error('Counter error:', e); }
  })();

  loadHistory();
});



// Cache note
let currentCacheMinutes = 0;

function updateCacheDisplay() {
  const now = new Date();
  const statusEl = document.getElementById('cacheStatus');

  if (!statusEl) return;

  if (currentCacheMinutes === 0) {
    statusEl.innerHTML = 'CDN cache: Immediate refresh (no caching)';
  } else {
    const minutes = now.getMinutes();
    const nextClear = new Date(now);
    nextClear.setMinutes(Math.ceil((minutes + 1) / currentCacheMinutes) * currentCacheMinutes, 0, 0);
    const timeString = nextClear.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    statusEl.innerHTML = `CDN cache refreshes every ${currentCacheMinutes} minute${currentCacheMinutes !== 1 ? 's' : ''} (next: ${timeString})`;
  }
}

function updateCacheTime() {
  const select = document.getElementById('cacheTimeSelect');
  currentCacheMinutes = parseInt(select.value);
  updateCacheDisplay();

  // Note: This only updates the display. Actual CloudFront TTL would need to be changed via API
  console.log(`Cache time updated to ${currentCacheMinutes} minutes`);
}

async function invalidateCache() {
  const btn = document.getElementById('immediateRefreshBtn');
  const originalText = btn.innerHTML;
  btn.innerHTML = 'Refreshing...';
  btn.disabled = true;

  try {
    const response = await fetch(`${apiUrl}/cache/invalidate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        paths: ['/*']  // Invalidate all paths
      })
    });

    if (response.ok) {
      const data = await response.json();
      console.log('Cache invalidation created:', data);
      alert(`Cache refresh initiated! Status: ${data.status}\nInvalidation ID: ${data.invalidation_id}`);
    } else {
      const error = await response.json();
      throw new Error(error.error || 'Failed to invalidate cache');
    }
  } catch (err) {
    console.error('Cache invalidation failed:', err);
    alert('Failed to refresh cache: ' + err.message);
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

// Initialize cache display
document.addEventListener('DOMContentLoaded', function() {
  updateCacheDisplay();
  populateRestaurantSelect();
});

// Load restaurants from API
async function populateRestaurantSelect() {
  const select = document.getElementById('restaurantSelect');
  try {
    const response = await fetch(`${apiUrl}/restaurants`);
    if (!response.ok) throw new Error('Failed to load restaurants');
    const restaurants = await response.json();
    select.innerHTML = '<option value="">Select Restaurant</option>';
    restaurants.forEach(r => {
      const option = document.createElement('option');
      option.value = r.id;
      option.textContent = r.name;
      select.appendChild(option);
    });
  } catch (error) {
    console.error('Error loading restaurants:', error);
    // Fallback to hardcoded
    select.innerHTML = '<option value="">Select Restaurant</option>';
    restaurants.forEach(r => {
      const option = document.createElement('option');
      option.value = r.id;
      option.textContent = r.name;
      select.appendChild(option);
    });
  }
}

// Cost panel (toggle from config.js)
let currentCostPeriod = 'month';

function toggleCostPanel() {
  const panel = document.getElementById('costPanel');
  const btn = panel.querySelector('.cost-panel-toggle');
  panel.classList.toggle('collapsed');
  btn.innerHTML = panel.classList.contains('collapsed') ? '&#x25BC;' : '&#x25B2;';
}

function switchCostPeriod(period) {
  currentCostPeriod = period;
  document.getElementById('periodMonth').classList.toggle('active', period === 'month');
  document.getElementById('periodYear').classList.toggle('active', period === 'year');
  document.getElementById('costLabel').textContent = period === 'year' ? 'Total This Year' : 'Total This Month';
  document.getElementById('costTotal').innerHTML = '<span class="currency">Loading...</span>';
  document.getElementById('costServices').innerHTML = '<li class="cost-loading">Fetching cost data...</li>';
  loadCosts(period);
}

async function loadCosts(period) {
  period = period || currentCostPeriod;
  const panel = document.getElementById('costPanel');
  const cacheKey = `costData_${period}`;
  const cacheDateKey = `costData_${period}_date`;
  
  // Check if we have cached data from today
  const cachedData = localStorage.getItem(cacheKey);
  const cachedDate = localStorage.getItem(cacheDateKey);
  const today = new Date().toDateString(); // Gets date string like "Tue Feb 11 2026"
  
  if (cachedData && cachedDate === today) {
    console.log('Using cached cost data for period:', period, 'from today');
    const data = JSON.parse(cachedData);
    updateCostDisplay(data, period);
    return;
  }
  
  try {
    console.log('Fetching fresh cost data for period:', period);
    const res = await fetch(`${apiUrl}/costs?period=${period}`);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    
    // Cache the data with today's date
    localStorage.setItem(cacheKey, JSON.stringify(data));
    localStorage.setItem(cacheDateKey, today);
    
    updateCostDisplay(data, period);
  } catch (err) {
    document.getElementById('costServices').innerHTML = '<li class="cost-error">Failed to load costs: ' + escapeHtml(err.message) + '</li>';
    console.error('Cost panel error:', err);
  }
}

function updateCostDisplay(data, period) {
  document.getElementById('costMonth').textContent = data.label;
  document.getElementById('costLabel').textContent = data.period === 'year' ? 'Total This Year' : 'Total This Month';
  document.getElementById('costTotal').innerHTML = '$' + data.total.toFixed(2) + ' <span class="currency">' + data.currency + '</span>';
  const ul = document.getElementById('costServices');
  if (data.services.length === 0) {
    ul.innerHTML = '<li class="cost-loading">No costs recorded yet.</li>';
  } else {
    // Filter out free tier services
    data.services = data.services.filter(s => s.amount > 0);
    ul.innerHTML = '';
    data.services.forEach(s => {
      const li = document.createElement('li');
      li.innerHTML = '<span class="svc-name">' + escapeHtml(s.service) + '</span><span class="svc-amount">$' + s.amount.toFixed(2) + '</span>';
      ul.appendChild(li);
    });
  }
}

// Init cost panel from config
(function() {
  console.log('Init cost panel, APP_CONFIG:', window.APP_CONFIG);
  if (window.APP_CONFIG && window.APP_CONFIG.showCostPanel) {
    console.log('Showing cost panel');
    const panel = document.getElementById('costPanel');
    panel.style.display = 'flex';
    panel.classList.add('collapsed');
    const btn = panel.querySelector('.cost-panel-toggle');
    btn.innerHTML = '&#x25BC;';
    console.log('Panel classes:', panel.className);
    loadCosts();
  } else {
    console.log('Cost panel disabled');
  }
})();

// To-Do List Functions
async function loadTodos() {
  console.log('loadTodos called');
  try {
    const ul = document.getElementById('todoList');
    if (!ul) {
      console.warn('todoList element not found, skipping loadTodos');
      return;
    }
    console.log('Fetching todos from:', `${apiUrl}/todos`);
    const response = await fetch(`${apiUrl}/todos`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
      // Remove mode: 'cors' for local development to avoid mixed content issues
    });
    console.log('Response status:', response.status);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    console.log('Received data:', data);
    ul.innerHTML = '';
    if (data.todos) {
      data.todos.forEach((todo) => {
        const li = document.createElement('li');
        li.className = todo.completed ? 'completed' : '';
        li.innerHTML = `
          <input type="checkbox" ${todo.completed ? 'checked' : ''} onchange="toggleTodo('${todo.id}')">
          <span>${escapeHtml(todo.text)}</span>
          <button onclick="deleteTodo('${todo.id}')">&times;</button>
        `;
        ul.appendChild(li);
      });
      console.log('Todos loaded successfully');
    } else {
      console.log('No todos found');
    }
  } catch (err) {
    console.error('Failed to load todos:', err);
    // Show error in the UI
    const ul = document.getElementById('todoList');
    if (ul) {
      if (isLocalDevelopment && err.message.includes('Mixed Content') || err.message.includes('CORS')) {
        ul.innerHTML = '<li style="color: orange;">⚠️ Local development: Use production site for full functionality<br><a href="https://d1qc6fbrksmxtc.cloudfront.net" target="_blank" style="color: blue;">Open Production Site</a></li>';
      } else {
        ul.innerHTML = `<li style="color: red;">Error loading todos: ${err.message}</li>`;
      }
    }
  }
}

async function addTodo() {
  const input = document.getElementById('newTodoInput');
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;
  try {
    const response = await fetch(`${apiUrl}/todos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, completed: false })
    });
    if (response.ok) {
      input.value = '';
      loadTodos();
    }
  } catch (err) {
    console.error('Failed to add todo:', err);
  }
}

async function deleteTodo(id) {
  try {
    const response = await fetch(`${apiUrl}/todos?id=${id}`, {
      method: 'DELETE'
    });
    if (response.ok) {
      loadTodos();
    }
  } catch (err) {
    console.error('Failed to delete todo:', err);
  }
}

async function toggleTodo(id) {
  try {
    // First get current state
    const response = await fetch(`${apiUrl}/todos`);
    const data = await response.json();
    const todo = data.todos.find(t => t.id === id);
    if (todo) {
      const updateResponse = await fetch(`${apiUrl}/todos`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, completed: !todo.completed })
      });
      if (updateResponse.ok) {
        loadTodos();
      }
    }
  } catch (err) {
    console.error('Failed to toggle todo:', err);
  }
}

function toggleTodoPanel() {
  const panel = document.getElementById('todoPanel');
  if (!panel) return;
  panel.classList.toggle('collapsed');
  const btn = panel.querySelector('.todo-panel-toggle');
  if (btn) {
    btn.innerHTML = panel.classList.contains('collapsed') ? '&#x25B2;' : '&#x25BC;';
  }
}

function handleTodoKeyPress(event) {
  if (event.key === 'Enter') {
    addTodo();
  }
}

// Init todo panel
document.addEventListener('DOMContentLoaded', async function() {
  console.log('DOM loaded, initializing todo panel');
  const panel = document.getElementById('todoPanel');
  if (!panel) {
    console.warn('todoPanel element not found, skipping todo initialization');
    return;
  }
  console.log('todoPanel found, loading todos');
  await loadTodos();
  panel.classList.add('collapsed');
  const btn = panel.querySelector('.todo-panel-toggle');
  if (btn) {
    btn.innerHTML = '&#x25B2;';
  }
  console.log('Todo panel initialized');
});

// Statistics page functionality
function goBack() {
  window.location.href = 'index.html';
}

// Load statistics when on stats page
if (window.location.pathname.includes('stats.html') || window.location.href.includes('stats.html')) {
  console.log('Loading statistics page...');
  loadStatistics();
}

async function loadStatistics() {
  console.log('loadStatistics called');
  try {
    const apiUrl = (window.APP_CONFIG && window.APP_CONFIG.apiUrl) || "https://nrnnywp9u0.execute-api.eu-west-2.amazonaws.com";
    console.log('Fetching from:', `${apiUrl}/stats?stats=detailed`);
    const res = await fetch(`${apiUrl}/stats?stats=detailed`, {
      method: 'GET',
      mode: 'cors',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    console.log('Response status:', res.status);
    console.log('Response headers:', res.headers);
    if (res.ok) {
      const responseText = await res.text();
      console.log('Raw response text:', responseText);
      try {
        const data = JSON.parse(responseText);
        console.log('Data received:', data);
        displayStatistics(data);
      } catch (parseError) {
        console.error('JSON parse error:', parseError);
        document.querySelector('.recent-visitors .loading').textContent = `JSON parse error: ${parseError.message}`;
      }
    } else {
      const errorText = await res.text();
      console.error('Failed to load statistics:', res.status, errorText);
      document.querySelector('.recent-visitors .loading').textContent = `Failed to load statistics: ${res.status}`;
      document.getElementById('debugDiv').textContent += ` - API call failed: ${res.status}`;
    }
  } catch(e) {
    console.error('Statistics error:', e);
    document.querySelector('.recent-visitors .loading').textContent = `Error loading statistics: ${e.message}`;
    document.getElementById('debugDiv').textContent += ` - Exception: ${e.message}`;
  }
}

function displayStatistics(data) {
  console.log('displayStatistics called with data:', data);

  // Update summary cards
  const totalEl = document.getElementById('totalVisitors');
  const todayEl = document.getElementById('todayVisitors');
  const weekEl = document.getElementById('weekVisitors');
  const monthEl = document.getElementById('monthVisitors');

  console.log('Elements found:', {totalEl, todayEl, weekEl, monthEl});

  if (totalEl) {
    totalEl.textContent = data.total_visitors || 0;
    console.log('Updated totalVisitors to:', data.total_visitors);
  }
  if (todayEl) {
    todayEl.textContent = data.today_visitors || 0;
    console.log('Updated todayVisitors to:', data.today_visitors);
  }
  if (weekEl) {
    weekEl.textContent = data.week_visitors || 0;
    console.log('Updated weekVisitors to:', data.week_visitors);
  }
  if (monthEl) {
    monthEl.textContent = data.month_visitors || 0;
    console.log('Updated monthVisitors to:', data.month_visitors);
  }

  console.log('Summary cards updated');

  // Display browser statistics
  displayChart('browserChart', data.browsers, 'Browser');

  // Display OS statistics
  displayChart('osChart', data.operating_systems, 'Operating System');

  // Display country statistics
  displayChart('countryChart', data.countries, 'Country');

  // Display device statistics
  displayChart('deviceChart', data.devices, 'Device Type');

  // Display recent visitors
  displayRecentVisitors(data.recent_visitors);

  console.log('displayStatistics completed');
}

function displayChart(containerId, data, label) {
  const container = document.getElementById(containerId);
  if (!data || data.length === 0) {
    container.innerHTML = `<div style="text-align: center; color: #64748b; padding: 40px;">No ${label.toLowerCase()} data available</div>`;
    return;
  }

  const maxValue = Math.max(...data.map(item => item[1]));
  const html = data.map(([name, count]) => {
    const percentage = maxValue > 0 ? (count / maxValue) * 100 : 0;
    // Leave space for the value text (about 60px) and cap at 80% to prevent overlap
    const displayPercentage = Math.min(percentage * 0.8, 80);
    return `
      <div class="chart-bar">
        <span class="chart-label">${name}</span>
        <div class="chart-bar-fill" style="width: ${displayPercentage}%"></div>
        <span class="chart-value" style="left: calc(${displayPercentage}% + 8px)">${count}</span>
      </div>
    `;
  }).join('');

  container.innerHTML = html;
}

function displayRecentVisitors(visitors) {
  const container = document.querySelector('.recent-visitors');
  if (!visitors || visitors.length === 0) {
    container.innerHTML = '<div style="text-align: center; color: #64748b; padding: 40px;">No recent visitors</div>';
    return;
  }

  // Sort visitors by visit datetime, most recent first
  visitors.sort((a, b) => new Date(b.visit) - new Date(a.visit));

  const tableHtml = `
    <table>
      <thead>
        <tr>
          <th>Visit Time</th>
          <th>IP Address</th>
          <th>Location</th>
          <th>Browser</th>
          <th>OS</th>
          <th>Device</th>
        </tr>
      </thead>
      <tbody>
        ${visitors.map(visitor => `
          <tr>
            <td>${new Date(visitor.visit).toLocaleString()}</td>
            <td>${visitor.ip}</td>
            <td>${visitor.city}, ${visitor.country}</td>
            <td>${visitor.browser}</td>
            <td>${visitor.os}</td>
            <td>${visitor.device_type}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  container.innerHTML = tableHtml;
}

window.addEventListener('load', populateRestaurantSelect);
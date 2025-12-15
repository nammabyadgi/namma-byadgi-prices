# ============================================================================
# BYADGI CHILLI PRICES - INTERACTIVE DASHBOARD GENERATOR (FIXED)
# ============================================================================
# 
# FIXED: Extract variety name from line FIRST, then extract prices
#
# ============================================================================

import os
import re
import sys
import json
import logging
from datetime import datetime
from PIL import Image
import pytesseract
import pandas as pd
import numpy as np
from dateutil import parser as dateparser

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_FOLDER = r'C:\Users\mrmay\Downloads\APMC Prices\Prices'
OUTPUT_FOLDER = r'C:\Users\mrmay\Downloads\APMC Prices\web'
TESSERACT_CMD = None

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(OUTPUT_FOLDER, 'generation.log'), encoding='utf-8')
    ]
)

# ============================================================================
# CANONICAL VARIETY NAMES - Source of Truth
# ============================================================================

# ---- REPLACE VARIETY_PATTERNS and CANONICAL_VARIETIES ----
CANONICAL_VARIETIES = [
    'Syngenta 2043',
    'Syngenta 5531',
    'Syngenta 102',
    'Kashmiri (Dabbi)',
    'Byadgi (KDL)',
    'Local KDL',
    'Devanur Deluxe (DD)',
    'Guntur S-10',
    'Seed Quality',
]
# Patterns (ordered - most specific first). Use robust word boundaries and OCR-friendly alternatives.
VARIETY_PATTERNS = [
    (r'\b2043\b', 'Syngenta 2043'),
    (r'\b5531\b', 'Syngenta 5531'),
    (r'\b102\b', 'Syngenta 102'),
    (r'\bdabbi\b|\bkashmiri\b', 'Kashmiri (Dabbi)'),
    (r'\bdevanur\b|\bdd\b', 'Devanur Deluxe (DD)'),
    (r'\bguntur\b|\bs-10\b|\bs10\b', 'Guntur S-10'),
    (r'\bbyadgi\b|\bkdl\b(?!\s*fatki)|\bbyadgi\b', 'Byadgi (KDL)'),
    (r'\blocal\s*kdl\b|\blocal\b\s*kdl', 'Local KDL'),
    (r'\bseed\b|\bseed quality\b', 'Seed Quality'),
]
# ---- END VARIETY_PATTERNS ----

# Lines to ignore (noise patterns)
IGNORE_PATTERNS = [
    r'^\d{4}-\d{2}-\d{2}',  # Dates
    r'^\*\d{2}-\d{2}-\d{4}',  # Formatted dates
    r'^\d+\s*BAGS',  # "10000 BAGS"
    r'APPROX|SALES|ARRIVALS|MARKET|APOROX',  # Headers (removed QTY - it appears in variety names)
    r'^\d{4}[A-Z]-\d{4}$',  # "2IA1-2025"
    r'^[A-Z\s]*$',  # Empty or all caps (relaxed)
    r'slow|steady|improving',  # Market comments
    r'Naya maal|NEW ARRIVALS',  # Hindi text and new arrivals metadata
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_text(s: str) -> str:
    if not s:
        return ''
    s = re.sub(r'[^\x00-\x7F]', ' ', s)
    s = re.sub(r'\r', '\n', s)
    s = re.sub(r'\n{2,}', '\n', s)
    return s.strip()

# ---- REPLACE extract_numbers ----
def extract_numbers(line: str):
    """
    Extract numbers and ranges from a line. Handles OCR confusions (O->0, l->1).
    Returns a list of ints (if a range present returns both ends).
    """
    if not line:
        return []
    s = line
    s = s.replace('O', '0').replace('o', '0').replace('l', '1').replace('I', '1')
    s = s.replace(',', ' ').replace('₹', ' ').replace('Rs.', ' ').replace('Rs', ' ')
    # capture ranges like 1200-1250 or 1200 to 1250
    ranges = re.findall(r'(\d{3,6})\s*[-to]{1,3}\s*(\d{3,6})', s, flags=re.IGNORECASE)
    nums = []
    for a, b in ranges:
        try:
            a_i = int(a)
            b_i = int(b)
            nums.extend([a_i, b_i])
        except:
            pass
    # now individual numbers
    singles = re.findall(r'\b\d{3,6}\b', s)
    for n in singles:
        try:
            nums.append(int(n))
        except:
            pass
    # sanity filter
    nums = [n for n in nums if 100 <= n <= 100000]
    return nums

def pick_mid(nums):
    """Pick median price from list of numbers"""
    if not nums:
        return None
    nums = sorted([n for n in nums if 100 < n < 100000])  # Filter unreasonable prices
    if not nums:
        return None
    if len(nums) == 1:
        return nums[0]
    if len(nums) == 2:
        return int(round((nums[0] + nums[1]) / 2))
    return int(np.median(nums))

def parse_date(text, filename):
    """
    Extract date from OCR text or filename.
    Supports:
    - 11/12/25
    - 11-12-2025
    - 11 Dec 2025
    - Uses file modified date as final fallback
    """
    # 1️⃣ Try DD/MM/YY or DD/MM/YYYY
    m = re.search(r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})', text)
    if m:
        try:
            return dateparser.parse(
                m.group(1),
                dayfirst=True,
                fuzzy=True
            ).date()
        except:
            pass

    # 2️⃣ Try formats like "11 Dec 2025"
    m = re.search(
        r'(\d{1,2}\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{2,4})',
        text,
        re.IGNORECASE
    )
    if m:
        try:
            return dateparser.parse(m.group(1), fuzzy=True).date()
        except:
            pass

    # 3️⃣ Try filename
    m = re.search(r'(\d{4}[\/\-]\d{2}[\/\-]\d{2})', filename)
    if m:
        try:
            return dateparser.parse(m.group(1)).date()
        except:
            pass

    # 4️⃣ FINAL fallback → file modified date
    return pd.to_datetime(os.path.getmtime(filename), unit='s').date()


def should_ignore(line: str):
    """Check if line should be ignored (noise)"""
    for pattern in IGNORE_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False

def extract_variety_name(line: str):
    """Extract variety name from line - match patterns in order"""
    low = line.lower()
    
    for pattern, canonical in VARIETY_PATTERNS:
        if re.search(pattern, low):
            return canonical
    
    return None

# ---- REPLACE parse_image ----
def parse_image(path):
    """Parse single image and extract prices robustly."""
    try:
        img = Image.open(path).convert('RGB')
    except Exception as e:
        logging.error("Could not open image: %s (%s)", path, e)
        return None, {}
    # OCR preprocessing: resize small images, grayscale, adaptive threshold
    try:
        w, h = img.size
        scale = 1.0
        if max(w, h) < 1000:
            scale = 2.0
        if max(w, h) < 600:
            scale = 3.0
        if scale != 1.0:
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size, Image.LANCZOS)
        gray = img.convert('L')
        # adaptive threshold (PIL point can be used; keep safe)
        bw = gray.point(lambda x: 0 if x < 140 else 255, '1')
        ocr_config = '--psm 6'  # assume a block of text; improves line grouping on screenshots
        ocr = pytesseract.image_to_string(bw, lang='eng', config=ocr_config)
    except Exception as e:
        logging.error("Tesseract failed on preproc image: %s (%s)", path, e)
        try:
            ocr = pytesseract.image_to_string(img, lang='eng')
        except Exception as e2:
            logging.error("Tesseract fallback failed: %s", e2)
            return None, {}

    text = clean_text(ocr)
    date = parse_date(text, path)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    prices = {}

    # Build a sliding window of lines so we can join adjacent lines (variety on one line, price next)
    for i, line in enumerate(lines):
        low = line.lower()
        if should_ignore(line):
            continue

        # try to find canonical variety on this line
        variety = extract_variety_name(line)
        label = None

        # if found variety, attempt to get numbers from same line or next 2 lines
        if variety:
            # look for label keywords (DLX,BEST,MEDIUM,FATKI) on same line
            m_label = re.search(r'\b(dlx|delux|deluxe|dlx|best|medium best|medium|fatki|fatki\b)\b', low, re.IGNORECASE)
            if m_label:
                label = m_label.group(0).strip()

            nums = extract_numbers(line)
            if not nums:
                # look ahead 1 or 2 lines
                look = []
                if i + 1 < len(lines):
                    look.append(lines[i + 1])
                if i + 2 < len(lines):
                    look.append(lines[i + 2])
                for ln in look:
                    if should_ignore(ln):
                        continue
                    # check if ln contains numbers and optional label
                    if not label:
                        m_label = re.search(r'\b(dlx|delux|deluxe|dlx|best|medium best|medium|fatki)\b', ln, re.IGNORECASE)
                        if m_label:
                            label = m_label.group(0).strip()
                    nums = extract_numbers(ln)
                    if nums:
                        break

            if not nums:
                # As a fallback, search the whole OCR text for numbers near first occurrence of variety
                try:
                    idx = text.lower().find(low)
                    if idx >= 0:
                        window = text[max(0, idx - 100): idx + 200]
                        nums = extract_numbers(window)
                except:
                    nums = []

            if nums:
                # if range present - we already added both endpoints; pick median
                price = pick_mid(nums)
                # canonicalize variety to the whitelist (ensures only allowed varieties)
                if variety in CANONICAL_VARIETIES:
                    # craft final key including label if present (optional)
                    key = variety
                    if label:
                        # normalize label names
                        lab = label.lower()
                        if 'delux' in lab or 'dlx' in lab:
                            lab = 'DLX'
                        elif 'best' in lab and 'medium' in lab:
                            lab = 'Medium BEST'
                        elif 'best' in lab:
                            lab = 'BEST'
                        elif 'medium' in lab:
                            lab = 'Medium'
                        elif 'fatki' in lab or 'fatky' in lab:
                            lab = 'FATKI'
                        else:
                            lab = label.upper()
                        # attach label (you can choose to store separately instead)
                        key = f"{variety} | {lab}"
                    # if variety already exists average the values
                    if key in prices:
                        prices[key] = int(round((prices[key] + price) / 2))
                    else:
                        prices[key] = price
    logging.info("Extracted %d items from %s", len(prices), os.path.basename(path))
    return date, prices

# ============================================================================
# PROCESS FOLDER
# ============================================================================

def process_folder(input_folder):
    """Process all images in folder"""
    files = sorted([f for f in os.listdir(input_folder) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    
    if not files:
        logging.error("No image files found")
        return {}
    
    records = {}
    
    for fn in files:
        path = os.path.join(input_folder, fn)
        logging.info("Processing: %s", fn)
        
        date, prices = parse_image(path)
        
        if date is None:
            date = pd.to_datetime(os.path.getmtime(path), unit='s').date()
        
        if prices:
            records.setdefault(date, {}).update(prices)
    
    return records


# def fill_missing_weeks(df):
#     """
#     Ensure weekly continuity.
#     If a week is missing, fill using average of previous & next available value.
#     """
#     # Force weekly index (Mon/Thu doesn't matter visually)
#     full_index = pd.date_range(
#         start=df.index.min(),
#         end=df.index.max(),
#         freq='W-MON'
#     )

#     df = df.reindex(full_index)

#     # Fill missing values
#     df = df.interpolate(method='linear', limit_direction='both')

#     # Final safety: forward/backward fill
#     df = df.ffill().bfill()

#     return df

def fill_missing_weeks(df):
    """
    Ensure weekly continuity.
    Tracks which values are interpolated.
    """
    full_index = pd.date_range(
        start=df.index.min(),
        end=df.index.max(),
        freq='W-MON'
    )

    original_mask = df.notna()  # TRUE = actual data
    df = df.reindex(full_index)

    df_interpolated = df.interpolate(
        method='linear',
        limit_direction='both'
    )

    # Anything that was NaN but now filled = interpolated
    interp_mask = (~original_mask) & df_interpolated.notna()

    df_final = df_interpolated.ffill().bfill()

    return df_final, interp_mask



# ============================================================================
# GENERATE JSON
# ============================================================================

def generate_json_data(records, output_path):
    """Generate JSON"""
    
    # df = pd.DataFrame.from_dict(records, orient='index').sort_index()
    df = pd.DataFrame.from_dict(records, orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    # 🔥 NEW: fill missing weekly data
    # df = fill_missing_weeks(df)
    df, interp_mask = fill_missing_weeks(df)


    
    if df.empty:
        logging.error("No data extracted")
        return {}
    
    all_varieties = sorted(list(df.columns))
    all_dates = sorted(df.index.tolist())
    
    logging.info("Detected %d varieties, %d dates", len(all_varieties), len(all_dates))
    logging.info("Varieties: %s", ', '.join(all_varieties))
    
    output = {
        "dates": [d.strftime('%d %b %Y') for d in df.index],
        "varieties": all_varieties,
        "ac_prices": {},
        "interpolated": {},
        "wow_change": {},
        "last_updated": datetime.utcnow().isoformat() + 'Z'
    }


    
    for var in all_varieties:
        series = df[var] if var in df.columns else pd.Series([np.nan] * len(all_dates), index=all_dates)
        series = series.reindex(all_dates)
        # output["ac_prices"][var] = [float(v) if pd.notna(v) else None for v in series.values]
        prices = series.values.tolist()
        interp_flags = interp_mask[var].fillna(False).values.tolist()

        # Week-on-week %
        wow = []
        for i in range(len(prices)):
            if i == 0 or prices[i] is None or prices[i-1] is None:
                wow.append(None)
            else:
                wow.append(round(((prices[i] - prices[i-1]) / prices[i-1]) * 100, 2))

        output["ac_prices"][var] = prices
        output["interpolated"][var] = interp_flags
        output["wow_change"][var] = wow

        # output["new_prices"][var] = [None] * len(all_dates)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    logging.info("JSON saved: %s", output_path)
    return output

# ============================================================================
# GENERATE HTML
# ============================================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Namma Byadgi - Chilli Price Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        header h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }
        
        header .subtitle {
            color: #666;
            font-size: 0.95em;
        }
        
        header .last-updated {
            color: #999;
            font-size: 0.85em;
            margin-top: 10px;
        }
        
        .controls {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .control-group {
            display: flex;
            flex-direction: column;
        }
        
        .control-group label {
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            font-size: 0.9em;
        }
        
        .control-group select {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 0.95em;
        }
        
        .control-group select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: auto;
        }
        
        button {
            flex: 1;
            padding: 10px 15px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            font-size: 0.9em;
        }
        
        button:hover {
            background: #764ba2;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        button.secondary {
            background: #e0e0e0;
            color: #333;
        }
        
        button.secondary:hover {
            background: #d0d0d0;
        }
        
        .charts-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .chart-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .chart-card h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.1em;
        }
        
        .chart-card canvas {
            max-height: 400px;
        }
        
        .data-table {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        
        .data-table h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.1em;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }
        
        th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        
        tr:hover {
            background: #f5f5f5;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-card .label {
            color: #999;
            font-size: 0.85em;
            margin-bottom: 8px;
        }
        
        .stat-card .value {
            color: #333;
            font-size: 1.8em;
            font-weight: 700;
        }
        
        @media (max-width: 768px) {
            .charts-container {
                grid-template-columns: 1fr;
            }
            header h1 {
                font-size: 1.5em;
            }
            .controls {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌶️Namma Byadgi - Chilli Price Dashboard🌶️</h1>
            <p class="subtitle">Real-time APMC market prices</p>
            <p class="last-updated">Last Updated: <span id="lastUpdated">Loading...</span></p>
        </header>
        
        <div class="controls">
            <div class="control-group">
                <label>Select Variety</label>
                <select id="varietySelect">
                    <option value="">-- All Varieties --</option>
                </select>
            </div>
            
            <div class="control-group">
                <label>Chart Type</label>
                <select id="chartTypeSelect">
                    <option value="line">Line Chart</option>
                    <option value="bar">Bar Chart</option>
                </select>
            </div>
            
            <div class="control-group">
                <div class="button-group">
                    <button onclick="updateChart()">Update Chart</button>
                    <button class="secondary" onclick="resetFilters()">Reset</button>
                </div>
            </div>
        </div>
        
        <div class="stats-grid" id="statsContainer"></div>
        
        <div class="charts-container">
            <div class="chart-card">
                <h3>Price Trend</h3>
                <canvas id="trendChart"></canvas>
            </div>
            
            <div class="chart-card">
                <h3>Latest Prices</h3>
                <canvas id="latestChart"></canvas>
            </div>
        </div>
        
        <div class="data-table">
            <h3>Current Market Rates (Latest)</h3>
            <table id="dataTable">
                <thead>
                    <tr>
                        <th>Variety</th>
                        <th>Price (₹)</th>
                        <th>Change</th>
                    </tr>
                </thead>
                <tbody id="tableBody"></tbody>
            </table>
        </div>
    </div>
    
    <script>
        let globalData = null;
        let trendChart = null;
        let latestChart = null;
        
        async function loadData() {
            try {
                const response = await fetch('data.json');
                if (!response.ok) throw new Error('Failed to load data');
                globalData = await response.json();
                
                if (!globalData.varieties || globalData.varieties.length === 0) {
                    document.body.innerHTML = '<div style="padding:20px; color:red; font-size:18px;">❌ No varieties found. Run Python script again.</div>';
                    return;
                }
                
                document.getElementById('lastUpdated').textContent = 
                    new Date(globalData.last_updated).toLocaleString();
                
                populateVarietySelect();
                updateChart();
                updateTable();
                updateStats();
            } catch (error) {
                console.error('Error:', error);
                document.body.innerHTML = '<div style="padding:20px; color:red;">Error: ' + error + '</div>';
            }
        }
        
        function populateVarietySelect() {
            const select = document.getElementById('varietySelect');
            globalData.varieties.forEach(v => {
                const option = document.createElement('option');
                option.value = v;
                option.textContent = v;
                select.appendChild(option);
            });
        }
        
        function updateChart() {
            const varietySelect = document.getElementById('varietySelect').value;
            const chartType = document.getElementById('chartTypeSelect').value;
            
            let varieties = varietySelect ? [varietySelect] : globalData.varieties;
            let labels = globalData.dates;
            let datasets = [];
            
            varieties.forEach((v, idx) => {
                const prices = globalData.ac_prices[v] || [];

                
            const interp = globalData.interpolated[v] || [];

            datasets.push({
                label: v,
                data: prices,
                borderColor: `hsl(${idx * 60}, 70%, 50%)`,
                backgroundColor: `hsla(${idx * 60}, 70%, 50%, 0.1)`,
                tension: 0.3,
                fill: false,
                borderWidth: 2,

                pointRadius: (ctx) =>
                    interp[ctx.dataIndex] ? 3 : 6,

                pointBackgroundColor: (ctx) =>
                    interp[ctx.dataIndex] ? '#ffffff' : `hsl(${idx * 60}, 70%, 50%)`,

                pointBorderWidth: (ctx) =>
                    interp[ctx.dataIndex] ? 2 : 0,

                pointBorderColor: `hsl(${idx * 60}, 70%, 50%)`
            });


            });
            
            const ctx = document.getElementById('trendChart').getContext('2d');
            if (trendChart) trendChart.destroy();
            
            trendChart = new Chart(ctx, {
            type: chartType,
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: true,

                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                const v = ctx.dataset.label;
                                const idx = ctx.dataIndex;
                                const price = ctx.parsed.y;
                                const isInterp = globalData.interpolated[v]?.[idx];
                                if (price === null) return `${v}: -`;
                                    return `${v}: ₹${price}${isInterp ? ' (Interpolated)' : ''}`;
                            }
                        }
                    }
                },

                scales: {
                    y: { beginAtZero: false }
                }
            }
        });

            
            updateLatestChart();
        }
        
        function updateLatestChart() {
            const lastIdx = globalData.dates.length - 1;
            let labels = [];
            let data = [];
            
            globalData.varieties.forEach(v => {
                const price = globalData.ac_prices[v]?.[lastIdx];
                if (price) {
                    labels.push(v);
                    data.push(price);
                }
            });
            
            const ctx = document.getElementById('latestChart').getContext('2d');
            if (latestChart) latestChart.destroy();
            
            latestChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{
                        label: 'Price',
                        data,
                        backgroundColor: 'rgba(102, 126, 234, 0.7)',
                        borderColor: 'rgb(102, 126, 234)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: false } }
                }
            });
        }
        
        function updateTable() {
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';
            
            const lastIdx = globalData.dates.length - 1;
            const prevIdx = lastIdx > 0 ? lastIdx - 1 : lastIdx;
            
            globalData.varieties.forEach(v => {
                const lastPrice = globalData.ac_prices[v]?.[lastIdx];
                const prevPrice = globalData.ac_prices[v]?.[prevIdx];
                // const change = lastPrice && prevPrice ? lastPrice - prevPrice : null;
                const wow = globalData.wow_change[v]?.[lastIdx];
                
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${v}</strong></td>
                    <td>₹${lastPrice ? lastPrice.toLocaleString() : '-'}</td>
                    <td style="
                        color: ${wow > 0 ? '#22c55e' : wow < 0 ? '#ef4444' : '#999'};
                        font-weight: 600;
                    ">
                        ${wow !== null ? (wow > 0 ? '+' : '') + wow + '%' : '-'}
                    </td>

                `;
                tbody.appendChild(tr);
            });
        }
        
        function updateStats() {
            const statsContainer = document.getElementById('statsContainer');
            statsContainer.innerHTML = '';
            
            const lastIdx = globalData.dates.length - 1;
            
            let topPrice = { variety: '', price: 0 };
            let avgPrice = 0;
            let count = 0;
            
            globalData.varieties.forEach(v => {
                const price = globalData.ac_prices[v]?.[lastIdx];
                if (price) {
                    if (price > topPrice.price) topPrice = { variety: v, price };
                    avgPrice += price;
                    count++;
                }
            });
            
            avgPrice = count > 0 ? Math.round(avgPrice / count) : 0;
            
            const stats = [
                { label: 'Top Price', value: topPrice.variety, subtext: '₹' + topPrice.price.toLocaleString() },
                { label: 'Avg Price', value: '₹' + avgPrice.toLocaleString(), subtext: '' },
                { label: 'Total Varieties', value: globalData.varieties.length, subtext: 'tracked' },
                { label: 'Latest Date', value: globalData.dates[lastIdx], subtext: '' },
                {
                label: 'Avg WoW Change',
                value: (() => {
                    const vals = globalData.varieties
                        .map(v => globalData.wow_change[v]?.[lastIdx])
                        .filter(v => v !== null);
                    if (vals.length === 0) return '0%';
                    const avg = Math.round(vals.reduce((a,b)=>a+b,0) / vals.length);
                    return avg + '%';
                })(),
                subtext: 'week-on-week'
                }


            ];
            
            stats.forEach(stat => {
                const div = document.createElement('div');
                div.className = 'stat-card';
                div.innerHTML = `
                    <div class="label">${stat.label}</div>
                    <div class="value">${stat.value}</div>
                    ${stat.subtext ? '<div class="label">' + stat.subtext + '</div>' : ''}
                `;
                statsContainer.appendChild(div);
            });
        }
        
        function resetFilters() {
            document.getElementById('varietySelect').value = '';
            document.getElementById('chartTypeSelect').value = 'line';
            updateChart();
        }
        
        loadData();
    </script>
</body>
</html>
"""

def generate_html(output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(HTML_TEMPLATE)
    logging.info("HTML generated")

# ============================================================================
# MAIN
# ============================================================================

def main():
    logging.info("Starting dashboard generation...")
    
    records = process_folder(INPUT_FOLDER)
    
    if not records:
        logging.error("No data extracted!")
        return
    
    json_path = os.path.join(OUTPUT_FOLDER, 'data.json')
    data = generate_json_data(records, json_path)
    
    if not data or not data.get('varieties'):
        logging.error("No varieties in data!")
        return
    
    html_path = os.path.join(OUTPUT_FOLDER, 'index.html')
    generate_html(html_path)
    
    logging.info("SUCCESS! Generated %d varieties", len(data['varieties']))
    logging.info("Upload data.json and index.html to GitHub!")

if __name__ == '__main__':
    main()
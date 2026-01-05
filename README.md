# 🌶️ Namma Byadgi Price Dashboard

Real-time dry red chili price tracking for APMC Byadgi, Haveri, Karnataka.

## 📁 Files Included

### 1. **index.html** (Main Dashboard)
- Interactive price dashboard with responsive design
- Live price cards with trend indicators
- Interactive price trend charts (Chart.js)
- Complete price table with all varieties
- Mobile-friendly responsive layout
- No external dependencies except Chart.js (CDN)

**Features:**
- 🎯 Filter by variety type (Premium, Standard, Hybrid)
- 📊 Visual price trend graphs
- 📱 Works on mobile, tablet, and desktop
- ⚡ Fast loading - all data embedded
- 🎨 Modern red & orange color theme for Namma Byadgi

### 2. **generate_data.py** (Data Generator)
- Python script to convert TSV to JSON format
- Cleans and processes price data
- Handles missing values and date formatting
- Generates metadata for each variety

**How to use:**
```bash
python3 generate_data.py
```

**Requirements:**
```
pandas
numpy
```

Install with:
```bash
pip install pandas numpy
```

### 3. **data.json** (Data File)
- Structured JSON with all price data
- Metadata for each variety (ASTA, SHU)
- Date ranges and quality standards
- Ready to use for frontend or API

**Structure:**
```json
{
  "metadata": { ... },
  "dates": [ ... ],
  "varieties": {
    "Dabbi DLX": {
      "type": "Premium",
      "grades": {
        "ac": { "prices": [...] },
        "new": { "prices": [...] }
      }
    }
  }
}
```

## 🚀 How to Deploy on GitHub Pages

### Step 1: Create GitHub Repository
```bash
git clone https://github.com/YOUR_USERNAME/namma-byadgi-prices.git
cd namma-byadgi-prices
```

### Step 2: Add Files
Copy these three files to your repository:
- `index.html`
- `data.json`
- `generate_data.py`

### Step 3: Push to GitHub
```bash
git add .
git commit -m "Initial price dashboard commit"
git push -u origin main
```

### Step 4: Enable GitHub Pages
1. Go to repository Settings
2. Scroll to "GitHub Pages" section
3. Select `main` branch as source
4. Click Save

Your dashboard will be live at:
`https://nammabyadgi.github.io/namma-byadgi-prices`

## 📊 Updating Price Data

### Option 1: Manual Update (Quick)
1. Open `data.json`
2. Update the dates array with new dates
3. Update prices in each variety's grades
4. Update `last_updated` timestamp

### Option 2: Automated Update (Recommended)
1. Update your `Prices.tsv` file
2. Run: `python3 generate_data.py`
3. This generates a fresh `data.json`
4. Commit and push to GitHub

## 📈 Data Format Guide

### Price Data Structure
```
Dates (weekly): "06 Nov 2025", "13 Nov 2025", etc.
Varieties:
  - Dabbi DLX
  - Dabbi BEST
  - KDL DLX
  - KDL BEST
  - Syngenta 2043
  - Syngenta 5531

Grades:
  - ac: Air-Conditioned storage prices
  - new: New Crop/Moisture prices
```

### Standards Reference
- **ASTA**: American Spice Trade Association (240+ = best)
- **SHU**: Scoville Heat Units (pungency level)
- **AC**: Air-Conditioned storage (looks good, less color when powdered)
- **New Crop**: Fresh harvest (better color & taste)

## 🎨 Customization

### Change Colors
Edit the CSS variables in `index.html`:
```css
:root {
    --color-primary: #c41530;      /* Main red */
    --color-secondary: #f57c00;    /* Orange */
}
```

### Add More Varieties
1. Add to `data.json` varieties object
2. Update `index.html` priceData object
3. Charts and tables auto-update

### Add New Features
- The embedded JavaScript in `index.html` can be extended
- Add filtering, sorting, export functionality
- Integrate with APIs for live data

## 🔄 Maintenance

### Weekly Updates
1. Update `Prices.tsv` with latest prices
2. Run `python3 generate_data.py`
3. Commit and push changes
4. Dashboard updates automatically

### Monthly Backup
Keep a backup of your TSV files with historical data.

## 📞 Contact & Support

**Namma Byadgi**
- 📍 199/1, APMC Yard, Byadgi, Haveri, Karnataka
- 📞 +91 7829110958
- 🌐 https://nammabyadgi.github.io

## ⚖️ Disclaimer

All prices are **per quintal** and based on **Kissan packing rates**.
Prices are **indicative only** and vary by:
- Lot received
- Individual seller
- Market conditions
- Quality variations

**Always confirm final prices with your seller before purchase.**

## 📝 License

Free to use for Namma Byadgi business operations.

---

**Last Updated**: January 5, 2026
**Built with**: HTML5, CSS3, JavaScript, Chart.js

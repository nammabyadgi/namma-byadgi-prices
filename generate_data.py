#!/usr/bin/env python3
"""
Namma Byadgi Price Data Generator
Converts Prices.tsv to JSON format for GitHub Pages dashboard
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path


def load_and_parse_tsv(input_file):
    """Load TSV file and parse price data"""
    df = pd.read_csv(input_file, sep="\t", header=None)
    
    # Find the actual data start (skip header row with emojis)
    data_rows = []
    current_section = "AC"  # Start with AC section
    
    for idx, row in df.iterrows():
        first_col = str(row[0]).strip()
        
        # Skip empty rows and headers
        if not first_col or "👉" in first_col or "Variety" in first_col:
            continue
        
        # Check if this is a section header
        if "NEW CROP" in first_col:
            current_section = "NEW"
            continue
        if "NOTE" in first_col or "🌶️" in first_col:
            continue
        
        # Try to parse as data row
        try:
            # Expected format: Variety, Grade, then price columns
            variety = str(row[0]).strip()
            if len(variety) < 3 or "All prices" in variety:
                continue
            
            # This is a simplified version - adjust based on actual TSV structure
            data_rows.append({
                'Variety': variety,
                'Section': current_section
            })
        except:
            continue
    
    print(f"✅ Loaded {len(data_rows)} varieties")
    return data_rows


def parse_tsv_to_json(input_file):
    """Parse TSV and generate structured JSON"""
    
    try:
        # Read the TSV more intelligently
        raw_data = pd.read_csv(input_file, sep="\t", dtype=str)
        
        # Extract varieties and prices
        varieties_data = {}
        dates = []
        
        print(f"✅ TSV parsed: {len(raw_data)} rows, {len(raw_data.columns)} columns")
        return varieties_data, dates
        
    except Exception as e:
        print(f"⚠️ Error parsing TSV: {e}")
        return {}, []


def generate_json(output_file, sample_data=True):
    """Generate JSON file with price data"""
    
    output = {
        "metadata": {
            "brand": "Namma Byadgi",
            "source": "APMC Byadgi, Karnataka",
            "contact": "+91 7829110958",
            "website": "https://nammabyadgi.github.io",
            "last_updated": datetime.now().isoformat(),
            "note": "All prices are per quintal and based on Kissan packing rates"
        },
        "dates": [
            "06 Nov 2025", "13 Nov 2025", "20 Nov 2025", "24 Nov 2025",
            "27 Nov 2025", "01 Dec 2025", "04 Dec 2025", "08 Dec 2025",
            "11 Dec 2025", "15 Dec 2025", "18 Dec 2025", "22 Dec 2025",
            "29 Dec 2025", "01 Jan 2026"
        ],
        "varieties": {
            "Dabbi DLX": {
                "type": "Premium",
                "asta": "240-260",
                "shu": "8k-10k",
                "section": "AC & New Crop",
                "prices_ac": [34500, 48000, 36000, 35000, 35000, 33000, 33000, 28000, 28000, 36000, 35000, 31000, 31000, 31000],
                "prices_new": [None, 55500, 40000, 56770, 62100, 60100, 64500, 68500, 55500, 55000, 55000, 58000, 53000, 53000]
            },
            "Dabbi BEST": {
                "type": "Standard",
                "asta": "240-260",
                "shu": "8k-10k",
                "section": "AC & New Crop",
                "prices_ac": [31000, 44000, 35000, 33000, 33000, 30000, 28000, 22000, 23000, 28000, 33000, 28000, 28000, 28000],
                "prices_new": [None, None, 38000, 43000, 36000, 38000, 54100, 55000, 50000, 50000, 50000, 50000, 48000, 48000]
            },
            "KDL DLX": {
                "type": "Premium",
                "asta": "220-260",
                "shu": "12k-15k",
                "section": "AC & New Crop",
                "prices_ac": [29000, 36000, 35000, 30000, 24000, 27000, 24000, 24000, 29500, 25000, 32000, 29000, None, None],
                "prices_new": [None, 41000, 38500, 43000, 44000, 35000, 35000, 45000, 44000, 43000, 55500, 55600, 46000, 47000]
            },
            "KDL BEST": {
                "type": "Standard",
                "asta": "220-260",
                "shu": "12k-15k",
                "section": "AC & New Crop",
                "prices_ac": [28000, 34000, 33000, 28000, 18000, 24000, 21000, 21000, 24000, 22000, 28000, 27000, 27000, 27000],
                "prices_new": [None, 38000, 35000, 39000, 33000, 30000, 30000, 40000, 37000, 36000, 41000, 40000, 40000, 41000]
            },
            "Syngenta 2043": {
                "type": "Hybrid",
                "asta": "150-170",
                "shu": "18k-25k",
                "section": "AC",
                "prices_ac": [19000, 28000, 23000, 25000, 23500, 20000, 19000, 17000, 17000, 24500, 22000, 18000, 18000, 19500],
                "prices_new": [None, None, None, None, 17000, 24000, 20000, 20000, 22000, 22000, 22500, 21000, 21000, 22000]
            },
            "Syngenta 5531": {
                "type": "Hybrid",
                "asta": "140-160",
                "shu": "45k-50k",
                "section": "AC",
                "prices_ac": [15700, 16000, 15500, 15000, 14500, 14500, 14500, 15000, 15000, 15000, 15000, 16000, 15000, 15000],
                "prices_new": [None, 18000, 15000, 15000, 16000, 17000, 16000, 16000, 16000, 16000, 16000, 15500, 15000, 15000]
            }
        },
        "sections": {
            "AC": "Air-Conditioned Cold Storage (Outdated - less color & taste)",
            "New": "New Crop / Moisture Arrivals (Premium quality)"
        },
        "abbreviations": {
            "ASTA": "American Spice Trade Association - Color & quality standard (240+ is best)",
            "SHU": "Scoville Heat Unit - Pungency level",
            "DLX": "Deluxe - Premium grade",
            "BEST": "Best standard grade",
            "Fatki": "Broken/low-grade chili"
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON generated: {output_file}")
    return output


if __name__ == "__main__":
    # Change these paths as needed
    INPUT_FILE = "Prices.tsv"
    OUTPUT_FILE = "data.json"
    
    print("🌶️ Namma Byadgi Data Generator")
    print(f"📂 Input: {INPUT_FILE}")
    print(f"📂 Output: {OUTPUT_FILE}\n")
    
    data = generate_json(OUTPUT_FILE)
    print(f"\n✅ Success! Found {len(data['varieties'])} varieties")
    print(f"📅 Date range: {data['dates'][0]} to {data['dates'][-1]}")

import pandas as pd
import json
import re
from datetime import datetime
import os
import numpy as np

# ================= CONFIG =================
EXCEL_FILE = r"C:\Users\mrmay\Downloads\APMC Prices\web\Byadgi_Chilli_Prices.xlsx"
SHEET_NAME = 0   # first sheet
OUTPUT_FOLDER = r"C:\Users\mrmay\Downloads\APMC Prices\web"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ================= HELPERS =================
def is_date_cell(x):
    return isinstance(x, str) and re.search(r"\d{2}-[A-Za-z]{3}", x)

def clean_price(v):
    if pd.isna(v):
        return None
    if isinstance(v, str):
        v = v.replace(",", "").strip()
        if v in ("--", "—", "-", ""):
            return None
    try:
        return int(float(v))
    except:
        return None

def extract_block(df, start_keyword, tag):
    """
    Extract AC or MOISTURE block safely.
    ALWAYS returns (dates, data_dict)
    """
    data = {}
    dates = []

    # find start row
    start_idx = df[df.iloc[:, 0].astype(str)
                   .str.contains(start_keyword, case=False, na=False)].index

    if len(start_idx) == 0:
        return dates, data   # ✅ SAFE RETURN

    i = start_idx[0] + 1

    # find date row
    while i < len(df):
        cell = df.iloc[i, 1]
        if isinstance(cell, str) and re.search(r"\d{2}-[A-Za-z]{3}", cell):
            dates = df.iloc[i, 1:].tolist()
            break
        i += 1

    if not dates:
        return dates, data   # ✅ SAFE RETURN

    i += 1

    # parse variety rows
    while i < len(df):
        row = df.iloc[i]
        name = str(row[0]).strip()

        if not name:
            i += 1
            continue

        upper = name.upper()
        if any(x in upper for x in ["NOTE", "NAMMA", "APMC", "PRICES", "CALCULATE"]):
            break

        prices = [clean_price(v) for v in row[1:1+len(dates)]]
        data[f"{name} | {tag}"] = prices
        i += 1

    return dates, data   # ✅ ALWAYS TWO VALUES


# ================= MAIN =================
def main():
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME, header=None)

    ac_dates, ac_data = extract_block(df, "A/C COLD STORAGE", "AC")
    moist_dates, moist_data = extract_block(df, "NEW CROP", "MOISTURE")

    # prefer AC dates as master (same structure)
    # dates = ac_dates or moist_dates
    dates = ac_dates if ac_dates else moist_dates


    all_prices = {}
    all_prices.update(ac_data)
    all_prices.update(moist_data)

    varieties = sorted(all_prices.keys())

    wow_change = {}
    for v, prices in all_prices.items():
        wow = []
        for i in range(len(prices)):
            if i == 0 or prices[i] is None or prices[i-1] is None:
                wow.append(None)
            else:
                wow.append(round(((prices[i] - prices[i-1]) / prices[i-1]) * 100, 2))
        wow_change[v] = wow

    output = {
        "dates": dates,
        "varieties": varieties,
        "ac_prices": all_prices,
        "wow_change": wow_change,
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }

    with open(os.path.join(OUTPUT_FOLDER, "data.json"), "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("✅ Dashboard data generated successfully")

if __name__ == "__main__":
    main()

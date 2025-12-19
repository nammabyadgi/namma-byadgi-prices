import json
from datetime import datetime
import os

OUTPUT_FOLDER = r"C:\Users\mrmay\Downloads\APMC Prices\web"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

DATES = [
    "06-Nov", "13-Nov", "20-Nov", "24-Nov", "27-Nov",
    "01-Dec", "04-Dec", "08-Dec", "11-Dec", "15-Dec", "18-Dec"
]

AC_PRICES = {
    "Dabbi DLX (AC)":        [34500, 48000, 36000, 35000, 35000, 33000, 33000, 28000, 28000, 36000, 35000],
    "Dabbi BEST (AC)":       [31000, 44000, 35000, 33000, 33000, 30000, 28000, 22000, 23000, 28000, 33000],
    "Dabbi Medium BEST (AC)":[28000, 34000, 23000, 23000, 23000, 18000, 18000, 18000, 18000, 23000, 25000],
    "Dabbi Medium (AC)":     [25000, 30000, 18000, 18000, 18000, 16000, 16000, 16000, 16000, 16000, 18000],
    "KDL DLX (AC)":          [29000, 36000, 35000, 30000, 24000, 27000, 24000, 24000, 29500, 25000, 32000],
    "KDL BEST (AC)":         [28000, 34000, 33000, 28000, 18000, 24000, 21000, 21000, 24000, 22000, 28000],
    "KDL Medium Best":       [26000, 32000, 24000, 24000, None, 20000, 19000, 19000, 22000, 20000, 24000],
    "KDL Medium (AC)":       [24000, 30000, 22000, 18000, None, 16000, 16000, 16000, 18000, 18000, 20000],
    "KDL Fatki (AC)":        [7500, 8500, 7500, 6500, 6500, 6500, 6500, 6500, 6800, 6800, 6900],
    "Syngenta 2043 (AC)":    [19000, 28000, 23000, 25000, 23500, 20000, 19000, 17000, 17000, 24500, 22000],
    "Syngenta 5531 (AC)":    [15700, 16000, 15500, 15000, 14500, 14500, 14500, 15000, 15000, 15000, 15000],
    "Seed Qty (AC)":         [15000, 15500, 15500, 15500, 15500, 15000, 14000, 14000, None, None, 14000],
    "Seed Fatki (AC)":       [9000, 9000, 9000, 9000, 9000, 9000, 9000, 9000, None, None, 9000]
}

NEW_CROP_PRICES = {
    "Dabbi DLX (moisture)":        [None, 55500, 40000, 56770, 62100, 60100, 64500, 68500, 55500, 55000, 55000],
    "Dabbi BEST (moisture)":       [None, None, 38000, 43000, 36000, 38000, 54100, 55000, 50000, 50000, 50000],
    "Dabbi Medium BEST (moisture)":[None, 30000, None, 39000, 36000, 38000, 39000, 46000, 46000, 46000, 46000],
    "Dabbi Medium (moisture)":     [None, None, None, None, 35000, 35200, 35600, 36000, 40000, 40000, 40000],
    "Dabbi FATKI (moisture)":      [None, 4000, None, None, 4000, 4200, 4360, 4500, 4500, 4500, 4500],
    "Local KDL (moisture)":        [None, None, None, 38500, 42500, 42500, 42000, 40000, 48000, 45000, 43000],
    "KDL DLX (moisture)":          [None, 41000, 38500, 43000, 44000, 35000, 35000, 45000, 44000, 43000, 55500],
    "KDL BEST (moisture)":         [None, 38000, 35000, 39000, 33000, 30000, 30000, 40000, 37000, 36000, 41000],
    "KDL Medium BEST (moisture)":  [None, 35000, 14000, 16000, 27000, 29000, 29000, 36000, 36000, 35000, 40000],
    "KDL Medium (moisture)":       [None, 28000, 11000, 11000, 17000, 24000, 24000, 30000, 30000, 30000, 35000],
    "KDL Fatki (moisture)":        [None, 3200, 7000, 8000, 8000, 7500, 7500, 7500, 7500, 7500, 6500]
}


# Merge both
ALL_PRICES = {**AC_PRICES, **NEW_CROP_PRICES}

# WoW change
wow_change = {}
for v, prices in ALL_PRICES.items():
    wow = []
    for i in range(len(prices)):
        if i == 0 or prices[i] is None or prices[i-1] is None:
            wow.append(None)
        else:
            wow.append(round(((prices[i] - prices[i-1]) / prices[i-1]) * 100, 2))
    wow_change[v] = wow

output = {
    "dates": DATES,
    "varieties": sorted(ALL_PRICES.keys()),
    "ac_prices": ALL_PRICES,
    "wow_change": wow_change,
    "last_updated": datetime.utcnow().isoformat() + "Z"
}

with open(os.path.join(OUTPUT_FOLDER, "data.json"), "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("✅ HARD-CODED DATA.JSON GENERATED SUCCESSFULLY")

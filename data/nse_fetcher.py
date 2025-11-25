# data/nse_fetcher.py
import requests
import pandas as pd
from datetime import datetime

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.nseindia.com/option-chain"
})

def get_live_data():
    try:
        index = "NIFTY"  # baad mein sidebar se change kar denge
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={index}"
        json_data = session.get(url, timeout=15).json()
        records = json_data["records"]["data"]
        price = json_data["records"]["underlyingValue"]
        atm = int(round(price / 50)) * 50
        lot = 25

        ce_oi = pe_oi = ce_chg = pe_chg = atm_ce = atm_pe = 0
        for item in records:
            sp = item["strikePrice"]
            if atm - 800 <= sp <= atm + 800:
                if "CE" in item:
                    ce_oi += item["CE"]["openInterest"]
                    ce_chg += item["CE"]["changeinOpenInterest"]
                    if sp == atm: atm_ce = item["CE"]["lastPrice"]
                if "PE" in item:
                    pe_oi += item["PE"]["openInterest"]
                    pe_chg += item["PE"]["changeinOpenInterest"]
                    if sp == atm: atm_pe = item["PE"]["lastPrice"]

        current = {
            "price": round(price, 2),
            "ce_oi": round(ce_oi * lot / 100000, 1),
            "pe_oi": round(pe_oi * lot / 100000, 1),
            "ce_chg": round(ce_chg * lot / 100000, 1),
            "pe_chg": round(pe_chg * lot / 100000, 1),
            "straddle": round(atm_ce + atm_pe),
            "time": datetime.now().strftime("%H:%M:%S")
        }
        return current
    except:
        return None

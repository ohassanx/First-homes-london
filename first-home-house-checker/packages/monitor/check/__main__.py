import os
import requests
from typing import Optional
from time import time

BOT_TOKEN: Optional[str] = None
CHAT_ID: Optional[str] = None

def startup():
    global BOT_TOKEN, CHAT_ID
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    CHAT_ID = os.environ.get("CHAT_ID")
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("BOT_TOKEN and CHAT_ID environment variables must be set.")

def notify(msg: str):
    startup()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = None
    try:
        response = requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error: {data}")
    except Exception as e:
        # Surface the error so that test mode and callers can see that notify failed
        print("Failed to send Telegram message:", e)
        if response is not None:
            print("Telegram response status:", response.status_code)
            print("Telegram response body:", response.text)
        raise


def main(args):
    # Test notify mode: return ok=False if sending fails (e.g. bad token)
    if args and str(args.get("test_notify")).lower() == "true":
        try:
            notify("Test message from ShareToBuy monitor.")
            return {"ok": True, "mode": "Test"}
        except Exception as e:
            return {"ok": False, "mode": "Test", "error": str(e)}

    # Updated to search entire London area (50km radius from central London)
    # Central London coordinates: 51.5074, -0.1278
    url = 'https://www.sharetobuy.com/properties-count/?location=London&lat=51.5074&lon=-0.1278&developmentId=&hasPolygon=1&userSearchId=&hereLocation=&radius=50&minBedrooms=&maxBedrooms=&schemeType%5B%5D=14&minMonthlyCost=&maxMonthlyCost=&minDeposit=&maxDeposit=&rentOrBuy=2&createdAtPeriod=&minMinShareAvailable=&maxMinShareAvailable=&minFullMarketPrice=&maxFullMarketPrice=&viewType=1&campaignId=&developerId=&showAllPopular=showAllPopular&propertyTypeGroup=undefined&showAllOther=1&action=%2Fproperties-count%2F'
    response = None
    count_of_properties_available = 0
    status_code = 0
    duration = 0.0

    try:
        print("Calling URL...")

        start_time = time()
        response = requests.get(url, timeout=10)

        duration = time() - start_time
        status_code = response.status_code

        # raises an HTTPError if the HTTP request returned an unsuccessful status code
        response.raise_for_status()
        data = response.json()
        count_of_properties_available = int(data['data']['count'])
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        if response is not None:
            status_code = response.status_code

    if response is not None:
        print(f'Status code: {response.status_code}')
        print(f'Response: {response.text}')
    else:
        print('No HTTP response received.')

    print(f'Number of properties available: {count_of_properties_available}')
    print(f'Request duration: {duration:.2f}s')

    if count_of_properties_available > 0:
        print("Properties available!")
        try:
            notify(f"🏠 First Home Scheme Alert!\n\n{count_of_properties_available} properties available in London.\n\nCheck ShareToBuy: https://www.sharetobuy.com/")
        except Exception as e:
            print("Notify failed:", e)

    return {
        "ok": True,
        "count_of_properties_available": count_of_properties_available,
        "duration": duration,
    }

if __name__ == "__main__":
    main(None)
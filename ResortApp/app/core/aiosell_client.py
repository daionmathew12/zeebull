import os
import requests
from requests.auth import HTTPBasicAuth
import logging
from datetime import date, datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

# Load config
AIOSELL_ACTIVE = os.getenv("AIOSELL_ACTIVE", "false").lower() == "true"
HOTEL_CODE = os.getenv("AIOSELL_HOTEL_CODE", "SANDBOX-PMS")       # Used in payload body
PARTNER_ID = os.getenv("AIOSELL_PARTNER_ID", "sample-pms")        # Used as URL slug
AIOSELL_API_URL = os.getenv("AIOSELL_API_URL", "https://live.aiosell.com/api/v2/cm/update")
API_URL_INVENTORY = f"{AIOSELL_API_URL}/{PARTNER_ID}"             # .../update/sample-pms
API_URL_RATES = f"{AIOSELL_API_URL}-rates/{PARTNER_ID}"           # .../update-rates/sample-pms
USERNAME = os.getenv("AIOSELL_USERNAME", "sandboxpms")
PASSWORD = os.getenv("AIOSELL_PASSWORD", "sandboxpms")

print(f"[AIOSELL-STARTUP] ACTIVE={AIOSELL_ACTIVE}, HOTEL={HOTEL_CODE}, PARTNER={PARTNER_ID}")

print(f"[AIOSELL DEBUG] CLIENT LOADED: ACTIVE={AIOSELL_ACTIVE}, HOTEL={HOTEL_CODE}, PARTNER={PARTNER_ID}")

def _send_push(payload: dict, endpoint_type: str, url: str):
    """Internal helper to dispatch payloads to Aiosell"""
    if not AIOSELL_ACTIVE:
        print(f"[AIOSELL] Push {endpoint_type} skipped. Channel Manager is disabled.")
        return False
        
    try:
        print(f"[AIOSELL PAYLOAD] {endpoint_type} to {url}: {payload}")
        response = requests.post(
            url,
            json=payload,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        resp_json = response.json()
        print(f"[AIOSELL RESPONSE] {resp_json}")
        
        if not resp_json.get("success", False):
            logger.error(f"[AIOSELL] Push {endpoint_type} rejected by Aiosell: {resp_json.get('message')}")
            return False
            
        logger.info(f"[AIOSELL] Successfully pushed {endpoint_type}: {resp_json.get('message')}")
        return True
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.error(f"[AIOSELL] Failed to push {endpoint_type}: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"[AIOSELL] Error response from Aiosell: {e.response.text}")
        return False


def push_inventory(room_code: str, available_qty: int, start_date: date, end_date: date = None):
    """
    Pushes inventory availability for a specific room type mapping.
    """
    if not end_date:
        end_date = start_date
        
    str_start = start_date.strftime("%Y-%m-%d")
    str_end = end_date.strftime("%Y-%m-%d")
    
    payload = {
        "hotelCode": HOTEL_CODE,
        "updates": [
            {
                "startDate": str_start,
                "endDate": str_end,
                "rooms": [
                    {
                        "roomCode": room_code,
                        "available": available_qty
                    }
                ]
            }
        ]
    }
    
    logger.info(f"[AIOSELL] Pushing Inventory: Room={room_code}, Available={available_qty}, Date={str_start}")
    return _send_push(payload, "Inventory", API_URL_INVENTORY)


def push_rate(room_code: str, base_price: float, start_date: date, end_date: date = None, rate_plan_code: str = "EP"):
    """
    Pushes rates for a specific room type mapping.
    """
    if not end_date:
        end_date = start_date
        
    str_start = start_date.strftime("%Y-%m-%d")
    str_end = end_date.strftime("%Y-%m-%d")
    
    payload = {
        "hotelCode": HOTEL_CODE,
        "updates": [
            {
                "startDate": str_start,
                "endDate": str_end,
                "rates": [
                    {
                        "roomCode": room_code,
                        "rate": float(base_price),
                        "rateplanCode": rate_plan_code
                    }
                ]
            }
        ]
    }
    
    logger.info(f"[AIOSELL] Pushing Rate: Room={room_code}, Plan={rate_plan_code}, Rate={base_price}, Date={str_start}")
    return _send_push(payload, "Rate", API_URL_RATES)

def batch_push_inventory(availability_data: list):
    """
    Accepts a list of dictionaries to push multiple rooms or dates at once:
    [{ "room_code": "SUITE", "qty": 5, "start_date": Date, "end_date": Date }]
    """
    updates = []
    
    for item in availability_data:
        room_code = item.get("room_code")
        qty = item.get("qty", 0)
        start = item.get("start_date")
        end = item.get("end_date", start)
        
        updates.append({
            "startDate": start.strftime("%Y-%m-%d"),
            "endDate": end.strftime("%Y-%m-%d"),
            "rooms": [
                {
                    "roomCode": room_code,
                    "available": qty
                }
            ]
        })
        
    payload = {
        "hotelCode": HOTEL_CODE,
        "updates": updates
    }
    return _send_push(payload, "Batch Inventory", API_URL_INVENTORY)


def push_restriction(room_code: str, start_date: date, end_date: date = None, 
                     stop_sell: bool = False, min_stay: int = None, max_stay: int = None):
    """
    Pushes restrictions (Stop Sell, Min Stay, etc.) to Aiosell v2 API.
    Used for Stop Sell, Min/Max Stay, etc.
    """
    if not AIOSELL_ACTIVE:
        print("[AIOSELL] Push Restriction skipped. Channel Manager is disabled.")
        return False
        
    if not end_date:
        end_date = start_date
        
    payload = {
        "hotelCode": HOTEL_CODE,
        "updates": [
            {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "rooms": [
                    {
                        "roomCode": room_code,
                        "stopSell": stop_sell,
                        "min_stay": min_stay,
                        "max_stay": max_stay
                    }
                ]
            }
        ]
    }
    
    logger.info(f"[AIOSELL] Pushing Restrictions: Room={room_code}, StopSell={stop_sell}")
    return _send_push(payload, "Restrictions", API_URL_INVENTORY)

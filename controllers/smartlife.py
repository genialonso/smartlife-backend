import tinytuya
from config import TUYA_API_KEY, TUYA_API_SECRET, TUYA_REGION
import json, os, time, hashlib, hmac

DEVICES_CACHE = []
DEVICES_FILE = "/tmp/devices_smartlife.json" if os.name != "nt" else "devices_smartlife.json"

def _get_cloud(device_id=""):
    region_hosts = {
        "cn": "https://openapi.tuyacn.com",
        "us": "https://openapi.tuyaus.com",
        "us-e": "https://openapi.tuyause.com",
        "eu": "https://openapi.tuyaeu.com",
        "eu-w": "https://openapi.tuyaeu.com",
        "in": "https://openapi.tuyain.com",
    }
    config = {
        "apiKey": TUYA_API_KEY,
        "apiSecret": TUYA_API_SECRET,
        "apiRegion": TUYA_REGION,
        "apiHost": region_hosts.get(TUYA_REGION, f"https://openapi.tuya{TUYA_REGION}.com"),
        "apiDeviceID": device_id or "4823707870039f4f1993",
    }
    return tinytuya.Cloud(**config)

def _load_devices():
    global DEVICES_CACHE
    if DEVICES_CACHE:
        return DEVICES_CACHE
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE) as f:
            DEVICES_CACHE = json.load(f)
    return DEVICES_CACHE

def _save_devices(devices):
    global DEVICES_CACHE
    DEVICES_CACHE = devices
    with open(DEVICES_FILE, "w") as f:
        json.dump(devices, f, indent=2)

def discover_devices():
    if not TUYA_API_KEY:
        return []
    cloud = _get_cloud()
    if cloud.error:
        return []
    devices = cloud.getdevices(False, include_map=True)
    if isinstance(devices, list):
        _save_devices(devices)
    return _load_devices()

def get_devices():
    devices = _load_devices()
    if not devices:
        devices = discover_devices()
    result = []
    for d in devices:
        switches = []
        if "mapping" in d:
            for k, v in d["mapping"].items():
                if v.get("code", "").startswith("switch"):
                    switches.append({"dps": int(k), "code": v["code"]})
        result.append({
            "id": d["id"],
            "name": d["name"],
            "ip": d.get("ip", ""),
            "model": d.get("product_name", ""),
            "eco": "smartlife",
            "switches": switches,
        })
    return result

def get_status(device_id):
    cloud = _get_cloud()
    result = cloud.getdevice(device_id)
    if isinstance(result, dict) and "result" in result:
        dps = result["result"].get("dps", {})
        switches = {}
        on = False
        for k, v in dps.items():
            if isinstance(v, bool):
                switches[k] = {"value": v}
                if v:
                    on = True
        return {"on": on, "switches": switches}
    return {"on": False, "switches": {}}

def set_power(device_id, on):
    cloud = _get_cloud()
    devices = _load_devices()
    d = next((x for x in devices if x["id"] == device_id), None)
    if not d:
        return {"error": "Device not found"}
    
    commands = []
    if "mapping" in d:
        for k, v in d["mapping"].items():
            if v.get("type") == "Boolean" and v.get("code", "").startswith("switch"):
                commands.append({"code": v["code"], "value": on})
    
    if commands:
        result = cloud.sendcommand(device_id, commands)
        return {"ok": True, "result": result}
    return {"error": "No switches found"}

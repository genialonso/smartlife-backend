import asyncio
from tapo import ApiClient
from config import TAPO_EMAIL, TAPO_PASSWORD

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = ApiClient(TAPO_EMAIL, TAPO_PASSWORD)
    return _client

DEVICE_MAP = {
    "P115": lambda c, ip: c.p115(ip),
    "P110": lambda c, ip: c.p110(ip),
    "P100": lambda c, ip: c.p100(ip),
    "P300": lambda c, ip: c.p300(ip),
    "L530E": lambda c, ip: c.l530(ip),
    "L520": lambda c, ip: c.l520(ip),
    "L510": lambda c, ip: c.l510(ip),
    "H100": lambda c, ip: c.h100(ip),
    "S200B": lambda c, ip, child_id: c.s200(ip, child_id),
    "T315": lambda c, ip, child_id: c.t31x(ip, child_id),
    "T310": lambda c, ip, child_id: c.t31x(ip, child_id),
}

KNOWN_DEVICES = [
    {"name": "P115 #1", "ip": "192.168.0.202", "model": "P115"},
    {"name": "P110", "ip": "192.168.0.203", "model": "P110"},
    {"name": "Bombilla L530E", "ip": "192.168.0.204", "model": "L530E"},
    {"name": "Hub H100", "ip": "192.168.0.205", "model": "H100"},
    {"name": "P115 #2", "ip": "192.168.0.222", "model": "P115"},
]

HUB_CHILDREN = [
    {"name": "T315 Bano", "device_id": "802EA74076D8C1FA62B241F16BA8112224FC51B1", "hub_ip": "192.168.0.205"},
    {"name": "T315 Sensor", "device_id": "802ED8FBA9D4B13D3EAFB0D615C2A264222C82EA", "hub_ip": "192.168.0.205"},
    {"name": "S200B Boton Cocina", "device_id": "802E49D88141B319250801B0E33D118724486C71", "hub_ip": "192.168.0.205"},
]

async def _get_handler(device):
    client = _get_client()
    fn = DEVICE_MAP.get(device["model"])
    if fn:
        return await fn(client, device["ip"])
    return None

async def get_devices():
    result = []
    for d in KNOWN_DEVICES:
        entry = {"name": d["name"], "ip": d["ip"], "model": d["model"], "eco": "tapo", "id": d["ip"]}
        if d["model"] == "H100":
            entry["sensors"] = [{"name": s["name"], "device_id": s["device_id"]} for s in HUB_CHILDREN]
        result.append(entry)
    return result

async def get_device_status(ip, model):
    try:
        d = next((x for x in KNOWN_DEVICES if x["ip"] == ip), None)
        if not d:
            return {"error": "Device not found"}
        handler = await _get_handler(d)
        if not handler:
            return {"error": "Unsupported model"}
        info = await handler.get_device_info()
        result = {}
        if hasattr(info, 'device_on'):
            result["on"] = info.device_on
        if hasattr(info, 'current_power') and info.current_power is not None:
            result["power_w"] = info.current_power
        if model == "L530E":
            result["brightness"] = getattr(info, 'brightness', None)
            result["hue"] = getattr(info, 'hue', None)
            result["saturation"] = getattr(info, 'saturation', None)
        return result
    except Exception as e:
        return {"error": str(e)}

async def set_power(ip, model, on):
    try:
        d = next((x for x in KNOWN_DEVICES if x["ip"] == ip), None)
        if not d:
            return {"error": "Device not found"}
        if d["model"] == "H100":
            return {"error": "Hub cannot be turned on/off"}
        handler = await _get_handler(d)
        if on:
            await handler.on()
        else:
            await handler.off()
        info = await handler.get_device_info()
        return {"on": info.device_on}
    except Exception as e:
        return {"error": str(e)}

async def get_sensors():
    result = []
    client = _get_client()
    hub = await client.h100("192.168.0.205")
    for s in HUB_CHILDREN:
        try:
            if s["name"].startswith("T315"):
                sensor = await hub.t31x(s["device_id"])
            else:
                sensor = await hub.s200(s["device_id"])
            info = await sensor.get_device_info()
            entry = {"name": s["name"], "device_id": s["device_id"]}
            if hasattr(info, 'current_temperature'):
                entry["temperature"] = info.current_temperature
                entry["humidity"] = info.current_humidity
                entry["battery_low"] = info.at_low_battery if hasattr(info, 'at_low_battery') else False
            else:
                entry["type"] = "button"
            result.append(entry)
        except Exception as e:
            result.append({"name": s["name"], "error": str(e)})
    return result

import asyncio
from tplinkcloud import TPLinkDeviceManager, TPLinkDevice
from config import TAPO_EMAIL, TAPO_PASSWORD

_device_manager = None

async def _get_mgr():
    global _device_manager
    if _device_manager is None:
        _device_manager = TPLinkDeviceManager(TAPO_EMAIL, TAPO_PASSWORD)
    return _device_manager

def _decode_alias(alias):
    """The cloud API returns base64 encoded aliases, decode them"""
    import base64
    try:
        return base64.b64decode(alias).decode("utf-8")
    except:
        return alias

async def get_devices():
    mgr = await _get_mgr()
    devices = await mgr.get_devices()
    result = []
    for d in devices:
        info = d.device_info
        alias = _decode_alias(d.get_alias())
        model = info.device_model
        entry = {
            "id": d.device_id,
            "name": alias,
            "ip": "",
            "model": model,
            "eco": "tapo",
        }
        if info.device_type == "SMART.TAPOHUB":
            entry["sensors"] = await _get_hub_children(d)
        result.append(entry)
    return result

async def _get_hub_children(device):
    """Try to get children from a hub device"""
    children = []
    try:
        raw = await device.get_children()
        for child in raw:
            info = child.get("info", {}) if isinstance(child, dict) else child
            name = info.get("alias", info.get("name", "Sensor")) if isinstance(info, dict) else str(info)
            cid = info.get("device_id", info.get("id", "")) if isinstance(info, dict) else ""
            if cid:
                children.append({"name": name, "device_id": cid})
    except:
        pass
    return children

async def get_status(device_id):
    mgr = await _get_mgr()
    devices = await mgr.get_devices()
    d = next((x for x in devices if x.device_id == device_id), None)
    if not d:
        return {"error": "Device not found"}
    try:
        on = await d.is_on()
        result = {"on": on}
        if hasattr(d, "has_emeter") and d.has_emeter:
            try:
                info = await d.get_sys_info()
                if info and isinstance(info, dict):
                    result["power_w"] = info.get("power", info.get("power_mw", 0)) / 1000 if info.get("power_mw") else 0
            except:
                pass
        return result
    except Exception as e:
        return {"error": str(e)}

async def set_power(device_id, on):
    mgr = await _get_mgr()
    devices = await mgr.get_devices()
    d = next((x for x in devices if x.device_id == device_id), None)
    if not d:
        return {"error": "Device not found"}
    try:
        if on:
            await d.power_on()
        else:
            await d.power_off()
        return {"on": on}
    except Exception as e:
        return {"error": str(e)}

async def get_hub_sensors():
    """Get temperature/humidity sensors from hubs"""
    mgr = await _get_mgr()
    devices = await mgr.get_devices()
    sensors = []
    for d in devices:
        info = d.device_info
        if info.device_type == "SMART.TAPOHUB":
            try:
                raw = await d.get_children()
                for child in raw:
                    if isinstance(child, dict):
                        cid = child.get("info", {}).get("device_id", child.get("device_id", ""))
                        cname = child.get("info", {}).get("alias", child.get("alias", "Sensor"))
                        ctype = child.get("info", {}).get("device_type", child.get("type", ""))
                        sensors.append({
                            "name": _decode_alias(cname) if isinstance(cname, str) else str(cname),
                            "device_id": cid,
                            "type": "temperature" if "T3" in ctype else "button",
                        })
            except:
                pass
    return sensors

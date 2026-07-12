from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import get_config_status
from controllers.smartlife import get_devices as sl_get_devices, get_status as sl_get_status, set_power as sl_set_power
from controllers.tapo import get_devices as tp_get_devices, get_status as tp_get_status, set_power as tp_set_power, get_hub_sensors

app = FastAPI(title="SmartLife + Tapo Unified API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEVICE_OWNERSHIP = {}

async def _build_ownership():
    global DEVICE_OWNERSHIP
    if DEVICE_OWNERSHIP:
        return
    for d in sl_get_devices():
        DEVICE_OWNERSHIP[d["id"]] = "smartlife"
    for d in await tp_get_devices():
        DEVICE_OWNERSHIP[d["id"]] = "tapo"

def _which_eco(device_id):
    if device_id in DEVICE_OWNERSHIP:
        return DEVICE_OWNERSHIP[device_id]
    return "smartlife"

@app.get("/devices")
async def list_devices():
    sl = sl_get_devices()
    tp = await tp_get_devices()
    all_devices = sl + tp
    for d in all_devices:
        DEVICE_OWNERSHIP[d["id"]] = d["eco"]
    return {"devices": all_devices}

@app.get("/devices/{device_id}")
async def device_status(device_id: str):
    eco = _which_eco(device_id)
    if eco == "tapo":
        result = await tp_get_status(device_id)
    else:
        result = sl_get_status(device_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.post("/devices/{device_id}/on")
async def device_on(device_id: str):
    eco = _which_eco(device_id)
    if eco == "tapo":
        result = await tp_set_power(device_id, True)
    else:
        result = sl_set_power(device_id, True)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/devices/{device_id}/off")
async def device_off(device_id: str):
    eco = _which_eco(device_id)
    if eco == "tapo":
        result = await tp_set_power(device_id, False)
    else:
        result = sl_set_power(device_id, False)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/sensors")
async def sensors():
    return {"sensors": await get_hub_sensors()}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/config")
async def config():
    return get_config_status()

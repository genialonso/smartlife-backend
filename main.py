import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from controllers.smartlife import get_devices as sl_get_devices, get_status as sl_get_status, set_power as sl_set_power
from controllers.tapo import get_devices as tp_get_devices, get_device_status as tp_get_status, set_power as tp_set_power, get_sensors as tp_get_sensors

app = FastAPI(title="SmartLife + Tapo Unified API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/devices")
async def list_devices():
    sl = sl_get_devices()
    tp = await tp_get_devices()
    return {"devices": sl + tp}

@app.get("/devices/{device_id}")
async def device_status(device_id: str):
    if device_id.startswith("192."):
        result = await tp_get_status(device_id, None)
    else:
        result = sl_get_status(device_id)
    if "error" in result:
        # Try tapo by IP
        tp_result = await tp_get_status(device_id, None)
        if "error" not in tp_result:
            return tp_result
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.post("/devices/{device_id}/on")
async def device_on(device_id: str):
    if device_id.startswith("192."):
        result = await tp_set_power(device_id, None, True)
    else:
        result = sl_set_power(device_id, True)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/devices/{device_id}/off")
async def device_off(device_id: str):
    if device_id.startswith("192."):
        result = await tp_set_power(device_id, None, False)
    else:
        result = sl_set_power(device_id, False)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/sensors")
async def sensors():
    return {"sensors": await tp_get_sensors()}

@app.get("/health")
async def health():
    return {"status": "ok"}

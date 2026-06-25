"""
System Monitor Route
Streams real-time CPU, RAM, disk, network and device energy estimates via SSE.
"""

import asyncio
import json
import time
import psutil
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from core.security import get_current_user
from models.user import User

router = APIRouter()

# ── Energy estimation constants ───────────────────────────────────────────────
# Typical TDP ranges used for estimation (Watts)
# CPU: ~15W idle → ~65W full load (laptop), ~125W desktop
# RAM: ~3W per 8GB DDR4 module
# Source: Intel/AMD TDP specs + LPDDR4 datasheet averages

CPU_TDP_W = 45.0       # conservative laptop CPU TDP
RAM_W_PER_GB = 0.375   # ~3W per 8GB module
BASE_SYSTEM_W = 10.0   # fans, chipset, storage baseline


def _get_snapshot() -> dict:
    cpu_pct = psutil.cpu_percent(interval=None)
    cpu_freq = psutil.cpu_freq()
    cpu_count = psutil.cpu_count(logical=True)
    cpu_count_phys = psutil.cpu_count(logical=False) or 1

    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage("/")

    # Network delta (bytes since last call — psutil accumulates totals)
    net = psutil.net_io_counters()

    # Battery (if available)
    battery = None
    try:
        b = psutil.sensors_battery()
        if b:
            battery = {
                "percent": round(b.percent, 1),
                "plugged": b.power_plugged,
                "secs_left": b.secsleft if b.secsleft != psutil.POWER_TIME_UNLIMITED else None,
            }
    except Exception:
        pass

    # CPU temperature (macOS / Linux)
    temps = {}
    try:
        raw = psutil.sensors_temperatures()
        if raw:
            for key, entries in raw.items():
                if entries:
                    temps[key] = round(entries[0].current, 1)
    except Exception:
        pass

    # ── Energy estimation ──────────────────────────────────────────────────────
    # Estimated current draw = CPU_TDP * (cpu% / 100) + RAM baseline + base
    cpu_draw_w = CPU_TDP_W * (cpu_pct / 100)
    ram_used_gb = mem.used / (1024 ** 3)
    ram_draw_w = ram_used_gb * RAM_W_PER_GB
    total_draw_w = cpu_draw_w + ram_draw_w + BASE_SYSTEM_W

    return {
        "ts": time.time(),
        "cpu": {
            "percent": cpu_pct,
            "count_logical": cpu_count,
            "count_physical": cpu_count_phys,
            "freq_mhz": round(cpu_freq.current, 1) if cpu_freq else None,
            "freq_max_mhz": round(cpu_freq.max, 1) if cpu_freq else None,
        },
        "ram": {
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "used_gb": round(mem.used / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
            "percent": mem.percent,
            "swap_used_gb": round(swap.used / (1024 ** 3), 2),
            "swap_percent": swap.percent,
        },
        "disk": {
            "total_gb": round(disk.total / (1024 ** 3), 1),
            "used_gb": round(disk.used / (1024 ** 3), 1),
            "free_gb": round(disk.free / (1024 ** 3), 1),
            "percent": disk.percent,
        },
        "network": {
            "bytes_sent_mb": round(net.bytes_sent / (1024 ** 2), 2),
            "bytes_recv_mb": round(net.bytes_recv / (1024 ** 2), 2),
        },
        "battery": battery,
        "temps": temps,
        "energy": {
            "cpu_draw_w": round(cpu_draw_w, 2),
            "ram_draw_w": round(ram_draw_w, 2),
            "total_draw_w": round(total_draw_w, 2),
            "note": "Estimated from CPU TDP and RAM usage. Actual may vary.",
        },
    }


@router.get("/snapshot")
async def system_snapshot(current_user: User = Depends(get_current_user)):
    """Single system snapshot."""
    psutil.cpu_percent(interval=None)  # prime the counter
    await asyncio.sleep(0.2)
    return _get_snapshot()


@router.get("/stream")
async def system_stream(current_user: User = Depends(get_current_user)):
    """SSE stream of system metrics every 2 seconds."""
    psutil.cpu_percent(interval=None)  # prime

    async def generator():
        try:
            while True:
                data = _get_snapshot()
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

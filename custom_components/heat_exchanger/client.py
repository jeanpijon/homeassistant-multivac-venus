import logging
import threading
import time
from typing import Dict, List, Optional
import serial
from .const import HA2DEV_MODE

_LOGGER = logging.getLogger(__name__)

COMMANDS: Dict[str, List[int]] = {
    "idle_0": [ord(c) for c in "ÿÿÿ1511011121pu)0800010000FE67\r"],
    "cool_1": [ord(c) for c in "ÿÿÿ1511011121pu)0803010000D645\r"],
    "cool_2": [ord(c) for c in "ÿÿÿ1511011121pu)0803020000822F\r"],
    "cool_3": [ord(c) for c in "ÿÿÿ1511011121pu)0803030000436A\r"],
    "auto_1": [ord(c) for c in "ÿÿÿ1511011121pu)0802010000CE5B\r"],
    "auto_2": [ord(c) for c in "ÿÿÿ1511011121pu)08020200009A31\r"],
    "auto_3": [ord(c) for c in "ÿÿÿ1511011121pu)08020300005B74\r"],
}

def parse_sensor_frame(resp: bytes) -> Optional[Dict[str, int]]:
    """Decode a status reply into the sensors dict; None if it is not a valid frame."""
    if len(resp) < 40:
        return None
    try:
        s = resp[19:-1].decode("utf-8")
        data = [int(s[i:i+2], 16) for i in range(0, len(s), 2)]
    except Exception:
        return None
    if len(data) < 23:
        return None
    return {
        "power_factor.fan_ingress": data[1],
        "power_factor.fan_egress": data[2],
        "temperature.out_ingress": data[19],
        "temperature.out_egress": data[20],
        "temperature.in_egress": data[21],
        "temperature.in_ingress": data[22],
    }


class RS485IPClient:
    def __init__(self, host: str, port: int, poll_seconds: float) -> None:
        self._url = f"socket://{host}:{port}"
        self._poll_seconds = poll_seconds
        self._mode = "idle"
        self._fan_level = 0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._latest_sensors: Dict = {"sensors": {}}
        self._last_frame: Optional[float] = None
        self._ser: Optional[serial.SerialBase] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        try:
            if self._ser and self._ser.is_open:
                self._ser.close()
        except Exception:
            pass

    def set_mode(self, ha_mode: str) -> None:
        dev_mode = HA2DEV_MODE.get(ha_mode, "idle")
        with self._lock:
            self._mode = dev_mode
            if dev_mode == "idle":
                self._fan_level = 0

    def set_fan_level(self, level: int) -> None:
        level = max(0, min(3, int(level)))
        with self._lock:
            self._fan_level = level

    def snapshot(self) -> Dict:
        ha_mode = "off" if self._mode == "idle" else self._mode
        age = None if self._last_frame is None else time.monotonic() - self._last_frame
        return {"state": {"mode": ha_mode, "fan": self._fan_level}, "frame_age": age, **self._latest_sensors}

    def _ensure(self) -> None:
        if self._ser and self._ser.is_open:
            return
        self._ser = serial.serial_for_url(self._url, timeout=2.0)

    def _run(self) -> None:
        backoff = 1
        while not self._stop.is_set():
            try:
                self._ensure()
                self._loop()
                backoff = 1
            except Exception as e:
                _LOGGER.warning("IP RS485 loop error: %s", e)
                try:
                    if self._ser:
                        self._ser.close()
                except Exception:
                    pass
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)

    def _loop(self) -> None:
        self._write("idle", 0)
        time.sleep(1)
        self._write("idle", 0)
        time.sleep(1)
        while not self._stop.is_set():
            with self._lock:
                mode = self._mode
                level = self._fan_level
            self._write(mode, level)
            resp = self._ser.read(74)
            sensors = parse_sensor_frame(resp)
            if sensors is not None:
                self._latest_sensors = {"sensors": sensors}
                self._last_frame = time.monotonic()
            time.sleep(self._poll_seconds)
        self._write("idle", 0)

    def _write(self, dev_mode: str, level: int) -> None:
        key = f"{dev_mode}_{level}"
        payload = COMMANDS.get(key) or COMMANDS.get("idle_0")
        if not payload:
            return
        self._ser.reset_input_buffer()
        self._ser.write(bytes(payload))

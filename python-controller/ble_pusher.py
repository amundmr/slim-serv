import asyncio
import logging
import requests
from bleak import BleakScanner, BLEDevice, AdvertisementData

from gicisky_ble.devices import get_device, DeviceEntry
from gicisky_ble.writer import update_image
from weather_renderer import render_weather_display

TAG_MAC = "FF:FF:92:95:77:10"
GICISKY_MFR_KEY = 0x5053
SCAN_TIMEOUT = 30.0

WEATHER_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=62.462294&lon=6.283750"
WEATHER_HEADERS = {"User-Agent": "rpi-slim-serv/1.0 Raniseth"}

_LOGGER = logging.getLogger(__name__)


def fetch_weather() -> dict:
    response = requests.get(WEATHER_URL, headers=WEATHER_HEADERS, timeout=10)
    response.raise_for_status()
    return response.json()


async def scan_for_tag(mac: str, timeout: float) -> tuple[BLEDevice, DeviceEntry | None]:
    found_ble: BLEDevice | None = None
    last_rssi: int | None = None
    ready: asyncio.Future = asyncio.get_event_loop().create_future()

    def detection_callback(device: BLEDevice, adv: AdvertisementData) -> None:
        nonlocal found_ble, last_rssi
        if device.address.upper() != mac.upper():
            return

        found_ble = device
        if adv.rssi != last_rssi:
            last_rssi = adv.rssi
            print(f"[*] Tag seen: RSSI={adv.rssi} dBm")

        if GICISKY_MFR_KEY not in adv.manufacturer_data:
            return

        data = adv.manufacturer_data[GICISKY_MFR_KEY]
        if len(data) != 5:
            return

        device_id = ((data[4] << 8) | data[0]) & 0x3FFF
        firmware = (data[2] << 8) + data[3]
        battery_v = data[1] / 10
        entry = get_device(device_id, firmware)
        if entry is None:
            _LOGGER.warning("0x5053 seen but device_id=0x%04x not in registry", device_id)
            return

        print(f"[*] Tag entered update mode: {entry.model}, battery {battery_v:.1f}V")
        if not ready.done():
            ready.set_result(entry)

    async with BleakScanner(detection_callback=detection_callback):
        try:
            entry = await asyncio.wait_for(ready, timeout=timeout)
            return found_ble, entry
        except asyncio.TimeoutError:
            return found_ble, None


async def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    print("[*] Fetching weather data...")
    met_data = fetch_weather()
    image = render_weather_display(met_data)

    print(f"[*] Scanning for tag {TAG_MAC} (waiting up to {SCAN_TIMEOUT:.0f}s for update window)...")
    ble_device, device_entry = await scan_for_tag(TAG_MAC, SCAN_TIMEOUT)

    if ble_device is None:
        print("[!] Tag not found in range.")
        return

    if device_entry is None:
        print("[!] Tag found but did not enter update mode — try again when it refreshes.")
        return

    print(f"[*] Pushing weather image to {device_entry.model}...")
    success = await update_image(
        ble_device=ble_device,
        device=device_entry,
        image=image,
        threshold=128,
        red_threshold=128,
        attempt=1,
        write_delay_ms=20,
    )

    if success:
        print("[+++] Done!")
    else:
        print("[!] Push failed.")


if __name__ == "__main__":
    asyncio.run(main())

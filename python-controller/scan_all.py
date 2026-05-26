"""Scan all nearby BLE devices for 10 seconds and report name, MAC, RSSI."""
import asyncio
from bleak import BleakScanner, BLEDevice, AdvertisementData

seen: dict[str, tuple[str | None, int]] = {}

def callback(device: BLEDevice, adv: AdvertisementData) -> None:
    seen[device.address] = (adv.local_name or device.name, adv.rssi)

async def main() -> None:
    print("Scanning for 10 seconds...")
    async with BleakScanner(detection_callback=callback):
        await asyncio.sleep(10)

    print(f"\n{'MAC':<20} {'RSSI':>6}  Name")
    print("-" * 50)
    for mac, (name, rssi) in sorted(seen.items(), key=lambda x: x[1][1], reverse=True):
        print(f"{mac:<20} {rssi:>4} dBm  {name or '?'}")

asyncio.run(main())

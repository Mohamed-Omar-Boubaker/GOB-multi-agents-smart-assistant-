"""
Device Manager - Resolve device ids from user-defined mapping.
"""
import json
from pathlib import Path
from typing import Dict, Optional, List


class DeviceManager:
    def __init__(self, devices_file: str = "backend/data/devices.json"):
        self.devices_file = Path(devices_file)
        self.device_mapping: Dict = {}
        self.aliases: Dict = {}
        self.load_devices()

    def load_devices(self) -> None:
        if not self.devices_file.exists():
            print(f"⚠️ [Devices] File not found: {self.devices_file}")
            print("⚠️ [Devices] Creating default file...")
            self._create_default_devices()

        try:
            with open(self.devices_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.device_mapping = data.get("device_mapping", {})
                self.aliases = data.get("aliases", {})

            print(f"✅ [Devices] {len(self.device_mapping)} device types loaded")
            print(f"✅ [Devices] {len(self.aliases)} aliases loaded")

        except Exception as e:
            print(f"❌ [Devices] Load error: {e}")
            self.device_mapping = {}
            self.aliases = {}

    def _create_default_devices(self) -> None:
        default_data = {
            "device_mapping": {
                "light": {
                    "salon": "lamp_salon_001",
                    "cuisine": "lamp_kitchen_001",
                    "chambre": "lamp_bedroom_001",
                    "bureau": "lamp_office_001"
                },
                "shutter": {
                    "salon": "shutter_salon_001",
                    "cuisine": "shutter_kitchen_001",
                    "chambre": "shutter_bedroom_001"
                },
                "temperature": {
                    "salon": "thermostat_salon_001",
                    "chambre": "thermostat_bedroom_001"
                }
            },
            "aliases": {
                "living room": "salon",
                "kitchen": "cuisine"
            }
        }

        self.devices_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.devices_file, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)

        print(f"✅ [Devices] File created: {self.devices_file}")
        self.device_mapping = default_data["device_mapping"]
        self.aliases = default_data["aliases"]

    def _save_devices(self) -> None:
        data = {
            "device_mapping": self.device_mapping,
            "aliases": self.aliases
        }

        with open(self.devices_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_device_id(self, device_type: str, location: Optional[str]) -> Optional[str]:
        if not device_type:
            return None

        if not location:
            return None

        location_normalized = location.strip().lower()

        if location_normalized in self.aliases:
            location_normalized = self.aliases[location_normalized]

        device_type_normalized = device_type.strip().lower()

        mapping = self.device_mapping.get(device_type_normalized, {})
        return mapping.get(location_normalized)

    def list_devices(self) -> List[Dict]:
        devices = []
        for device_type, locations in self.device_mapping.items():
            for location, device_id in locations.items():
                devices.append({
                    "device_type": device_type,
                    "location": location,
                    "device_id": device_id
                })
        return devices

    def set_device(self, device_type: str, location: str, device_id: str) -> None:
        device_type_normalized = device_type.strip().lower()
        location_normalized = location.strip().lower()

        if device_type_normalized not in self.device_mapping:
            self.device_mapping[device_type_normalized] = {}

        self.device_mapping[device_type_normalized][location_normalized] = device_id
        self._save_devices()

    def delete_device(self, device_type: str, location: str) -> None:
        device_type_normalized = device_type.strip().lower()
        location_normalized = location.strip().lower()

        if device_type_normalized not in self.device_mapping:
            raise ValueError("Device type not found")

        if location_normalized not in self.device_mapping[device_type_normalized]:
            raise ValueError("Device location not found")

        self.device_mapping[device_type_normalized].pop(location_normalized)
        if not self.device_mapping[device_type_normalized]:
            self.device_mapping.pop(device_type_normalized)

        self._save_devices()

    def add_alias(self, alias: str, location: str) -> None:
        self.aliases[alias.strip().lower()] = location.strip().lower()
        self._save_devices()

    def delete_alias(self, alias: str) -> None:
        key = alias.strip().lower()
        if key not in self.aliases:
            raise ValueError("Alias not found")

        self.aliases.pop(key)
        self._save_devices()


# Global instance
device_manager = DeviceManager()

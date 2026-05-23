import json
import logging

# 1. Declarative Scene Configuration (Device-Level)
# Map each scene to the exact payload required by that specific hardware.
LIVING_ROOM_SCENES = {
    "off": {
        "corner_plug": {"state": "OFF"},
        "aqara_bulb": {"state": "OFF"},
        "nobrand_rgb": {"state": "OFF"}
    },
    "cosy": {
        "corner_plug": {"state": "ON"},
        "aqara_bulb": {
            "state": "ON", 
            "brightness": 100, 
            "color_temp": 400
        },
        "nobrand_rgb": {
            "state": "ON", 
            "brightness": 80, 
            # Note: Z2M expects RGB as a nested object
            "color": {"r": 255, "g": 140, "b": 50} 
        }
    },
    "full": {
        "corner_plug": {"state": "ON"},
        "aqara_bulb": {
            "state": "ON", 
            "brightness": 254, 
            "color_temp": 250
        },
        "nobrand_rgb": {
            "state": "ON", 
            "brightness": 254, 
            "color": {"r": 255, "g": 255, "b": 255}
        }
    }
}

class RoomController:
    """Manages explicit device states for a group of heterogeneous lights."""
    
    def __init__(self, room_name: str, scenes_config: dict):
        self.room_name = room_name
        self.scenes = scenes_config
        self.current_scene = "off" 

    def handle_button_press(self, action: str) -> list:
        """
        Determines the new scene and generates specific MQTT payloads 
        for every device defined in that scene.
        """
        # 1. Determine the target scene
        if action == "single":
            new_scene = "off" if self.current_scene == "cosy" else "cosy"
        elif action == "double":
            new_scene = "cosy" if self.current_scene == "full" else "full"
        else:
            return []

        self.current_scene = new_scene
        logging.info(f"[{self.room_name}] Switched to scene: {new_scene}")
        
        # 2. Generate the bespoke commands
        commands = []
        target_scene_config = self.scenes[new_scene]
        
        for device_name, device_payload in target_scene_config.items():
            topic = f"zigbee2mqtt/{device_name}/set"
            payload_str = json.dumps(device_payload)
            commands.append((topic, payload_str))
            
        return commands
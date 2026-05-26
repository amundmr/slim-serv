import sys
import requests
from weather_renderer import render_weather_display
from ble_pusher import WEATHER_URL, WEATHER_HEADERS

def main():
    print("Fetching live data from met.no...")
    try:
        response = requests.get(WEATHER_URL, headers=WEATHER_HEADERS)
        response.raise_for_status()
        met_data = response.json()
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        sys.exit(1)

    print("Rendering...")
    try:
        image = render_weather_display(met_data)
    except Exception as e:
        print(f"Renderer failed: {e}")
        sys.exit(1)

    image.save("test_render.png")
    print("Saved test_render.png")

if __name__ == "__main__":
    main()

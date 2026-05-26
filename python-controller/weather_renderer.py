from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# --- CONFIGURATION CONSTANTS ---
DISPLAY_WIDTH = 296
DISPLAY_HEIGHT = 128

# Precise paths based on your tree output
FONT_BOLD = "fonts/InterDisplay-Bold.ttf"
FONT_REGULAR = "fonts/Inter-Regular.ttf"
FONT_MDI = "fonts/materialdesignicons-webfont.ttf"

# Verified 32-bit Unicode mapping matching the local preview.html definitions
MDI_ICONS = {
    "rain-drop": "\U000F058C",   # mdi:water
    "cloud-rain": "\U000F0597",  # mdi:weather-rainy
    "cloud": "\U000F0590",       # mdi:weather-cloudy
    "sun": "\U000F0599",         # mdi:weather-sunny
    "arrow-up": "\U000F005D",    # mdi:arrow-up
    "arrow-tr": "\U000F005C",    # mdi:arrow-top-right
    "arrow-r": "\U000F0054",     # mdi:arrow-right
    "arrow-br": "\U000F0043",    # mdi:arrow-bottom-right
    "arrow-down": "\U000F0045",  # mdi:arrow-down
    "arrow-bl": "\U000F0042",    # mdi:arrow-bottom-left
    "arrow-l": "\U000F004D",     # mdi:arrow-left
    "arrow-tl": "\U000F005B",    # mdi:arrow-top-left
}

def get_wind_arrow(bearing: float) -> str:
    """Maps wind bearing directly to the correct font arrow character."""
    b = bearing % 360
    if b >= 337.5 or b < 22.5:    return MDI_ICONS["arrow-down"]  # Wind blowing FROM North points DOWN
    elif b >= 22.5 and b < 67.5:   return MDI_ICONS["arrow-bl"]
    elif b >= 67.5 and b < 112.5:  return MDI_ICONS["arrow-l"]
    elif b >= 112.5 and b < 157.5: return MDI_ICONS["arrow-tl"]
    elif b >= 157.5 and b < 202.5: return MDI_ICONS["arrow-up"]
    elif b >= 202.5 and b < 247.5: return MDI_ICONS["arrow-tr"]
    elif b >= 247.5 and b < 292.5: return MDI_ICONS["arrow-r"]
    else:                          return MDI_ICONS["arrow-br"]

def render_weather_display(met_data: dict) -> Image.Image:
    """Renders weather data as a single RGB image for the BWR e-ink display."""
    black_img = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), 255)
    red_img = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), 255)

    draw_b = ImageDraw.Draw(black_img)
    draw_r = ImageDraw.Draw(red_img)

    # --- EXTRACT DATA ---
    timeseries = met_data['properties']['timeseries']
    now_data = timeseries[0]['data']

    temp = now_data['instant']['details']['air_temperature']
    wind_speed = round(now_data['instant']['details']['wind_speed'])
    wind_bearing = now_data['instant']['details']['wind_from_direction']

    # Use next_12_hours symbol for a full-day character; fall back to shorter windows
    symbol_code = (
        now_data.get('next_12_hours', {}).get('summary', {}).get('symbol_code')
        or now_data.get('next_6_hours', {}).get('summary', {}).get('symbol_code')
        or now_data.get('next_1_hours', {}).get('summary', {}).get('symbol_code', 'cloudy')
    )

    # Sum hourly precipitation over the next 12 hours for a day total
    precip = sum(
        entry['data'].get('next_1_hours', {}).get('details', {}).get('precipitation_amount', 0.0)
        for entry in timeseries[:12]
    )

    # Scan next 12 hours of timeseries to find today's high temperature
    temp_high = max(
        entry['data']['instant']['details']['air_temperature']
        for entry in timeseries[:12]
    )

    # --- INITIALIZE FONTS ---
    font_metrics = ImageFont.truetype(FONT_BOLD, 30)
    font_date = ImageFont.truetype(FONT_REGULAR, 16)
    font_icon_main = ImageFont.truetype(FONT_MDI, 92)  # Balanced size for 128px height
    font_icon_sub = ImageFont.truetype(FONT_MDI, 24)

    # --- ROW 1: PRECIPITATION ---
    if precip > 0:
        precip_str = f"{precip}mm"
        draw_r.text((250, 20), precip_str, font=font_metrics, anchor="rm", fill=0)
        draw_r.text((258, 20), MDI_ICONS["rain-drop"], font=font_icon_sub, anchor="lm", fill=0)
    else:
        draw_b.text((290, 20), "Ingen regn", font=font_metrics, anchor="rm", fill=0)

    # --- ROW 2: WIND ---
    wind_str = f"{wind_speed} m/s"
    wind_arrow = get_wind_arrow(wind_bearing)
    
    if wind_speed > 10.8:
        draw_r.text((255, 60), wind_str, font=font_metrics, anchor="rm", fill=0)
        draw_r.text((285, 60), wind_arrow, font=font_icon_sub, anchor="rm", fill=0)
    else:
        draw_b.text((255, 60), wind_str, font=font_metrics, anchor="rm", fill=0)
        draw_b.text((285, 60), wind_arrow, font=font_icon_sub, anchor="rm", fill=0)

    # --- ROW 3: TEMPERATURE ---
    temp_str = f"{temp} / {round(temp_high)}°C"
    draw_b.text((290, 100), temp_str, font=font_metrics, anchor="rm", fill=0)

    # --- LEFT SECTION: HERO ICON & DATE ---
    if "rain" in symbol_code:
        main_icon = MDI_ICONS["cloud-rain"]
        active_draw = draw_r
    elif "clear" in symbol_code or "sun" in symbol_code:
        main_icon = MDI_ICONS["sun"]
        active_draw = draw_b
    else:
        main_icon = MDI_ICONS["cloud"]
        active_draw = draw_b

    # Center the large weather icon on the left panel grid
    active_draw.text((65, 50), main_icon, font=font_icon_main, anchor="mm", fill=0)

    # Print the tracking date
    date_str = datetime.now().strftime('%Y.%m.%d')
    draw_b.text((65, 115), date_str, font=font_date, anchor="mm", fill=0)

    rgb = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), (255, 255, 255))
    bw_mask = black_img.convert("L").point(lambda x: 0 if x > 128 else 255)
    red_mask = red_img.convert("L").point(lambda x: 0 if x > 128 else 255)
    rgb.paste((0, 0, 0), mask=bw_mask)
    rgb.paste((255, 0, 0), mask=red_mask)
    return rgb

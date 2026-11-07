"""Pre-rendered per-day Strip maps from real map tiles.

Reads the exported week (held sessions with venues) plus geocoded venue
coordinates, fetches one shared CARTO dark_matter tile mosaic, crops a
per-day view, and draws venue pins plus the session list onto a single
PNG per day. Static files: no JavaScript, no runtime tile fetching.

`python3 -m reinvent26.daymaps reinvent2026 --week week.json
--venues-json editorial.json --out-dir static/reinvent26
[--transit-json transit.json]`

Also renders one close-up map per venue (venue-<slug>.png) and, with
--transit-json, a monorail strip (transit-monorail.png).

Network only touches tile servers (polite: one subdomain, small sleeps).
Tests use synthetic tiles and never touch the network.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import urllib.request

TILE_SIZE = 256
ZOOM = 15
USER_AGENT = "reinvent26-daymaps/1.0 (contact via bryanchasko.com)"
TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
REQUEST_PAUSE_SECONDS = 0.5
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
AMBER = (245, 197, 66)
GREY = (148, 163, 184)
PANEL = (23, 23, 31)
OFFWHITE = (242, 237, 228)

DAY_LABELS = {
    "2026-11-30": "MON NOV 30",
    "2026-12-01": "TUE DEC 1",
    "2026-12-02": "WED DEC 2",
    "2026-12-03": "THU DEC 3",
    "2026-12-04": "FRI DEC 4",
}


def latlng_to_tile(latitude: float, longitude: float, zoom: int) -> tuple:
    """Slippy-map tile indices for a coordinate."""
    count = 2 ** zoom
    x_tile = int((longitude + 180.0) / 360.0 * count)
    lat_rad = math.radians(latitude)
    y_tile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * count)
    return x_tile, y_tile


def latlng_to_pixel(latitude: float, longitude: float, zoom: int,
                    origin_x: int, origin_y: int) -> tuple:
    """Pixel position inside a mosaic whose top-left tile is origin."""
    from PIL import Image as _Image  # noqa: F401  (keeps import local to use)
    count = 2 ** zoom
    global_x = (longitude + 180.0) / 360.0 * count * TILE_SIZE
    lat_rad = math.radians(latitude)
    global_y = ((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0
                * count * TILE_SIZE)
    return (int(global_x - origin_x * TILE_SIZE),
            int(global_y - origin_y * TILE_SIZE))


def fetch_tile(z: int, x: int, y: int, cache_dir: str):
    """One map tile, cached on disk. Only function that touches network."""
    from PIL import Image
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{z}-{x}-{y}.png")
    if not os.path.exists(path):
        req = urllib.request.Request(
            TILE_URL.format(z=z, x=x, y=y),
            headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(path, "wb") as handle:
                handle.write(resp.read())
        time.sleep(REQUEST_PAUSE_SECONDS)
    return Image.open(path).convert("RGB")


def build_mosaic(venues: list, cache_dir: str):
    """Fetch the smallest tile grid covering every venue (plus margin)."""
    from PIL import Image
    corners = [latlng_to_tile(venue["lat"], venue["lng"], ZOOM)
               for venue in venues]
    min_tile_x = min(corner[0] for corner in corners) - 1
    max_tile_x = max(corner[0] for corner in corners) + 1
    min_tile_y = min(corner[1] for corner in corners) - 1
    max_tile_y = max(corner[1] for corner in corners) + 1
    mosaic = Image.new(
        "RGB",
        ((max_tile_x - min_tile_x + 1) * TILE_SIZE,
         (max_tile_y - min_tile_y + 1) * TILE_SIZE))
    for tile_x in range(min_tile_x, max_tile_x + 1):
        for tile_y in range(min_tile_y, max_tile_y + 1):
            tile = fetch_tile(ZOOM, tile_x, tile_y, cache_dir)
            mosaic.paste(tile, ((tile_x - min_tile_x) * TILE_SIZE,
                                (tile_y - min_tile_y) * TILE_SIZE))
    return mosaic, min_tile_x, min_tile_y


def ordered_numbers(day_held):
    """1-based numbers in time order, shared by dots and side rows."""
    ordered = sorted(
        day_held,
        key=lambda held_session: (held_session.get("date", ""),
                                  held_session["start"]))
    return {id(held_session): number
            for number, held_session in enumerate(ordered, 1)}


def venue_labels(day_held):
    """Session lines per venue, date/time-ordered to match the side rows."""
    numbers = ordered_numbers(day_held)
    labels: dict = {}
    for held_session in sorted(
            day_held,
            key=lambda session_row: (session_row.get("date", ""),
                                     session_row["start"])):
        labels.setdefault(held_session["venue"], []).append(
            f"{numbers[id(held_session)]} "
            f"{held_session['start']} {held_session['code']}")
    return labels


SHORT_NAMES = {
    "MGM Grand": "MGM Grand",
    "Wynn/Encore": "Wynn",
    "Caesars Palace": "Caesars Palace",
    "Caesars Forum": "Caesars Forum",
    "Venetian": "Venetian",
    "Harrah's / LINQ": "LINQ",
    "Flamingo": "Flamingo",
}


def slugify(name: str) -> str:
    """URL slug for a venue or station name: Wynn/Encore -> wynn-encore."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def draw_day(date: str, day_held: list, venues: list,
             mosaic, origin: tuple, title: str | None = None):
    """Composite: map crop left, session list right, attribution bottom."""
    from PIL import Image, ImageDraw, ImageFont
    title_font = ImageFont.truetype(FONT_PATH, 22)
    row_font = ImageFont.truetype(FONT_PATH, 16)
    small_font = ImageFont.truetype(FONT_PATH, 13)
    label_font = ImageFont.truetype(FONT_PATH, 12)
    labels = venue_labels(day_held)
    active = {held_session["venue"] for held_session in day_held}
    multi_day = len({h.get("date", "") for h in day_held}) > 1
    points = {}
    for venue in venues:
        points[venue["name"]] = latlng_to_pixel(
            venue["lat"], venue["lng"], ZOOM, *origin)
    active_x = [points[venue_name][0] for venue_name in active
                if venue_name in points]
    active_y = [points[venue_name][1] for venue_name in active
                if venue_name in points]
    pad = 90
    left = max(0, min(active_x) - pad)
    top = max(0, min(active_y) - pad)
    right = min(mosaic.width, max(active_x) + pad)
    bottom = min(mosaic.height, max(active_y) + pad)
    min_side = 520
    if right - left < min_side:
        center_x = (left + right) // 2
        left = max(0, center_x - min_side // 2)
        right = min(mosaic.width, left + min_side)
    if bottom - top < min_side:
        center_y = (top + bottom) // 2
        top = max(0, center_y - min_side // 2)
        bottom = min(mosaic.height, top + min_side)
    crop = mosaic.crop((left, top, right, bottom))
    panel_width = 330
    list_bottom = 60 + len(day_held) * 62 + 30
    canvas_height = max(crop.height + 26, list_bottom)
    canvas = Image.new("RGB", (crop.width + panel_width, canvas_height),
                       PANEL)
    canvas.paste(crop, (0, 26))
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 2), title or DAY_LABELS.get(date, date),
              font=title_font, fill=AMBER)
    for venue_name, (pixel_x, pixel_y) in points.items():
        if not (left <= pixel_x <= right and top <= pixel_y <= bottom):
            continue
        dot_x, dot_y = pixel_x - left, pixel_y - top + 26
        color = AMBER if venue_name in active else GREY
        draw.ellipse([dot_x - 7, dot_y - 7, dot_x + 7, dot_y + 7],
                     fill=color, outline=(10, 10, 14), width=2)
        if venue_name == "Venetian":
            draw.ellipse([dot_x - 11, dot_y - 11, dot_x + 11, dot_y + 11],
                         outline=AMBER, width=2)
        if venue_name in labels:
            lines = [SHORT_NAMES.get(venue_name, venue_name)]
            if len(labels) == 1 and len(labels[venue_name]) > 2:
                lines += [f"{len(labels[venue_name])} sessions, "
                          "numbered at right"]
            else:
                lines += labels[venue_name]
            anchor = "la"
            text_x = dot_x + 12
            if dot_x > crop.width * 0.62:
                anchor = "ra"
                text_x = dot_x - 12
            placed_labels = []
            label_y = dot_y - 10 * len(lines)
            for label_line in lines:
                placed_labels.append((text_x, label_y, label_line))
                label_y += 20
            boxes = [draw.textbbox((box_x, box_y), box_text,
                                   font=label_font, anchor=anchor)
                     for box_x, box_y, box_text in placed_labels]
            backing = (min(box[0] for box in boxes) - 4,
                       min(box[1] for box in boxes) - 3,
                       max(box[2] for box in boxes) + 4,
                       max(box[3] for box in boxes) + 3)
            draw.rectangle(backing, fill=PANEL)
            for (box_x, box_y, box_text) in placed_labels:
                draw.text((box_x, box_y), box_text, font=label_font,
                          fill=OFFWHITE, anchor=anchor)
    row_y = 60
    numbers = ordered_numbers(day_held)
    for held_session in sorted(
            day_held,
            key=lambda session_row: (session_row.get("date", ""),
                                     session_row["start"])):
        session_number = numbers[id(held_session)]
        row_title = held_session.get("title") or ""
        if len(row_title) > 40:
            row_title = row_title[:37] + "..."
        draw.text((crop.width + 14, row_y),
                  f"{session_number}. "
                  f"{_row_when(held_session, multi_day)} "
                  f"{held_session['code']}",
                  font=row_font, fill=OFFWHITE)
        draw.text((crop.width + 14, row_y + 22), held_session["venue"],
                  font=small_font, fill=GREY)
        draw.text((crop.width + 14, row_y + 38), row_title,
                  font=small_font, fill=GREY)
        row_y += 62
    draw.text((12, canvas.height - 20),
              "(c) OpenStreetMap contributors",
              font=small_font, fill=GREY)
    return canvas


def _row_when(held_session: dict, multi_day: bool) -> str:
    """Side-row time: with MM-DD prefix when rows span several days."""
    when = held_session["start"]
    if multi_day and held_session.get("date"):
        when = f"{held_session['date'][5:]} {held_session['start']}"
    return when


def venue_slug(venues: list, name: str) -> str:
    """Editorial slug when present, else a slug of the venue name."""
    for venue in venues:
        if venue.get("name") == name and venue.get("slug"):
            return venue["slug"]
    return slugify(name)


def run_venues(week: dict, venues: list, mosaic, origin: tuple,
               out_dir: str) -> int:
    """One close-up map per venue holding sessions across the week."""
    names = sorted({held_session.get("venue", "")
                    for held_session in week.get("held", [])
                    if held_session.get("venue")})
    for name in names:
        at_venue = sorted(
            (held_session for held_session in week["held"]
             if held_session.get("venue") == name),
            key=lambda venue_session: (venue_session.get("date", ""),
                                        venue_session["start"]))
        image = draw_day(name, at_venue, venues, mosaic, origin,
                         title=name)
        out_path = os.path.join(out_dir, f"venue-{venue_slug(venues, name)}.png")
        image.save(out_path)
        print(f"# wrote {out_path} ({image.width}x{image.height})")
    return 0


def draw_transit(stops: list, mosaic, origin: tuple):
    """Monorail strip: station dots joined south to north, names aside."""
    from PIL import Image, ImageDraw, ImageFont
    title_font = ImageFont.truetype(FONT_PATH, 22)
    row_font = ImageFont.truetype(FONT_PATH, 16)
    small_font = ImageFont.truetype(FONT_PATH, 13)
    label_font = ImageFont.truetype(FONT_PATH, 12)
    ordered = sorted(stops, key=lambda station: station["lat"])
    points = [latlng_to_pixel(station["lat"], station["lng"], ZOOM, *origin)
              for station in ordered]
    points_x = [point[0] for point in points]
    points_y = [point[1] for point in points]
    pad = 110
    left = max(0, min(points_x) - pad)
    top = max(0, min(points_y) - pad)
    right = min(mosaic.width, max(points_x) + pad)
    bottom = min(mosaic.height, max(points_y) + pad)
    crop = mosaic.crop((left, top, right, bottom))
    panel_width = 330
    list_bottom = 60 + len(ordered) * 40 + 30
    canvas_height = max(crop.height + 26, list_bottom)
    canvas = Image.new("RGB", (crop.width + panel_width, canvas_height),
                       PANEL)
    canvas.paste(crop, (0, 26))
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 2), "LAS VEGAS MONORAIL", font=title_font, fill=AMBER)
    shifted = [(point_x - left, point_y - top + 26)
               for point_x, point_y in points]
    row_y = 60
    for number, (stop, (dot_x, dot_y)) in enumerate(zip(ordered, shifted),
                                                    1):
        draw.ellipse([dot_x - 7, dot_y - 7, dot_x + 7, dot_y + 7],
                     fill=AMBER, outline=(10, 10, 14), width=2)
        draw.text((dot_x + 12, dot_y - 10), str(number),
                  font=label_font, fill=OFFWHITE,
                  stroke_width=2, stroke_fill=PANEL)
        draw.text((crop.width + 14, row_y), f"{number}. {stop['name']}",
                  font=row_font, fill=OFFWHITE)
        row_y += 40
    draw.text((12, canvas.height - 20),
              "(c) OpenStreetMap contributors",
              font=small_font, fill=GREY)
    return canvas


def run_transit(transit_path: str, out_dir: str, cache_dir: str) -> int:
    """Render the monorail strip from geocoded station stops."""
    transit = json.load(open(transit_path, encoding="utf-8"))
    stops = transit["stops"]
    os.makedirs(out_dir, exist_ok=True)
    mosaic, origin_x, origin_y = build_mosaic(stops, cache_dir)
    image = draw_transit(stops, mosaic, (origin_x, origin_y))
    out_path = os.path.join(out_dir, "transit-monorail.png")
    image.save(out_path)
    print(f"# wrote {out_path} ({image.width}x{image.height})")
    return 0


def run(week_path: str, editorial_path: str, out_dir: str,
        cache_dir: str, transit_path: str | None = None) -> int:
    week = json.load(open(week_path, encoding="utf-8"))
    editorial = json.load(open(editorial_path, encoding="utf-8"))
    venues = editorial["map_venues"]
    os.makedirs(out_dir, exist_ok=True)
    mosaic, origin_x, origin_y = build_mosaic(venues, cache_dir)
    dates = sorted({held_session.get("date", "")
                    for held_session in week["held"]
                    if held_session.get("date")})
    for date in dates:
        day_held = [held_session for held_session in week["held"]
                    if held_session.get("date") == date]
        image = draw_day(date, day_held, venues, mosaic, (origin_x, origin_y))
        out_path = os.path.join(out_dir, f"day-{date}.png")
        image.save(out_path)
        print(f"# wrote {out_path} ({image.width}x{image.height})")
    run_venues(week, venues, mosaic, (origin_x, origin_y), out_dir)
    if transit_path:
        run_transit(transit_path, out_dir, cache_dir)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="reinvent26 daymaps",
                                     description="render per-day Strip maps")
    parser.add_argument("event_id")
    parser.add_argument("--week", required=True)
    parser.add_argument("--venues-json", required=True,
                        help="editorial.json holding map_venues")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--cache-dir", default="/tmp/re26tiles")
    parser.add_argument("--transit-json", default=None,
                        help="transit.json with monorail stops; "
                             "also renders transit-monorail.png")
    args = parser.parse_args(argv)
    return run(args.week, args.venues_json, args.out_dir, args.cache_dir,
               args.transit_json)


if __name__ == "__main__":
    raise SystemExit(main())

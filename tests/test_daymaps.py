import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import daymaps  # noqa: E402


def test_tile_math_roundtrip():
    x, y = daymaps.latlng_to_tile(36.1217, -115.1693, 15)
    # slippy-map formula, verified to 10 digits: x = 5901.03, y = 12853.82
    assert x == 5901
    assert y == 12853
    px, py = daymaps.latlng_to_pixel(36.1217, -115.1693, 15, x, y)
    assert 0 <= px < 256
    assert 0 <= py < 256


def test_draw_day_composites_synthetic_mosaic(tmp_path):
    from PIL import Image
    mosaic = Image.new("RGB", (1408, 1408), (20, 20, 30))
    venues = [
        {"name": "MGM Grand", "lat": 36.1028, "lng": -115.1694},
        {"name": "Venetian", "lat": 36.1217, "lng": -115.1693},
    ]
    tiles = [daymaps.latlng_to_tile(v["lat"], v["lng"], 15)
             for v in venues]
    origin = (min(t[0] for t in tiles) - 1,
              min(t[1] for t in tiles) - 1)
    held = [
        {"code": "AAA111", "title": "First", "date": "2026-11-30",
         "start": "08:30", "end": "09:30", "venue": "MGM Grand"},
    ]
    image = daymaps.draw_day("2026-11-30", held, venues, mosaic, origin)
    assert image.width >= 330 + 50
    assert image.mode == "RGB"
    out = str(tmp_path / "day.png")
    image.save(out)
    assert os.path.getsize(out) > 5000


def test_run_writes_five_pngs_with_cached_tiles(tmp_path, monkeypatch):
    from PIL import Image
    cache = tmp_path / "tiles"
    cache.mkdir()
    for name in ["15-5900-12655.png"]:
        Image.new("RGB", (256, 256), (30, 30, 40)).save(str(cache / name))
    import json
    week = {"held": [
        {"code": "AAA111", "title": "First", "date": "2026-11-30",
         "start": "08:30", "end": "09:30", "venue": "MGM Grand"},
    ]}
    week_path = tmp_path / "week.json"
    week_path.write_text(json.dumps(week))
    ed = {"map_venues": [
        {"name": "MGM Grand", "lat": 36.1028, "lng": -115.1694},
        {"name": "Venetian", "lat": 36.1217, "lng": -115.1693},
    ]}
    ed_path = tmp_path / "ed.json"
    ed_path.write_text(json.dumps(ed))

    def fake_fetch(z, x, y, cache_dir):
        return Image.new("RGB", (256, 256), (30, 30, 40))
    monkeypatch.setattr(daymaps, "fetch_tile", fake_fetch)
    out_dir = tmp_path / "out"
    assert daymaps.run(str(week_path), str(ed_path), str(out_dir),
                       str(cache)) == 0
    assert (out_dir / "day-2026-11-30.png").exists()


def test_venue_labels_group_time_ordered_sessions():
    held = [
        {"code": "BBB222", "start": "15:00", "venue": "MGM Grand"},
        {"code": "AAA111", "start": "08:30", "venue": "MGM Grand"},
        {"code": "CCC333", "start": "12:00", "venue": "Wynn/Encore"},
    ]
    from reinvent26.daymaps import ordered_numbers, venue_labels
    assert venue_labels(held) == {
        "MGM Grand": ["1 08:30 AAA111", "3 15:00 BBB222"],
        "Wynn/Encore": ["2 12:00 CCC333"],
    }
    numbers = ordered_numbers(
        sorted(held, key=lambda held_session: held_session["start"]))
    assert sorted(numbers.values()) == [1, 2, 3]


def test_slugify_venue_names():
    from reinvent26.daymaps import slugify, venue_slug
    assert slugify("Wynn/Encore") == "wynn-encore"
    assert slugify("Harrah's / LINQ") == "harrah-s-linq"
    venues = [{"name": "MGM Grand", "slug": "mgm"}]
    assert venue_slug(venues, "MGM Grand") == "mgm"
    assert venue_slug(venues, "Wynn/Encore") == "wynn-encore"


def test_single_venue_dot_label_collapses_to_count():
    from reinvent26 import daymaps
    from PIL import Image
    mosaic = Image.new("RGB", (3 * 256, 3 * 256), (20, 20, 30))
    venues = [{"name": "MGM Grand", "lat": 36.1028, "lng": -115.1694}]
    tile = daymaps.latlng_to_tile(36.1028, -115.1694, 15)
    origin = (tile[0] - 1, tile[1] - 1)
    held = [{"code": f"AAA11{i}", "title": "T", "date": "2026-11-30",
             "start": f"08:3{i}", "end": "09:30", "venue": "MGM Grand"}
            for i in range(3)]
    image = daymaps.draw_day("2026-11-30", held, venues, mosaic, origin)
    assert image.mode == "RGB"
    assert daymaps.venue_labels(held) == {
        "MGM Grand": ["1 08:30 AAA110", "2 08:31 AAA111", "3 08:32 AAA112"],
    }


def test_venue_labels_match_side_row_order_across_days():
    from reinvent26.daymaps import venue_labels
    held = [
        {"code": "BBB222", "start": "15:00", "date": "2026-11-30",
         "venue": "MGM Grand"},
        {"code": "AAA111", "start": "08:30", "date": "2026-12-01",
         "venue": "MGM Grand"},
    ]
    assert venue_labels(held) == {
        "MGM Grand": ["1 15:00 BBB222", "2 08:30 AAA111"],
    }


def test_row_when_prefixes_date_on_multi_day_rows():
    from reinvent26.daymaps import _row_when
    item = {"date": "2026-12-03", "start": "08:00"}
    assert _row_when(item, True) == "12-03 08:00"
    assert _row_when(item, False) == "08:00"


def test_run_venues_writes_one_png_per_venue(tmp_path, monkeypatch):
    from PIL import Image
    from reinvent26 import daymaps
    venues = [
        {"name": "MGM Grand", "slug": "mgm-grand",
         "lat": 36.1028, "lng": -115.1694},
    ]
    tile = daymaps.latlng_to_tile(36.1028, -115.1694, 15)
    origin = (tile[0] - 1, tile[1] - 1)
    mosaic = Image.new("RGB", (3 * 256, 3 * 256), (20, 20, 30))
    week = {"held": [
        {"code": "AAA111", "title": "First", "date": "2026-11-30",
         "start": "08:30", "end": "09:30", "venue": "MGM Grand"},
    ]}
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    assert daymaps.run_venues(week, venues, mosaic, origin,
                              str(out_dir)) == 0
    assert (out_dir / "venue-mgm-grand.png").exists()


def test_draw_transit_composites_synthetic_mosaic():
    from PIL import Image
    from reinvent26 import daymaps
    stops = [
        {"name": "MGM Grand", "lat": 36.1028, "lng": -115.1694},
        {"name": "Sahara", "lat": 36.1425, "lng": -115.1546},
    ]
    tiles = [daymaps.latlng_to_tile(s["lat"], s["lng"], 15)
             for s in stops]
    origin = (min(t[0] for t in tiles) - 1,
              min(t[1] for t in tiles) - 1)
    width = (max(t[0] for t in tiles) - min(t[0] for t in tiles) + 3) * 256
    height = (max(t[1] for t in tiles) - min(t[1] for t in tiles) + 3) * 256
    mosaic = Image.new("RGB", (width, height), (20, 20, 30))
    image = daymaps.draw_transit(stops, mosaic, origin)
    assert image.mode == "RGB"
    assert image.width >= 330 + 50

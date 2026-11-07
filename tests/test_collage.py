import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from PIL import Image  # noqa: E402

from reinvent26 import collage  # noqa: E402


def _make_photos(photo_dir, count=4):
    colors = [(200, 30, 30), (30, 200, 30), (30, 30, 200), (200, 200, 30)]
    for position in range(count):
        photo = Image.new("RGB", (800, 600), colors[position % 4])
        photo.save(os.path.join(photo_dir, f"photo-{position + 1:02d}.jpg"))
        photo.close()


def test_cover_panel_exact_size():
    photo = Image.new("RGB", (1600, 900), (10, 20, 30))
    panel = collage.cover_panel(photo)
    assert panel.size == (collage.PANEL_WIDTH, collage.PANEL_HEIGHT)
    photo.close()


def test_run_packs_strips_manifest_sidecars(tmp_path):
    photo_dir = tmp_path / "photos"
    photo_dir.mkdir()
    _make_photos(str(photo_dir), 4)
    out_dir = tmp_path / "out"
    manifest_path = str(tmp_path / "photos.json")
    assert collage.run(str(photo_dir), str(out_dir), manifest_path) == 0
    strip_one = out_dir / "photos-strip-01.webp"
    strip_two = out_dir / "photos-strip-02.webp"
    assert strip_one.exists()
    assert strip_two.exists()
    first_strip = Image.open(strip_one)
    assert first_strip.size == (collage.STRIP_WIDTH, collage.STRIP_HEIGHT)
    first_strip.close()
    manifest = json.load(open(manifest_path, encoding="utf-8"))
    assert len(manifest["strips"]) == 2
    assert manifest["strips"][0]["photos"] == [
        "photo-01.jpg", "photo-02.jpg", "photo-03.jpg"]
    assert manifest["strips"][1]["photos"] == [
        "photo-02.jpg", "photo-03.jpg", "photo-04.jpg"]
    sidecar = json.load(open(str(strip_one) + ".sidecar.json",
                             encoding="utf-8"))
    assert sidecar["sha256"]
    assert sidecar["geometry"]["strip"] == [collage.STRIP_WIDTH,
                                            collage.STRIP_HEIGHT]
    assert sidecar["quality"] == collage.WEBP_QUALITY


def test_run_empty_dir_fails(tmp_path):
    photo_dir = tmp_path / "empty"
    photo_dir.mkdir()
    assert collage.run(str(photo_dir), str(tmp_path / "out"),
                       str(tmp_path / "photos.json")) == 2

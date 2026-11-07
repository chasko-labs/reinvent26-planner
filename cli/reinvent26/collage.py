"""Photo strips for the reinvent26 page, following ~/writing/BRAND.md.

`python3 -m reinvent26.collage <photos-dir> --out-dir <static/reinvent26>
--manifest <photos.json>`

Reads floor photos in filename order (sequencing is the photographer's),
packs them into 3-panel strips (1584x340 = 3x520 panels + 2x12px dividers on
navy #0F141C), and writes one webp strip plus a sidecar per strip. Stills
first: no motion is built from these until the stills ship. Deterministic:
same inputs, same bytes. Photos land in the repo; nothing is fetched.
After regenerating, run prettier --write on the manifest and sidecars:
the site repo hook enforces prettier style.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import PIL.Image

PANEL_WIDTH = 520
PANEL_HEIGHT = 340
DIVIDER_WIDTH = 12
PANELS_PER_STRIP = 3
STRIP_WIDTH = PANELS_PER_STRIP * PANEL_WIDTH + 2 * DIVIDER_WIDTH
STRIP_HEIGHT = 340
NAVY = (15, 20, 28)
WEBP_QUALITY = 82
PHOTO_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


def cover_panel(photo: PIL.Image.Image) -> PIL.Image.Image:
    """Scale a photo to fill 520x340, center-cropped. Deterministic."""
    source = photo.convert("RGB")
    scale = max(PANEL_WIDTH / source.width, PANEL_HEIGHT / source.height)
    resized = source.resize((round(source.width * scale),
                             round(source.height * scale)),
                            PIL.Image.LANCZOS)
    left = (resized.width - PANEL_WIDTH) // 2
    top = (resized.height - PANEL_HEIGHT) // 2
    return resized.crop((left, top, left + PANEL_WIDTH, top + PANEL_HEIGHT))


def build_strip(photos: list) -> PIL.Image.Image:
    """Three cover panels on navy with 12px dividers between them."""
    strip = PIL.Image.new("RGB", (STRIP_WIDTH, STRIP_HEIGHT), NAVY)
    for position, photo in enumerate(photos):
        panel = cover_panel(photo)
        strip.paste(panel, (position * (PANEL_WIDTH + DIVIDER_WIDTH), 0))
    return strip


def strip_sha256(path: str) -> str:
    """Hex digest of a finished file, recorded in its sidecar."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_photos(photos_dir: str) -> list:
    """Photo files in filename order. Sequencing is the photographer's."""
    return sorted(entry for entry in os.listdir(photos_dir)
                  if entry.lower().endswith(PHOTO_EXTENSIONS))


def run(photos_dir: str, out_dir: str, manifest_path: str) -> int:
    """Pack photo groups of three into webp strips plus sidecars."""
    names = list_photos(photos_dir)
    if not names:
        print("error: no photos found", file=sys.stderr)
        return 2
    os.makedirs(out_dir, exist_ok=True)
    strips = []
    for strip_number, offset in enumerate(range(0, len(names), 3), 1):
        group = names[offset:offset + 3]
        if len(group) < PANELS_PER_STRIP:
            need = PANELS_PER_STRIP - len(group)
            group = names[max(0, offset - need):offset] + group
        with PIL.Image.open(
                os.path.join(photos_dir, group[0])) as first_photo:
            first_size = first_photo.size
        photos = [PIL.Image.open(os.path.join(photos_dir, name))
                  for name in group]
        try:
            while len(photos) < PANELS_PER_STRIP:
                photos.append(photos[-1].copy())
            strip = build_strip(photos)
            strip_name = f"photos-strip-{strip_number:02d}.webp"
            strip_path = os.path.join(out_dir, strip_name)
            strip.save(strip_path, "WEBP", quality=WEBP_QUALITY)
            sidecar = {
                "sources": group,
                "first_photo_size": list(first_size),
                "geometry": {"panel": [PANEL_WIDTH, PANEL_HEIGHT],
                             "divider": DIVIDER_WIDTH,
                             "strip": [STRIP_WIDTH, STRIP_HEIGHT]},
                "quality": WEBP_QUALITY,
                "sha256": strip_sha256(strip_path),
            }
            sidecar_path = strip_path + ".sidecar.json"
            with open(sidecar_path, "w", encoding="utf-8") as handle:
                json.dump(sidecar, handle, indent="\t")
                handle.write("\n")
            strips.append({"image": strip_name,
                           "alt": f"re:Invent floor photos, strip "
                                  f"{strip_number}",
                           "photos": group})
        finally:
            for photo in photos:
                photo.close()
        print(f"# wrote {strip_path} ({STRIP_WIDTH}x{STRIP_HEIGHT})")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump({"strips": strips}, handle, indent="\t")
        handle.write("\n")
    return 0


def main(argv=None) -> int:
    """Parse arguments and pack photo strips."""
    parser = argparse.ArgumentParser(prog="reinvent26 collage",
                                     description="pack floor photos "
                                                 "into page strips")
    parser.add_argument("photos_dir", help="directory of floor photos")
    parser.add_argument("--out-dir", required=True,
                        help="directory receiving strip webp files")
    parser.add_argument("--manifest", required=True,
                        help="output JSON manifest the page renders")
    args = parser.parse_args(argv)
    return run(args.photos_dir, args.out_dir, args.manifest)


if __name__ == "__main__":
    raise SystemExit(main())

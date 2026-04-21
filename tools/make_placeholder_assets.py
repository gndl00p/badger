from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from tools.dither_image import convert


def _headshot(tmp: Path) -> Path:
    img = Image.new("L", (128, 128), color=255)
    draw = ImageDraw.Draw(img)
    draw.ellipse((44, 20, 84, 60), fill=60)
    draw.pieslice((24, 60, 104, 140), 180, 360, fill=60)
    p = tmp / "headshot.png"
    img.save(p)
    return p


def _wordmark(tmp: Path) -> Path:
    img = Image.new("L", (296, 128), color=255)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
    except OSError:
        font = ImageFont.load_default()
    text = "ROBB.TECH"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((296 - tw) // 2 - bbox[0], (128 - th) // 2 - bbox[1]), text, fill=0, font=font)
    p = tmp / "wordmark.png"
    img.save(p)
    return p


def main():
    import tempfile

    assets = Path(__file__).resolve().parent.parent / "assets"
    assets.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        convert(str(_headshot(tmp)), str(assets / "headshot.bin"), 128, 128)
        convert(str(_wordmark(tmp)), str(assets / "robbtech_wordmark.bin"), 296, 128)
    print(f"Wrote {assets}/headshot.bin and {assets}/robbtech_wordmark.bin")


if __name__ == "__main__":
    main()

"""Generate assets/icon.png and assets/icon.ico from the favicon design using PIL."""
from PIL import Image, ImageDraw, ImageFont
import pathlib

assets = pathlib.Path(__file__).parent

size = 256  # render at high res, then downsample for smaller sizes
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
# Green rounded rect matching favicon.svg: fill=#15803d, rx≈6/32 * 256 ≈ 48px
draw.rounded_rectangle([8, 8, size - 8, size - 8], radius=48, fill="#15803d")
# 🌿 emoji via Segoe UI Emoji (Windows)
try:
    font = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", 170)
    draw.text((28, 38), "\U0001f33f", font=font, embedded_color=True)
    print("emoji rendered OK")
except Exception as e:
    print(f"emoji skipped ({e})")

# Save PNG at 64px (tray icon)
png_out = assets / "icon.png"
img.resize((64, 64), Image.LANCZOS).save(png_out)
print(f"saved {png_out}")

# Save ICO with multiple sizes (exe icon)
ico_out = assets / "icon.ico"
img.save(ico_out, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)])
print(f"saved {ico_out}")
